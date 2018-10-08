import os
import subprocess as sp
import argparse

from multiprocessing import Pool
import re

import pdb



if __name__ == "__main__":
  parser = argparse.ArgumentParser() 
  parser.add_argument("--train", type=str, help="Training data, conll file")
  parser.add_argument("--val", type=str, help="Validation data, conll file ")
  parser.add_argument("--iters", default=20,type=int, help="Number of iterations for randomized search of hyperparams")
  parser.add_argument("--cpus", default=11,type=int, help="Number of iterations for randomized search of hyperparams")
  parser.add_argument("--mode", default="train",type=str, help="Train / test")
  args = parser.parse_args()

  def run_udpipe(idx):
    popen = sp.Popen(["udpipe","--train","tokenizer/tuning/model.run.%i" %(idx+1),
                  "--heldout="+args.val,
                  "--tagger=none", "--parser=none",
                  "--tokenizer", "run=%d" % (idx+2),
                  args.train])

    while popen.wait()==None: pass
    return

  res_re = re.compile("precision: (?P<p>[0-9]{0,2}[.][0-9]{0,2})[%], recall: (?P<r>[0-9]{0,2}[.][0-9]{0,2})[%], f1: (?P<f1>[0-9]{0,2}[.][0-9]{0,2})[%]")

  if args.mode == 'train':
    # train
    pool = Pool(args.cpus)
    pool.map(run_udpipe,range(args.iters))

    
  # evaluate after training / loading models
  best_f1, best_id = -1,-1
  for run_id in range(1,args.iters+1):
    popen = sp.Popen(["udpipe",
                      "--accuracy","--tokenizer","--input=conllu",
                      "tokenizer/tuning/model.run.%i" %(run_id),
                      args.val],
                  stdout=sp.PIPE)
    with popen.stdout as f:
      lines = f.read().decode('utf-8').split('\n')
      lines = [x for x in lines if x!='']
      mt = res_re.search(lines[-1])
      if mt:
        prec = float(mt.group('p'))
        rec = float(mt.group('r'))
        f1 = float(mt.group('f1'))

        print("run %d : P(%.2f) | R(%.2f) | F1(%.2f)" % (run_id,prec,rec,f1))

        if f1 > best_f1:
          best_f1 = f1
          best_id = run_id
        #
      #
    ##
  ###
  print("best conf:")
  print(best_f1,"||",best_id)

