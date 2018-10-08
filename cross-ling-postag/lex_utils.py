import re
import pdb
from affixes import *
from collections import OrderedDict
import queue
import numpy as np


def get_closed_words():
  closed_dict = {}
  closed_dict["conj"] = open("closed/conj",'r').read().strip("\n").split("\n")
  closed_dict["dem"]  = open("closed/dem",'r').read().strip("\n").split("\n")
  closed_dict["group_nouns"] = open("closed/group_nouns",'r').read().strip("\n").split("\n")
  closed_dict["interj"]  = open("closed/interj",'r').read().strip("\n").split("\n")
  closed_dict["postpos"]  = open("closed/postpos",'r').read().strip("\n").split("\n")
  closed_dict["pref"]  = open("closed/pref",'r').read().strip("\n").split("\n")
  closed_dict["pron"]  = open("closed/pron",'r').read().strip("\n").split("\n")
  closed_dict["quant"]  = open("closed/quant",'r').read().strip("\n").split("\n")
  closed_dict["wh"]  = open("closed/wh",'r').read().strip("\n").split("\n")

  return closed_dict


def get_affix_dict():
  affix_dict = {}
  pos_suflist = zip(['NOUN','VERB','AUX','ADV','ADJ','POSTP','PRON','INTW','clit'],
                    [noun_suf,verb_suf,aux_suf,adv_suf,adj_suf,\
                     post_pos_suf,pron_suf,intw_suf,clit_suf])
  for pos,aff_list in pos_suflist:
    if pos not in affix_dict:
      affix_dict[pos] = {}
    for af,code in aff_list:
      if af not in affix_dict[pos]:
        affix_dict[pos][af] = set()
      affix_dict[pos][af].add(code)
  poss = affix_dict.keys()
  for pos in poss:
    sorted_af = list(affix_dict[pos].keys())
    sorted_af.sort(reverse=True,key=lambda x: len(x))
    temp = dict(affix_dict[pos])
    affix_dict[pos] = OrderedDict()
    for af in sorted_af:
      affix_dict[pos][af] = list(temp[af])
    
  return affix_dict


def copy_unique(to_list,from_list):
  to_copy = []
  for ff in from_list:
    found = False
    for tt in to_list:
      if ff == tt:
        found = True
        break
    if not found:
      to_copy.append(ff)
  to_list.extend(to_copy)

  return to_list


def lexicon_format(entry):
  wform = ''.join([a[0] for a in entry])
  morphs = " ".join(["%s[%s]" % (morph,code) for morph,code in entry[1:]])
  lformat = "%s\t%s\t%s %s" % (wform,entry[0][0],entry[0][1],morphs)
  return lformat

