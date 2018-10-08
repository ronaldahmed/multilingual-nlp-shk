import os,sys

import pandas as pd
import numpy as np
import pdb
from sklearn.decomposition import PCA
from sklearn.metrics.pairwise import cosine_similarity
from label_dictionary import LabelDictionary


class FeatureFactory(object):
  def __init__(self,data):
    self.features = LabelDictionary()
    self.extract_features(data)

  def extract_features(self,dframe):
    N = dframe.shape[0]
    for key,rows in dframe.items():
      for i in range(N):
        if pd.isnull(rows[i]): continue
        feat_name = key.lower()+"::"+rows[i].lower()
        self.features.add(feat_name)
      ##
    ##
    return
    

  def get_features(self,dframe,num_dframe):
    N = dframe.shape[0]
    X = np.zeros([N,len(self.features)+2],dtype=np.float64)

    for i in range(N):
      feats = set()
      for key,rows in dframe.items():  
        if pd.isnull(rows[i]): continue
        feat_name = key.lower()+"::"+rows[i].lower()
        feat_id = self.features.get_label_id(feat_name)
        feats.add(feat_id)
      ##
      X[i,list(feats)] = 1.0
    ##
    X[:,-2:] = num_dframe.as_matrix()
    
    return X


def get_sim_topk(candidate,data,k=10):
  '''
  candidate.shape = [1,D] | (D,)
  data:.shape = [M,D]
  '''
  M = data.shape[0]
  id_score = []
  for i in range(M):
    #sc = np.linalg.norm(candidate-data[i,:])
    sc = cosine_similarity(candidate.reshape([1,-1]),data[i,:].reshape([1,-1]))[0,0]
    id_score.append( [i,sc] )
  id_score.sort(key=lambda x: x[1],reverse=True)

  if k<0:
    return id_score[k:][::-1]

  return id_score[:k]