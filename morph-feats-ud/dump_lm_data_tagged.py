import os
import glob as gb

import xml.etree.ElementTree as ET
from lex_utils import *
from utils import *
from word_type import WordType


if __name__ == "__main__":
  affix_dict = get_affix_dict()
  for filename in gb.glob(tagged_corpora_dir+"/*.xml"):
    tree = ET.ElementTree(file=filename)
    root = tree.getroot()
    count += 1

    for sentence in root:
      if sentence.tag == "lastSentence":
        continue #omit this cases

      for word in sentence:
        candidate = WordType(word,affix_dict)
        lemma = candidate.lemma
        if lemma == None:
          print("-> no lemma for u")
          pdb.set_trace()        
        
      
  