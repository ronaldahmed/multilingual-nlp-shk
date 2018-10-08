import os,sys
import subprocess as sp
from morph_mapper import MorphMapper
import argparse
import pdb


def get_morph_annon(form,fst_file):
  parsed = sp.run(["flookup",fst_file],
                  stdout=sp.PIPE,
                  input=form.encode("utf8") )
  parsed = parsed.stdout.decode("utf8").strip('\n').split('\n')
  options = []
  for option_line in parsed:
    inp,m_out = option_line.split('\t')
    if m_out=="+?":
      return []
    morph_tag = []
    m_out = m_out.split(" ")
    morph_tag.append(m_out[0][1:-1]) # first elmt is POS
    for seg in m_out[1:]:
      try:
        morph,tag = seg.replace("["," ").replace("]","").split(" ")
      except:
        pdb.set_trace()

      #if "+" not in tag:  continue
      if morph=="-": morph = "_"
      morph_tag.append([morph,tag.strip("+").lower()])
    #
    if len(morph_tag)>0:
      options.append(morph_tag)
  # print(options)

  return options

        
def normalize_upos(form,pos,deprel):
  if   pos in ["CL2P","CLNOM","SUFV"]:    return "PART"
  elif pos=="PINT":   return "PRON"
  elif pos=="ONOM":
    if deprel=='obj': return "NOUN"
    else:             return "PART"
  #elif pos=="CONJ":
  #  return
  else:
    return pos
  


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("--input", '-i', default="", type=str, help="Treebank file in CONLLU format")
  parser.add_argument("--fst", '-fst', default=None, type=str, help="Compiled Morphological Analyser in fst format")
  parser.add_argument("--morph_map", '-m', default="morph_map_table.tsv", type=str, help="Morphological dictionary")
  parser.add_argument("--allom", '-a', default="allomorphs.tsv", type=str, help="Allomorphs dictionary")
  args = parser.parse_args()

  morph_mapper = MorphMapper(args.morph_map,args.allom)
  sent_lines = open(args.input,'r').read().strip('\n').split('\n\n')

  pop_out = open(args.input+".annot",'w')

  pos_vocab = set()
  sent_count = 1

  for sent_block in sent_lines:
    lines = sent_block.split('\n')
    # comments = lines[:4]
    # print('\n'.join(comments),file=pop_out)

    lines = lines[4:]
    is_comp = False
    lbound = ""
    
    sent_cols = []
    lemmas = []
    sent_morph_tags = []
    orig_annot = []
    main_form,main_seg = "",""
    segments,form,lemma = "","",""

    zerom_id = -1
    for i,wline in enumerate(lines):
      cols = wline.split('\t')
      if cols[1]=='-':
        cols[1] = "&hypen"
      
      # grab pos from first compound
      if "-" in cols[0]:
        is_comp = True
        lbound,_ = cols[0].split("-")
        main_seg = cols[1].split("-")
        main_form = "".join(main_seg)
        continue

      if cols[0]==lbound:
        segments = main_seg
        form = main_form
      else:
        segments = [x for x in cols[1].split("-") if x != ""]
        form = "".join(segments)

      try:
        lemma = segments[0]
      except:
        pdb.set_trace()

      upos = normalize_upos(form,cols[3],cols[7])
      pos_vocab.add(upos)

      filtered = []
      if not cols[1].startswith("-"):
        # original root
        parse_opts = get_morph_annon("".join(segments).lower(),args.fst)

        # guesser with generic root-m1-m2-..
        if parse_opts==[]:
          parse_opts = get_morph_annon("root" +"".join(segments[1:]).lower(),args.fst)

        # filter MA options using segmented form (x-x-x)
        for morph_tags in parse_opts:
          if len(morph_tags)<2: continue
          # if any([upos!='CONJ' and upos!=morph_tags[0],
          #         upos=='CONJ' and morph_tags[0] not in ['SCONJ','CCONJ'],
          #       ]):
          if upos=='CONJ' and morph_tags[0] in ['SCONJ','CCONJ']:
            upos = morph_tags[0]
          if upos!=morph_tags[0]:
            continue
          #morph_tags = morph_tags[1:]
          #if morph_tags==[]: continue
          morph_tags = [[x,y] for x,y in morph_tags[1:] if x!="_"]
          #if len(filt_morph_tags) != len(morph_tags):
          #  zerom_id = i
          match = True
          min_len = min(len(segments[1:]),len(morph_tags))
          for sid in range(-1,-min_len,-1):
            suff = segments[sid]
            norm,tag = morph_tags[sid]
            if suff!=norm and not morph_mapper.is_allomorph(norm,tag,suff):
              match = False
              break
          if match:
            filtered.append(morph_tags)
        #END-FOR-M-TAGS

        # pdb.set_trace()
        
      ##
      orig_annot.append(cols[1])  # save original annotation for MISC
      cols[1] = cols[1].replace("-","")
      cols[3] = upos
      if cols[1]=='&hypen':
        cols[1] = "-"
      sent_cols.append(cols)
      lemmas.append(lemma)
      sent_morph_tags.append(filtered)
    ##END-FOR-SENT-BLOCK

    pop_sent_cols = morph_mapper.get_conllu_cols_conllu(sent_cols,lemmas,sent_morph_tags)

    #if zerom_id!=-1:
    #  pdb.set_trace()

    for i,fcol in enumerate(pop_sent_cols):
      sent_cols[i][4] = fcol[3] # xpos
      sent_cols[i][5] = fcol[4] # feats
      extra = "" if fcol[5]=="_" else  "|" + fcol[5]
      sent_cols[i][9] =  orig_annot[i] + extra # misc
      sent_cols[i][0] = str(i+1)

      # print(sent_cols[i])
    #
    
    text = " ".join([x[1] for x in sent_cols])
    print("# sent_id =",sent_count,file=pop_out)
    print("# text =",text,file=pop_out)
    print("\n".join(['\t'.join(x) for x in sent_cols]),file=pop_out)
    print("",file=pop_out)
    sent_count += 1

    if sent_count%10 == 0:
      print("->",sent_count)
  ##


  #pdb.set_trace()
    
      

