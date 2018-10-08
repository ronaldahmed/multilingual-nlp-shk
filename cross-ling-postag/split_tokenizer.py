from __future__ import print_function

import os,sys
import pdb

from sklearn.model_selection import train_test_split

def dump_conll_tok(data,fn):
  with open(fn,'w') as out:
    for i,sent_str in enumerate(data):
      sents = sent_str.split('\n')
      if sents[0]=='# newdoc':
      	sents[2] = "# sent_id = %d" % (i+1)
      else:
      	sents[0] = "# sent_id = %d" % (i+1)
      out.write("\n".join(sents) + '\n\n')
	#
       

if __name__ == "__main__":
  data_file = sys.argv[1]
  data = open(data_file,'r').read().split('\n\n')[:-1]
  bn = os.path.basename(data_file)
  train,test  = train_test_split(data,test_size=0.1,random_state=42)

  dump_conll_tok(train,"tokenizer/%s.tok_train" % bn)
  dump_conll_tok(test,"tokenizer/%s.tok_val" % bn)