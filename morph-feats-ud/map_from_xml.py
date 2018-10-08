import os
import glob as gb
import numpy as np
import xml.etree.ElementTree as ET
from utils import *
from word_type import WordType
from lex_utils import *
from morph_mapper import MorphMapper

import argparse
import pdb


if __name__ == "__main__":
  # Parse arguments
  parser = argparse.ArgumentParser()
  parser.add_argument("--morph_map", default=".", type=str, help="Morphological dictionary")

  context_win = 3
  args = parser.parse_args()

  tagged_corpora_dir = 'tagged'
  
  morph_type = {}
  vocab = set()
  affix_dict = get_affix_dict()
  
  morph_mapper = MorphMapper(args.morph_map)

  output_conllu = open("gold.conllu",'w')
  count = 0

  for filename in gb.glob(tagged_corpora_dir+"/*.xml"):
    tree = ET.ElementTree(file=filename)
    root = tree.getroot()
    count += 1

    output_conllu.write("# sent %d\n" % count)

    for sentence in root:
      if sentence.tag == "lastSentence":
        continue #omit this cases
      
      proc_sent = []
      word_objs = []
      
      for word in sentence:
        #if not is_valid_annotation(word):
        #  continue
        candidate = WordType(word,affix_dict)
        lemma = candidate.lemma
        #if candidate.pos in ["PUNCT"] or candidate.form.isdigit():
        #  continue
        if lemma == None:
          print("-> no lemma for u")
          pdb.set_trace()        
        
        
        ###
        # candidate.affixes
        # candidate.lemma
        # candidate.pos
        # candidate.subpos
        #print("%s | %s | %s | %s , %s " % 
        #  (candidate.form,candidate.lemma," ".join([" (%s,%s)" % (x,y) for x,y in candidate.affixes]),candidate.pos,candidate.sub_pos) )
        #print("-------------------------------")
        
        word_objs.append(candidate)

      #END-SENTENCE

      #[form,lemma,xpos,upos,feat_str,misc_str]
      sent_conllu = morph_mapper.get_conllu_cols_wordtype(word_objs)
      #for x in sent_conllu: print(x)
      
      for i,cols in enumerate(sent_conllu):
        cols = [str(i+1)] + cols[:-1] + 3*["_"] + [cols[-1]]
        output_conllu.write("\t".join(cols)+"\n")

    #END-FOR-SENT
    output_conllu.write("\n")

  #END-FOR-FN
  output_conllu.close()
