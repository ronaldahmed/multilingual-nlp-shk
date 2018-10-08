import os
import glob as gb
import numpy as np
import xml.etree.ElementTree as ET
from utils import *
from word_type import WordType
from lex_utils import *

from collections import Counter

import pdb

if __name__ == "__main__":
  tagged_corpora_dir = 'tagged'
  lexicon = {}
  morph_type = {}
  
  vocab = set()
  affix_dict = get_affix_dict()
    
  gold_data = []
  count = 0
  for filename in gb.glob(tagged_corpora_dir+"/*.xml"):
    try:
      tree = ET.ElementTree(file=filename)
    except:
      print(filename.split('/')[1])
      count += 1
      #continue
      pdb.set_trace()

    root = tree.getroot()
    for sentence in root:
      if sentence.tag == "lastSentence":
        continue #omit this cases
      firstWord = True

      proc_sentence = []
      skip = False
      
      for word in sentence:
        if not is_valid_annotation(word):
          print(filename.split('/')[1])
          print(word.get("token")," - ", word.get("posTag"))
          print("---not valid")
          count += 1
          pdb.set_trace()
          skip = True
          break
        try:
          candidate = WordType(word,affix_dict)
          lemma = "_" if candidate.lemma==None else candidate.lemma
          if candidate.pos=='PUNCT' and lemma=='':
            lemma = candidate.form
          
          if candidate.pos==None:
            print(filename.split('/')[1])
            print(word.get("token")," - ", word.get("posTag"))
            pdb.set_trace()

          proc_sentence.append([candidate.form,lemma,candidate.pos])
        except:
          print(filename.split('/')[1])
          print(word.get("token")," - ", word.get("posTag"))
          print("---uh caraju")
          pdb.set_trace()
          count += 1
      #END-WORDS
      if not skip:
        gold_data.append(proc_sentence)
    #END-FOR-SENT
  #END-FOR-FN
  print("changes left: ",count)
  print("Gold data: ", len(gold_data))

  print("#tokens: ",sum([len(x) for x in gold_data]))

  count_pos = Counter([x[2] for sent in gold_data for x in sent])
  lemmas = Counter([x[1] for sent in gold_data for x in sent])

  #pdb.set_trace()

  saveObject(gold_data,'gold.list')