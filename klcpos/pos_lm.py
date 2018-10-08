import numpy as np
from collections import defaultdict,Counter
from label_dictionary import LabelDictionary
import pdb

class UPOSDist():
  def __init__(self):
    self.tagsize = 17+1
    self.tag2id = LabelDictionary()
    self.unigram_counts = np.zeros([self.tagsize],dtype=np.float32)
    self.bigram_counts = np.zeros([self.tagsize,self.tagsize],dtype=np.float32)
    self.trigram_counts = np.zeros([self.tagsize,self.tagsize,self.tagsize],dtype=np.float32)

    self.unigram_prob = np.zeros([self.tagsize],dtype=np.float32)
    self.bigram_prob = np.zeros([self.tagsize,self.tagsize],dtype=np.float32)
    self.trigram_prob = np.zeros([self.tagsize,self.tagsize,self.tagsize],dtype=np.float32)

    self.alpha = np.zeros(4)
    self.p_0 = 1.0 / self.tagsize
    self.tolerance = 1e-6
    self.MAX_ITERS = 50


  def update_counts(self,sequence_list):

    for sequence in sequence_list:
      nw = len(sequence)
      self.unigram_counts[ self.tag2id.add(sequence[1]) ] += 1

      for i in range(2,nw):
        y = self.tag2id.add(sequence[i])
        y1 = self.tag2id.add(sequence[i-1])
        y2 = self.tag2id.add(sequence[i-2])
        self.unigram_counts[y] += 1
        self.bigram_counts[y,y1] += 1
        self.trigram_counts[y,y1,y2] += 1
      #
    #
    return

  def compute_parameters(self,smoothing,alpha):
    self.unigram_prob = self.unigram_counts / self.unigram_counts.sum()
    self.bigram_prob  = self.bigram_counts / self.bigram_counts.sum()
    if smoothing=='add':
      ntrigrams = (self.trigram_counts!=0).sum()
      self.trigram_prob = (self.trigram_counts + alpha) / \
                          (self.trigram_counts.sum() + alpha*ntrigrams)
    else:
      self.trigram_prob = self.trigram_counts / self.trigram_counts.sum()

    return


  def calc_expected_alphas(self,sequence_list):
    p3,p2,p1 = 0,0,0
    alp_exp = np.zeros(4)
    for seq in sequence_list:
      for i in range(2,len(seq)):
        y = self.tag2id.get_label_id(seq[i])
        y1 = self.tag2id.get_label_id(seq[i-1])
        y2 = self.tag2id.get_label_id(seq[i-2])
        p1 = self.unigram_prob[y]
        p2 = self.bigram_prob[y,y1]
        p3 = self.trigram_prob[y,y1,y2]
        pt = np.array([self.p_0,p1,p2,p3]) * self.alpha
        alp_exp += pt / pt.sum()
    return alp_exp


  def comp_intp_smoothing(self,sequence_list):
    np.random.seed(42)
    self.alpha = np.random.random(4)
    prev = np.zeros(4,dtype=np.float32)

    count = 0
    while np.fabs(self.alpha - prev).sum() > self.tolerance \
          and count<self.MAX_ITERS:
      prev = self.alpha
      a_exp = self.calc_expected_alphas(sequence_list)
      self.alpha = a_exp / a_exp.sum()
      if count % 10 == 0:
        print("->",count,np.fabs(self.alpha - prev).sum())
        print(self.alpha)
        print("-"*40)
      count += 1

      # pdb.set_trace()
    #
    print("->",count,np.fabs(self.alpha - prev).sum())
    print(self.alpha)
    print("-"*40)

    for y in range(self.tagsize):
      for y1 in range(self.tagsize):
        for y2 in range(self.tagsize):
          self.trigram_prob[y,y1,y2] = self.trigram_prob[y,y1,y2] * self.alpha[3] + \
                                       self.bigram_prob[y,y1] * self.alpha[2] + \
                                       self.unigram_prob[y] * self.alpha[1] + \
                                       self.p_0 * self.alpha[0]
    #
    return

  # i,i-1,i-2
  def p_tg(self,x,y,z):
    return self.trigram_prob[x,y,z]