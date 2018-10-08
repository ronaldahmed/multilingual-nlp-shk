from utils import *
from sklearn.preprocessing import StandardScaler

import argparse


if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Run IR system w specific configuration.')
  parser.add_argument('--task','-t',type=int,default=1, help='Task id')
  parser.add_argument('--wals','-w',type=str,default="cze", help='WALS code')
  parser.add_argument('--genus','-g',type=str,default="none", help='Genus code')
  parser.add_argument('--family','-f',type=str,default="none", help='Family name')
   
  args = parser.parse_args()

  if args.task == 2 and args.genus=='none':
    print("Error: must specify genus!")
    sys.exit(1)

  
  data = pd.read_csv('../language.tsv',sep='\t',header=0)
  metadata = data[['wals_code','iso_code','glottocode','Name','countrycodes']]
  to_excl = [
    'wals_code','iso_code','glottocode','Name','countrycodes',
    "latitude", "longitude",
  ]

  num_feats = data[["latitude", "longitude"]]
  cat_feats = data[data.columns.difference(to_excl)]

  print("Extracting features...")
  feat_factory = FeatureFactory(cat_feats)
  X = feat_factory.get_features(cat_feats,num_feats)

  print("Dim reduction...")
  pca = PCA(n_components=50)
  stdsc = StandardScaler()
  xstd = stdsc.fit_transform(X)

  X = pca.fit_transform( xstd )

  if args.task == 1:
    print("Task 1: top k similar langs to %s..." % args.wals)
    qidx = np.where(metadata["wals_code"]==args.wals)[0][0]
    x_nc = np.vstack([X[:qidx,:],X[qidx+1:,:]])
    #topk = get_sim_topk(X[qidx,:],x_nc,10)
    topk = get_sim_topk(X[qidx,:],x_nc,20)
    for _id,sc in topk:
      print("%s(%s) : %.4f" % (metadata["Name"][_id],metadata["wals_code"][_id],sc) )

  elif args.task == 2:
    print("Task 2: get centroid lang for queried genus...")

    gidx = np.where(cat_feats["genus"]==args.genus)[0]

    centroid = X[gidx,:].sum(axis=0) / gidx.shape[0]
    top = get_sim_topk(centroid,X[gidx,:],1)
    top_glob_idx = gidx[top[0][0]]

    print("Centroid lang of genus %s: %s(%s)" % 
      (args.genus,metadata["Name"][top_glob_idx],metadata["wals_code"][top_glob_idx] ) )
    

  elif args.task == 3:
    print("Task 3: find most disimilar lang...")
    
    qidxs = []
    if args.genus=='none' and args.family=='none':
      # run over all wals
      qidxs = list(range(X.shape[0]))

    elif args.genus=='none':
      # run over family
      qidxs = np.where(cat_feats["family"]==args.family)[0]

    elif args.family=='none':
      # run over genus
      qidxs = np.where(cat_feats["genus"]==args.genus)[0]

    else:
      fidx = set(np.where(cat_feats["family"]==args.family)[0])
      gidx = set(np.where(cat_feats["genus"]==args.genus)[0])
      qidxs = list(fidx & gidx)
    ##

    centroid = X[qidxs,:].sum(axis=0) / len(qidxs)
    top = get_sim_topk(centroid,X[qidxs,:],-1)

    top_glob_idx = qidxs[top[0][0]]

    print("Most disimilar lang : %s(%s)" % 
      (metadata["Name"][top_glob_idx],metadata["wals_code"][top_glob_idx] ) )

  elif args.task == 4:
    print("Task 4: find similar langs to query in family/genus...")
    qidx = np.where(metadata["wals_code"]==args.wals)[0][0]

    print("Ranking by genus (%s)..." % cat_feats["genus"][qidx])
    qidxs = np.where(cat_feats["genus"]==cat_feats["genus"][qidx])[0]
    topk = get_sim_topk(X[qidx,:],X[qidxs,:],20)
    for _psid,sc in topk:
      _id = qidxs[_psid]
      print("%s(%s) : %.4f" % (metadata["Name"][_id],metadata["wals_code"][_id],sc) )
    print("-----------------------------------")

    print("Ranking by family (%s)..." % cat_feats["family"][qidx])
    qidxs = np.where(cat_feats["family"]==cat_feats["family"][qidx])[0]
    topk = get_sim_topk(X[qidx,:],X[qidxs,:],20)
    for _psid,sc in topk:
      _id = qidxs[_psid]
      print("%s(%s) : %.4f" % (metadata["Name"][_id],metadata["wals_code"][_id],sc) )

