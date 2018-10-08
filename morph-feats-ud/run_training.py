import os
from utils import uploadObject
import subprocess as sp
import argparse
import numpy as np
import re

from multiprocessing import Pool
import pdb

upos_re = re.compile("upostag: (?P<upos>[0-9]{0,2}[.][0-9]{0,2})[%]")
lem_re = re.compile("lemmas: (?P<lemma>[0-9]{0,2}[.][0-9]{0,2})[%]")

def k_perm(base,k):    
  for e in base:  
    if k == 1:
      yield [e]      
    else:
      for perm in k_perm(base-set([e]),k-1):
        yield [e] + perm


def dump_temp_conllu(data,filename,header=True,offset=0):
  out = open(filename,'w')
  if header:
    out.write("# newdoc\n# newpar\n")
  #else:
  #  out.write("\n")
  for i,sent in enumerate(data):
    out.write("# sent_id = %d\n" % (i+1+offset))
    
    for wi,(form,lem,pos) in enumerate(sent):
      cf = ["_"] * 10
      cf[0] = str(wi+1)
      cf[1] = form
      cf[2] = lem
      cf[3] = pos
      if wi==len(sent)-1:
        cf[-1] = "SpacesAfter=\\n"
      try:
        out.write("\t".join(cf) + '\n')
      except:
        print(cf)
        pdb.set_trace()
    ##
    out.write("\n")
  ##
  out.close()


def eval_model(pref,run_id,test_fn):
  popen = sp.Popen(["udpipe",
                    "--accuracy","--tagger","--input=conllu",
                    "tagger/tuning/model.%s.run.%i" %(pref,run_id),
                    "tagger/val.conllu"],
                    stdout=sp.PIPE)
  upos,lem = -1,-1
  with popen.stdout as f:
    lines = f.read().decode('utf-8').split('\n')
    lines = [x for x in lines if x!='']
    upos_mat = upos_re.search(lines[-1])
    if upos_mat:
      upos = float(upos_mat.group('upos'))
      
    lemma_mat = lem_re.search(lines[-1])
    if lemma_mat:
      lem = float(upos_mat.group('lemma'))
  return upos,lem
      

def pick_best(pref,val_runs):
  best_upos,best_lem,u_is,l_id = -1,-1,-1,-1
  for i in range(1,val_runs+1):
    upos,lem = eval_model(pref,i,"tagger/val.conllu")
    if upos > best_upos:
      best_upos = upos
      u_id = i
    if lem > best_lem:
      best_lem = lem
      l_id = i
  ## END-FOR
  #print("best conf UPOS :",best_upos,"||",u_id)
  #print("best conf lemma:",best_lem,"||",l_id)
  return u_id,l_id


if __name__ == "__main__":
  parser = argparse.ArgumentParser() 
  parser.add_argument("--proj", type=str, help="Projected data in conllu format")
  parser.add_argument("--gold", type=str, help="Gold file of gold data ")
  parser.add_argument("--k", default=3,type=int, help="Number of folds")
  parser.add_argument("--val_runs", default=5,type=int, help="Number of iterations for randomized search of hyperparams")
  parser.add_argument("--cpus", default=10,type=int, help="Number of iterations for randomized search of hyperparams")
  parser.add_argument("--tagger_iters", default=20,type=int, help="Number of folds")
  parser.add_argument("--mode", default="mono",type=str, help="Training strategy: mono, ext")
  
  args = parser.parse_args()
  log_file = open("tagger/train.log",'w')


  gold = uploadObject(args.gold)

  np.random.seed(42)
  np.random.shuffle(gold)

  ## find out how many sents there are in projected data file
  popen = sp.Popen(["tail","-100",args.proj],
                  stdout=sp.PIPE)
  nsents_proj = 0
  with popen.stdout as f:
    for line in f:
      line = line.decode('utf-8').strip("\n")
      if not line.startswith('# sent_id'):
        continue
      nsents_proj = int(line[line.find("=") +2:])

  ###
  fold_size = len(gold) // args.k

  ###

  def run_udpipe_mono(idx):
    popen = sp.Popen(["udpipe","--train","tagger/tuning/model.mono.run.%i" %(idx),
                      "--input=conllu",
                      "--heldout=tagger/val.conllu",
                      "--tokenizer=none","--parser=none",
                      "--tagger", "run=%d;iterations=%d" % (idx,args.tagger_iters),
                      "tagger/train.fold.gold.conllu"],
                      stdout=sp.DEVNULL)

    while popen.wait()==None: pass
    return

  def run_udpipe_ext(idx):
    popen = sp.Popen(["udpipe","--train","tagger/tuning/model.ext.run.%i" %(idx),
                      "--input=conllu",
                      "--heldout=tagger/val.conllu",
                      "--tokenizer=none","--parser=none",
                      "--tagger", "run=%d;iterations=%d" % (idx,args.tagger_iters),
                      "tagger/train.conllu"],
                      stdout=sp.DEVNULL)

    while popen.wait()==None: pass
    return
  ###
  
  count_cv = 0
  total_upos,total_lem = 0,0

  pool = Pool(args.cpus)

  ## k=10 : 90 iters
  print("Running CV:::::::::::::::::",file=log_file)
  for val_id,test_id in k_perm(set(range(args.k)),2):
    val_idxs = range(val_id*fold_size,(val_id+1)*fold_size)
    test_idxs = range(test_id*fold_size,(test_id+1)*fold_size)
    val  = gold[val_id*fold_size:(val_id+1)*fold_size]
    test = gold[test_id*fold_size:(test_id+1)*fold_size]
    train = [x for i,x in enumerate(gold) if i not in val_idxs and i not in test_idxs]

    dump_temp_conllu(val,"tagger/val.conllu")
    dump_temp_conllu(test,"tagger/test.conllu")
    dump_temp_conllu(train,"tagger/train.fold.gold.conllu",False,nsents_proj)

    if args.mode=='ext':
      popen = sp.Popen(["cat",args.proj,"tagger/train.fold.gold.conllu"],
        stdout=open("tagger/train.conllu",'w'))
      while popen.wait()==None: pass

    #pdb.set_trace()
    upos,lem = -1,-1
    if args.mode=='mono':
      #### run train on gold tagged data
      pool.map(run_udpipe_mono,range(1,args.val_runs+1))
      
      #   evaluate mono
      u_id,l_id = pick_best("mono",args.val_runs)
      upos,_ = eval_model("mono",u_id,"tagger/test.conllu")
      _,lem  = eval_model("mono",l_id,"tagger/test.conllu")
      
    else:
      #### run train on gold tagged data + projected
      pool.map(run_udpipe_ext,range(1,args.val_runs+1))

      #   evaluate extended
      u_id,l_id = pick_best("ext",args.val_runs)
      upos,_ = eval_model("ext",u_id,"tagger/test.conllu")
      _,lem  = eval_model("ext",l_id,"tagger/test.conllu")
      
    total_upos += upos
    total_lem += lem
    print("\tCV_iter(%d) | Test: upos(%.4f), lemma(%.4f)" % (count_cv,upos,lem),file=log_file)

    ##
    count_cv += 1
    
  ##END-CV

  total_upos /= count_cv
  total_lem /= count_cv
  

  print("=================================================================",file=log_file)
  print("=================================================================",file=log_file)
  print("=================================================================",file=log_file)
  print("Setups:",file=log_file)
  print("CV test: upos(%.4f), lemma(%.4f)" % (total_upos,total_lem),file=log_file)
  
  log_file.close()
