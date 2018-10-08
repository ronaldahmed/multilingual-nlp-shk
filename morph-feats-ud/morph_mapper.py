import pandas as pd
import pdb
from collections import defaultdict

SUFFIX = "0"
WHOLE = "1"
ROOT = "2"
CLIT = "_"
accent_mark = [
  "á","é","í","ó","ú"
]

class Entry(object):
  def __init__(self,_pos,_morphs,_code,_feats,_form_code):
    self._pos = _pos
    self._morphs = _morphs.split(",")
    self._codes = _code.split(",")
    self._feats = dict([x.split("=") for x in _feats.split("|")])
    self._form_code = _form_code



class MorphMapper(object):
  def __init__(self,map_fn,allom_fn):
    self._pos2ids = {} # {pos::FORM_CODE : [entry_ids]}
    self._items = []
    self._print_debug = False
    ## read mapping table
    table = pd.read_csv(map_fn,sep='\t')
    for poss,morphs,codes,feats,form_code in \
            zip(table["pos"],table["morph"],table["code"],table["ud_feat"],table["root"]):
      pos_list = poss.split(",")
      item = Entry(pos_list,morphs,codes,feats,form_code)
      
      self._items.append(item)
      _id = len(self._items) - 1
      for pos in pos_list:
        pos_c = pos + "::" + str(form_code)
        if pos_c not in self._pos2ids:
          self._pos2ids[pos_c] = []  
        self._pos2ids[pos_c].append(_id)
      #
    ##

    ## read allomorphs table
    table = pd.read_csv(allom_fn,sep='\t')
    self.allomorph_table = {} # {norm : {"tag":str,"allm":[str] }}
    for norm,tag,allms in zip(table["norm"],table["tag"],table["allomorphs"]):
      self.allomorph_table[norm] = {"tag": tag, "allm": allms.split(',')}


  def is_allomorph(self,norm,tag,morph):
    if norm not in self.allomorph_table:
      return False
    return morph in self.allomorph_table[norm]["allm"] and self.allomorph_table[norm]["tag"]==tag


  def update_features(self,feats,to_add):
    """
    @param feats: {Name:Val}, features of the word parsed so far
    @param to_add: {Name:Val}, features to aggregate considering hierarchical precedence
    """
    for feat_name,val in to_add.items():
      # precedence goes from (higher) left to right
      feats[feat_name].add(val)
    return feats


  def debug(self,feats,pos,extra):
    print("\t  %s\t%s\t%s" % (pos,[x+"="+','.join(y) for x,y in feats.items()],extra))



  def get_wlvl_inner(self,form,lemma,upos,morph_tags,feats={}):
    """
    extract features from forms, root, and tagged morphemes
    """
    if self._print_debug: print(form,"||",upos)
    
    suff_entries  = self._pos2ids.get(upos + "::" + SUFFIX,[])
    whole_entries = self._pos2ids.get(upos + "::" + WHOLE,[])
    root_entries  = self._pos2ids.get(upos + "::" + ROOT,[])

    if whole_entries!=[] and self._print_debug:
      print("\tWHOLE WORD")

    ## WHOLE WORD FEATURES
    for entry_id in whole_entries:
      if form in self._items[entry_id]._morphs:
        feats = self.update_features(feats,self._items[entry_id]._feats)
        if self._print_debug: self.debug(feats,upos,form)

    if suff_entries!=[] and self._print_debug:
      print("\tSUFFIX")

    ## SUFFIX FEATURES
    for morph,code in morph_tags:
      for entry_id in suff_entries:
        if any([ morph=='_' and code.lower() in self._items[entry_id]._codes,
                 code=='_'  and morph.lower() in self._items[entry_id]._morphs,
                 morph!='_' and code!='_' and morph.lower() in self._items[entry_id]._morphs and \
                 code.lower() in self._items[entry_id]._codes ]):
          feats = self.update_features(feats,self._items[entry_id]._feats)
          if self._print_debug: self.debug(feats,upos,morph+"-"+code)

    if root_entries!=[] and self._print_debug: 
      print("\tLEMMA")
    # get stem from morph_an
    stem,root_tag = '',''
    for morph,code in morph_tags:
      if 'Root' in code or 'root' in code:
        stem = morph
        root_tag = code
        break

    ## LEMMA & STEM FEATURES
    for entry_id in root_entries:
      if lemma in self._items[entry_id]._morphs:
        feats = self.update_features(feats,self._items[entry_id]._feats)
        if self._print_debug: self.debug(feats,upos,lemma)
      if stem in self._items[entry_id]._morphs or root_tag in self._items[entry_id]._codes:
        feats = self.update_features(feats,self._items[entry_id]._feats)
        if self._print_debug: self.debug(feats,upos,lemma)

    if self._print_debug: print("\t",feats)
    return feats


  def get_word_lvl_features_by_pos(self,word,pos,feats={} ):
    """
    @param word: WordType object
    @param pos: POS tag to use for entries indexing.
    """
    form  = word.form
    stem = word.stem
    upos  = pos

    feats = self.get_wlvl_inner(form,stem,upos,word.affixes,feats)

    return feats




  def get_conllu_cols_wordtype(self,sentence):
    """
    @param sentence: [WordType]
    """
    conllu = []
    for i,word in enumerate(sentence):
      form  = word.form
      lemma = word.lemma
      upos  = word.pos
      xpos  = word.xpos
      feats = defaultdict(set)

      ####################
      ## word level features
      # specific POS feats have preference
      if upos=='CONJ':
        feats = self.get_word_lvl_features_by_pos(word,'CCONJ',feats)
        feats = self.get_word_lvl_features_by_pos(word,'SCONJ',feats)
      else:
        feats = self.get_word_lvl_features_by_pos(word,upos,feats)

      if self._print_debug: print("++++++++++++++++++++++++++++++++++++++++++++++++++++")
      # then clitic features
      feats = self.get_word_lvl_features_by_pos(word,CLIT,feats)

      if self._print_debug: print("++++++++++++++++++++++++++++++++++++++++++++++++++++")

      #####################
      # sentence-lvl rules
      # * if NOUN, accent -> Case=Voc
      if upos == 'NOUN' and any(voc in form for voc in accent_mark):
        feats["Case"].add("Voc")
      
      if i<len(sentence)-1:
        # * genitive case only if next word is also a NOUN 
        if sentence[i+1].pos=="NOUN" and upos=="NOUN":
          feats["Case"].add("Gen")
        # * ppart if V-a ika/iká iki construction
        if upos=="VERB":
          if all([form[-1]=="a",
                  sentence[i+1].form.lower() in ["iki","ika","iká"]
            ]):
            feats["Tense"].add("Pqp")
          if all([form[-1]=="i",
                  sentence[i+1].form.lower() in ["kai","kaai"]
            ]):
            feats["Tense"].add("Fut")
            feats["Aspect"].add("Imp")
          if all([form[-1]=="nonx",
                  sentence[i+1].form.lower() in ["iki","ika","iká"]
            ]):
            feats["Tense"].add("Fut")


      # * Aspect=Prog if verb_startswith(itai) [i-t-ai] (relax cond that MorphID must match)
    
      if all([upos=="VERB",
              form.lower().startswith("itai"),
              "tai" == "".join([morph for morph,code in word.affixes])
              ]):
        feats["Aspect"].add("Prog")


      #####
      morphs = []
      misc = []
      for name,val_set in feats.items():
        if len(val_set)==1:
          morphs.append(name+"="+''.join(val_set))
        else:
          misc.append(name+"="+','.join(sorted(val_set)))
      morphs.sort()
      misc.sort()
      morph_str = "|".join(morphs)
      misc_str = "|".join(misc)
      conllu.append([form,lemma,upos,xpos,morph_str,misc_str])
    ##
    return conllu




  def get_conllu_cols_conllu(self,sentence,lemmas,man_tags):
    """
    @param sentence: [conllu_cols]
    @param man_tags: tags obtained with morphological analyser,
                      [ [[m,t]_parse1,[m,t]_parse2,... ]_w1 ]
    """
    conllu = []
    for i,cols in enumerate(sentence):
      form  = cols[1].lower()
      upos  = cols[3]
      lemma = lemmas[i].lower()
      # xpos not populated yet in treebank
      # for now, similar format as ufeats
      xpos = set()
      # if len(man_tags[i])<2:
      #   xpos.add(upos)
      feats = defaultdict(set)

      for morph_der in man_tags[i]:
        _,new_tags = zip(*(morph_der))
        xpos.update(new_tags)

        ####################
        ## word level features
        # specific POS feats have preference
        feats = self.get_wlvl_inner(form,lemma,upos,morph_der,feats)
        
        if self._print_debug: print("++++++++++++++++++++++++++++++++++++++++++++++++++++")
        # then clitic features
        feats = self.get_wlvl_inner(form,lemma,CLIT,morph_der,feats)

        if self._print_debug: print("++++++++++++++++++++++++++++++++++++++++++++++++++++")

        # pdb.set_trace()

        #####################
        # sentence-lvl rules
        # * if NOUN, accent -> Case=Voc
        if upos == 'NOUN' and any(voc in form for voc in accent_mark):
          feats["Case"].add("Voc")
        
        if i<len(sentence)-1:
          # * genitive case only if next word is also a NOUN 
          if sentence[i+1][3]=="NOUN" and upos=="NOUN":
            feats["Case"].add("Gen")
          # * ppart if V-a ika/iká iki construction
          if upos=="VERB":
            if all([form[-1]=="a",
                    sentence[i+1][1].lower() in ["iki","ika","iká"]
              ]):
              feats["Tense"].add("Pqp")
            if all([form[-1]=="i",
                    sentence[i+1][1].lower() in ["kai","kaai"]
              ]):
              feats["Tense"].add("Fut")
              feats["Aspect"].add("Imp")
            if all([form[-1]=="nonx",
                    sentence[i+1][1].lower() in ["iki","ika","iká"]
              ]):
              feats["Tense"].add("Fut")

        # * Aspect=Prog if verb_startswith(itai) [i-t-ai] (relax cond that MorphID must match)
      
        if all([upos=="VERB",
                form.lower().startswith("itai"),
                "tai" == "".join([morph for morph,code in morph_der])
                ]):
          feats["Aspect"].add("Prog")
      #END-FOR-MORPH-DERVS
      if xpos != upos:
        xpos = list(xpos)
        xpos.sort()
        xpos = upos +"|"+ "|".join(xpos)

      morphs = []
      misc = []
      for name,val_set in feats.items():
        if len(val_set)==1:
          morphs.append(name+"="+''.join(val_set))
        else:
          misc.append(name+"="+','.join(sorted(val_set)))
      morphs.sort()
      misc.sort()
      morph_str = "|".join(morphs) if len(morphs)>0 else "_"
      misc_str = "|".join(misc) if len(misc)>0 else "_"
      conllu.append([form,lemma,upos,xpos,morph_str,misc_str])
    ##



    return conllu





