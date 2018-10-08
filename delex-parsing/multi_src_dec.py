import os,sys
from collections import defaultdict,Counter
import argparse
import subprocess as sp
import math
import pdb

sys.path.append("../hw06")
from pos_lm import UPOSDist
from main import uploadObject, calc_kl_cpos3, read_conllu


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("--langs", '-l', default="cs", type=str, help="Language codes")
  parser.add_argument("--w_mode", '-wm', default="bin", type=str, help="Weight mode [bin,klcpos]")
  parser.add_argument("--p_mode", '-pm', default="raw", type=str, help="preprocessing mode [raw,clean]")
  parser.add_argument("--output", '-o', default="bin.edges", type=str, help="Output filename")
  args = parser.parse_args()

  ###########

  langs = args.langs.split(',')
  lang2trees = defaultdict(list)
  lang2conllu = defaultdict(list)

  for lang in langs:
    blocks = open('parses/%s-shk.%s.conllu' % (lang,args.p_mode), 'r').read().strip('\n').split('\n\n')
    for bl in blocks:
      graph = []
      conllu_sent = []
      for line in bl.split('\n'):
        if line[0]=="#": continue
        fields = line.split('\t')
        u = fields[0]
        v = fields[6]
        graph.append(v+"-"+u)
        conllu_sent.append(fields)
      #
      lang2trees[lang].append(graph)
      lang2conllu[lang].append(conllu_sent)
    #
  #
  tgt_conllu = lang2conllu[langs[0]].copy()
  
  #########  
  distr_map = {}
  tgt_ditr = {}
  lang2klcpos = {}
  if args.w_mode=="klcpos":
    distr_map = uploadObject("../hw06/counts.pickle")
    for lang in langs:
      distr_map[lang].compute_parameters(smoothing="add", alpha=0)
    tgt_seq_list = read_conllu("parses/%s-shk.%s.conllu" % (langs[0],args.p_mode))
    tgt_ditr = UPOSDist()
    tgt_ditr.update_counts(tgt_seq_list)
    tgt_ditr.compute_parameters(smoothing="add", alpha=0.0001)

    for lang in langs:
      w = calc_kl_cpos3(tgt_ditr,distr_map[lang])
      lang2klcpos[lang] = math.pow(w,-1)

    print("klcpos scores:")
    for lang in langs:
      print(lang)
      print(lang2klcpos[lang])


  ###########

  outfile = open(args.output,'w')
  ntrees = len(tgt_conllu)

  
  for i in range(ntrees):
    text = ""
    combined = Counter()

    # simple binary voting
    if args.w_mode=='bin':
      for lang in langs:
        combined.update(lang2trees[lang][i])
      # fix outlet of root
      outedge,max_w = -1,-1
      edges = []
      for vu,cnt in combined.most_common():
        if vu[:2]!="0-":
          edges.append("%s %d"%(vu.replace('-',' '),-cnt))
        elif cnt > max_w:
          max_w = cnt
          outedge = vu
      #
      edges.append("%s %d"%(outedge.replace('-',' '),-max_w))
      text = " ".join(edges)
    
    # KLcpos weighting
    elif args.w_mode=="klcpos":
      combined = defaultdict(float)
      for lang in langs:
        w = lang2klcpos[lang]
        for vu in lang2trees[lang][i]:
          combined[vu] += w
      ##
      outedge,max_w = -1,-1
      edges = []
      for vu,w in combined.items():
        if vu[:2]!="0-":
          edges.append("%s %s"%(vu.replace('-',' '),str(-w)))
        elif w > max_w:
          max_w = w
          outedge = vu
      #
      edges.append("%s %s"%(outedge.replace('-',' '),str(-max_w) ))
      text = " ".join(edges)
    ##

    # pdb.set_trace()

    pobj = sp.Popen(["perl","run_edmonds.pl"],stdin=sp.PIPE,stdout=sp.PIPE)
    stdout,_ = pobj.communicate(input=text.encode("utf8"))
    mst = [x.split('-') for x in stdout.decode("utf8").split(",")]

    nroots = 0
    # replace col 6  - 7
    for v,u in mst:
      tgt_conllu[i][int(u)-1][6] = v
      deprel = ""
      if v=="0":
        deprel = "root"
      else:
        # get deprel from first lang that proposed it
        for lang in langs:
          if lang2conllu[lang][i][int(u)-1][7] == "root" and v!="0":
            continue
          if lang2conllu[lang][i][int(u)-1][6] == v:
            deprel = lang2conllu[lang][i][int(u)-1][7]
            break
      ##
      tgt_conllu[i][int(u)-1][7] = deprel
      if deprel=="root":
        nroots += 1
    #
    # pdb.set_trace()

    # print output to file
    print("\n".join(["\t".join(fields) for fields in tgt_conllu[i]]) + "\n", file=outfile )

    if i%10 == 0:
      print("->",i)

    if nroots>1:
      pdb.set_trace()
  #



