import os,sys
import argparse
from multiprocessing import Pool
import subprocess as sp
import numpy as np
import glob as gb
import pdb
import pickle

from pos_lm import UPOSDist


BOUND="<s>"
EPS = 1e-100



def saveObject(obj, name='model'):
  with open(name + '.pickle', 'wb') as fd:
    pickle.dump(obj, fd, protocol=pickle.HIGHEST_PROTOCOL)


def uploadObject(obj_name):
  # Load tagger
  with open(obj_name, 'rb') as fd:
    obj = pickle.load(fd)
  return obj



def read_conllu(fname):
  data = []
  sent  = []
  for line in open(fname,'r'):
    line = line.strip('\n')
    if line=='' or line[0]=="#":
      continue
    cols = line.split('\t')
    if '-' in cols[0] or '.' in cols[0]:
      continue
    if cols[0]=='1' and len(sent)>0:
      data.append([BOUND]*2 + sent + [BOUND])
      sent = []

    if cols[3] == '_' or cols[3]=='':
      pdb.set_trace() 
    sent.append(cols[3])
  #
  if len(sent)>0:
    data.append([BOUND]*2 + sent + [BOUND])
  return data


# input: UPOSDist objects
def calc_kl_cpos3(tgt,src):
  res = 0.0
  tagsize = 17+1
  for y in range(tagsize):
    for y1 in range(tagsize):
      for y2 in range(tagsize):
        ptg = tgt.p_tg(y,y1,y2)
        if ptg!=0:
          res += ptg * (np.log2(ptg) - np.log2(src.p_tg(y,y1,y2) + EPS))
  #
  return res


if __name__ == "__main__":
  parser = argparse.ArgumentParser() 
  parser.add_argument("--src", "-s", type=str, default=None, help="Source treebank file")
  parser.add_argument("--ud_tbk", "-u", type=str, default=None, help="Directory with ud treebanks")
  parser.add_argument("--src_sm", "-ss", type=str, default="add-0.1", help="Smooting conf for source [add-{alpha}]")
  parser.add_argument("--tgt_sm", "-ts", type=str, default="add-0.1", help="Smooting conf for target [add-{alpha}]")
  parser.add_argument("--force","-f", action='store_true', help="Force counting")
  args = parser.parse_args()

  distr_map = {}
  s_sinfo = args.src_sm.split('-') 
  s_sinfo[1] = float(s_sinfo[1])
  t_sinfo = args.tgt_sm.split('-') 
  t_sinfo[1] = float(t_sinfo[1])
  
  if not os.path.exists("counts.pickle") or args.force:
    for ud_dir in os.listdir(args.ud_tbk):
      # print("="*60)
      print(ud_dir)
      tbk_files = gb.glob( os.path.join(args.ud_tbk,ud_dir,'*-ud-train.conllu') )
      if len(tbk_files)==0:
        tbk_files = gb.glob( os.path.join(args.ud_tbk,ud_dir,'*-ud-test.conllu') )
      
      for fn in tbk_files:
        code = os.path.basename(fn)[:2]
        if code not in distr_map:
          distr_map[code] = UPOSDist()
        seq_list = read_conllu(fn)
        distr_map[code].update_counts(seq_list)
      #
      # pdb.set_trace()
      # break
    #
    saveObject(distr_map,"counts")

  else:
    distr_map = uploadObject("counts.pickle")

  for lang in distr_map.keys():
    distr_map[lang].compute_parameters(smoothing=s_sinfo[0], alpha=s_sinfo[1])
    
  ## target reading

  tgt_seq_list = read_conllu(args.src)
  tgt_ditr = UPOSDist()
  tgt_ditr.update_counts(tgt_seq_list)
  tgt_ditr.compute_parameters(smoothing=t_sinfo[0], alpha=t_sinfo[1])

  outfile = open('shk-%s-%s' % (args.src_sm,args.tgt_sm),'w')

  triplets = []
  for lang,src_distr in distr_map.items():
    ntokens = src_distr.unigram_counts.sum()
    score = calc_kl_cpos3(tgt_ditr,src_distr)
    triplets.append([lang,ntokens,score])

  triplets.sort(key=lambda x: x[2])

  for lang,ntokens,score in triplets:
    print("%s,%d,%.6f" % (lang,ntokens,score), file=outfile)



