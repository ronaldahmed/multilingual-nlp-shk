from __future__ import print_function

import os,sys
import argparse
import pdb
from collections import Counter
from string import punctuation


if __name__ == "__main__":
  # Parse arguments
  parser = argparse.ArgumentParser()
  parser.add_argument("--ts", type=str, help="Tagged source sentences in conllu format")
  parser.add_argument("--ut", type=str, help="Untagged target sentences in conllu format")
  parser.add_argument("--a" , type=str, help="Alignment file")
  args = parser.parse_args()

  source = open(args.ts,'r').read().split('\n\n')[:-1]
  target = open(args.ut,'r').read().split('\n\n')[:-1]
  alignment = open(args.a,'r').read().split('\n')
  nsents = len(source)

  low_pref = 'low_algm' if 'low' in args.a else 'true_algm'
  out_fn = args.ut + ".%s.proj" % low_pref
  print("Output file: ", out_fn)
  
  output = open(out_fn,'w')
  output_list = []
  tag_tracker = {}

  for idx in range(nsents):
    source_sents = source[idx].split('\n')
    target_sents = target[idx].split('\n')
    sid = 0
    tid = 0
    
    while source_sents[sid][0] == '#':  sid+=1
    while target_sents[tid][0] == '#': 
      #output.write(target_sents[tid] + '\n')
      output_list.append(target_sents[tid])
      tid+=1
    source_sents = [x.split('\t') for x in source_sents[sid:]]
    target_sents = [x.split('\t') for x in target_sents[tid:]]

    algns = alignment[idx].split()
    for al_str in algns:
      i,j = al_str.split('-')
      i,j = int(i), int(j)

      if target_sents[j][3] != "_":
        pdb.set_trace()
      else:
        target_sents[j][3] = source_sents[i][3]
    ##
    # dump projection
    output_list.extend(target_sents)
    for sent in target_sents:
      # count the tag aligned for this word form
      if sent[3]!="_":
        if sent[1] not in tag_tracker:
          tag_tracker[sent[1]] = Counter()
        tag_tracker[sent[1]].update([sent[3]])
      #
      #output.write('\t'.join(sent) + '\n')
      
    #
    #output.write('\n')
    output_list.append('')
  ##
  
  ##
  for i,out_sent in enumerate(output_list):
    if type(out_sent)==list:
      # punctuation is trivial
      if out_sent[1] in punctuation:
        out_sent[3] = 'PUNCT'

      if out_sent[3]=='_':
        # 1. unaligned but elsewhere in the data aligned, use most freq POS tag
        if out_sent[1] in tag_tracker:
          out_sent[3] = tag_tracker[out_sent[1]].most_common(1)[0][0]
          #print("opts: ",tag_tracker[out_sent[1]].most_common())
        # 2. if not aligned, back-off to NOUN
        else:
          #print("--fallback to noun")
          out_sent[3] = 'NOUN'
        #print("aft::  ",'\t'.join([out_sent[1],out_sent[3]]))
        #print()
        #pdb.set_trace()
      #
      output.write('\t'.join(out_sent) + '\n')
    
    else:
      output.write(out_sent + '\n')
    

  output.close()
