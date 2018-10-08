from pan4.preprocess import children
import pdb

def remove_token(sentence, i):
    words, tags, heads, labels = sentence
    _children = children(heads)

    chunk_start = i
    while _children[chunk_start] and min(_children[chunk_start]) < chunk_start:
        chunk_start = min(_children[chunk_start])
    chunk_end = i
    while _children[chunk_end] and max(_children[chunk_end]) > chunk_end:
        chunk_end = max(_children[chunk_end])

    heads = [h-(chunk_end+1-chunk_start) if type(h)==int and h >= chunk_start else h for h in heads[:chunk_start] + heads[chunk_end+1:]]

    def glue(lst):
        if type(lst) == dict:
            return {key: glue(val) for key,val in lst.items()}
        return lst[:chunk_start] + lst[chunk_end+1:]

    sentence = glue(words), glue(tags), heads, glue(labels)
    return sentence, chunk_start

def switch_tokens(sentence, i):
    # i <-> i+1
    words, tags, heads, labels = sentence
    _children = children(heads)

    chunk_start = i
    while _children[chunk_start] and min(_children[chunk_start]) < chunk_start:
        chunk_start = min(_children[chunk_start])
    chunk_end = i+1
    while _children[chunk_end] and max(_children[chunk_end]) > chunk_end:
        chunk_end = max(_children[chunk_end])

    if heads[i] == i+1:
        # mv i+1 before chunk(i)
        heads = [chunk_start if h==i+1 else h for h in heads[:chunk_start]] + heads[i+1:i+2] + [h+1 for h in heads[chunk_start:i]] + [chunk_start] + [chunk_start if h==i+1 else h for h in heads[i+2:]]
        chunk_end = i+1
    elif heads[i+1] == i:
        # mv i after chunk(i+1)
        heads = [chunk_end if h==i else h for h in heads[:i]] + [chunk_end] + [h-1 for h in heads[i+2:chunk_end+1]] + heads[i:i+1] + [chunk_end if h==i else h for h in heads[chunk_end+1:]]
        chunk_start = i
    elif heads[i] == heads[i+1]:
        # mv chunk(i+1) before chunk(i)
        heads = heads[:chunk_start] + heads[i+1:i+2] + [h-(i+1-chunk_start) for h in heads[i+2:chunk_end+1]] + [h+(chunk_end-i) for h in heads[chunk_start:i]] + heads[i:i+1] + heads[chunk_end+1:]
    else:
        return sentence, i+1

    def glue(lst):
        if type(lst) == dict:
            return {key: glue(val) for key,val in lst.items()}
        return lst[:chunk_start] + lst[i+1:chunk_end+1] + lst[chunk_start:i+1] + lst[chunk_end+1:]

    sentence = glue(words), glue(tags), heads, glue(labels)
    return sentence, chunk_start


def rewrite_wals(dataset, ops=""):
    ratios = type('', (), {})()
    ratios.adp = ratios.gen = ratios.adj = ratios.det = ratios.num = (0,0)
    if type(ops) == str: ops = list(filter(None, ops.split("+")))
    for ex in dataset:
        yield rewrite1_wals(ex, ratios, ops)

def rewrite1_wals(sentence, ratios, ops=[]):

    def pattern_cpos(sentence,i,cpos):
        words, feats, _, _ = sentence
        return (i < len(words) and
                feats[i].cpos==cpos)
    def pattern_feat(sentence,i,feat):
        words, feats, _, _ = sentence
        key, val = feat
        features = feats[i].ufeats
        return (i < len(words) and
                (features.get(key)==val or
                 type(features.get(key))==list and val in features[key]))
    def pattern_dep(sentence,i,j):
        words, _, heads, _ = sentence
        return (i < len(words) and
                j < len(words) and
                heads[i]==j)
    def pattern_2related(sentence,i,j):
        words, _, heads, _ = sentence
        return (i < len(words) and
                j < len(words) and
                (heads[i]==j or
                 heads[j]==i or
                 heads[i]==heads[j]))

    # orig_sentence = [x.copy() for x in sentence]

    # transform
    for _ in range(3):
        for op in ops:
            op1,op2 = op.split('-')
            # delete
            if op1=='del':
                i = 1
                while i+1 < len(sentence[0]):
                    if op2=='def' and pattern_cpos(sentence,i,"DET") and pattern_feat(sentence,i,("Definite","Def")):
                        sentence, i = remove_token(sentence, i)
                    elif op2=='ind' and pattern_cpos(sentence,i,"DET") and pattern_feat(sentence,i,("Definite","Ind")):
                        sentence, i = remove_token(sentence, i)
                    elif op2=='d' and pattern_cpos(sentence,i,"DET"):
                        sentence, i = remove_token(sentence, i)
                    else:
                        i += 1
                continue

            # switch if necessary
            obj_ratio = float(op2)/100
            i = 1
            while i+1 < len(sentence[0]):
                if (op1=='adp'
                    and pattern_cpos(sentence,i,"NOUN") and pattern_cpos(sentence,i+1,"ADP") and pattern_2related(sentence,i+1,i)
                    and ratios.adp[0] < (obj_ratio-0.05) * ratios.adp[1]):
                        sentence, i = switch_tokens(sentence, i)
                elif (op1=='adp'
                      and pattern_cpos(sentence,i,"ADP") and pattern_cpos(sentence,i+1,"NOUN") and pattern_2related(sentence,i,i+1)
                      and ratios.adp[0] > (obj_ratio+0.05) * ratios.adp[1]):
                    sentence, i = switch_tokens(sentence, i)
                elif (op1=='ngen'
                      and pattern_cpos(sentence,i,"NOUN") and (pattern_cpos(sentence,i+1,"NOUN") or pattern_cpos(sentence,i+1,"PROPN")) and pattern_dep(sentence,i+1,i)
                      and ratios.gen[0] < (obj_ratio-0.05) * ratios.gen[1]):
                    sentence, i = switch_tokens(sentence, i)
                elif (op1=='ngen'
                      and (pattern_cpos(sentence,i,"NOUN") or pattern_cpos(sentence,i,"PROPN")) and pattern_cpos(sentence,i+1,"NOUN") and pattern_dep(sentence,i,i+1)
                      and ratios.gen[0] > (obj_ratio+0.05) * ratios.gen[1]):
                    sentence, i = switch_tokens(sentence, i)
                elif (op1=='adj'
                      and pattern_cpos(sentence,i,"NOUN") and pattern_cpos(sentence,i+1,"ADJ") and pattern_dep(sentence,i+1,i)
                      and ratios.adj[0] < (obj_ratio-0.05) * ratios.adj[1]):
                    sentence, i = switch_tokens(sentence, i)
                elif (op1=='adj'
                      and pattern_cpos(sentence,i,"ADJ") and pattern_cpos(sentence,i+1,"NOUN") and pattern_dep(sentence,i,i+1)
                      and ratios.adj[0] > (obj_ratio+0.05) * ratios.adj[1]):
                    sentence, i = switch_tokens(sentence, i)
                elif (op1=='det'
                      and pattern_cpos(sentence,i,"NOUN") and pattern_cpos(sentence,i+1,"DET") and pattern_dep(sentence,i+1,i)
                      and ratios.det[0] < (obj_ratio-0.05) * ratios.det[1]):
                    sentence, i = switch_tokens(sentence, i)
                elif (op1=='det'
                      and pattern_cpos(sentence,i,"DET") and pattern_cpos(sentence,i+1,"NOUN") and pattern_dep(sentence,i,i+1)
                      and ratios.det[0] > (obj_ratio+0.05) * ratios.det[1]):
                    sentence, i = switch_tokens(sentence, i)
                elif (op1=='num'
                      and pattern_cpos(sentence,i,"NOUN") and pattern_cpos(sentence,i+1,"NUM") and pattern_dep(sentence,i+1,i)
                      and ratios.num[0] < (obj_ratio-0.05) * ratios.num[1]):
                    sentence, i = switch_tokens(sentence, i)
                elif (op1=='num'
                      and pattern_cpos(sentence,i,"NUM") and pattern_cpos(sentence,i+1,"NOUN") and pattern_dep(sentence,i,i+1)
                      and ratios.num[0] > (obj_ratio+0.05) * ratios.num[1]):
                    sentence, i = switch_tokens(sentence, i)
                else:
                    i += 1

    # reestimate ratios
    for i in range(1,len(sentence[0])):
        if pattern_cpos(sentence,i,"NOUN") and pattern_cpos(sentence,i+1,"ADP") and pattern_2related(sentence,i+1,i):
            ratios.adp = ratios.adp[0], ratios.adp[1]+1
        if pattern_cpos(sentence,i,"ADP") and pattern_cpos(sentence,i+1,"NOUN") and pattern_2related(sentence,i,i+1):
            ratios.adp = ratios.adp[0]+1, ratios.adp[1]+1

        if pattern_cpos(sentence,i,"NOUN") and (pattern_cpos(sentence,i+1,"NOUN") or pattern_cpos(sentence,i+1,"PROPN")) and pattern_dep(sentence,i+1,i):
            ratios.gen = ratios.gen[0], ratios.gen[1]+1
        if (pattern_cpos(sentence,i,"NOUN") or pattern_cpos(sentence,i,"PROPN")) and pattern_cpos(sentence,i+1,"NOUN") and pattern_dep(sentence,i,i+1):
            ratios.gen = ratios.gen[0]+1, ratios.gen[1]+1

        if pattern_cpos(sentence,i,"NOUN") and pattern_cpos(sentence,i+1,"ADJ") and pattern_dep(sentence,i+1,i):
            ratios.adj = ratios.adj[0], ratios.adj[1]+1
        if pattern_cpos(sentence,i,"ADJ") and pattern_cpos(sentence,i+1,"NOUN") and pattern_dep(sentence,i,i+1):
            ratios.adj = ratios.adj[0]+1, ratios.adj[1]+1

        if pattern_cpos(sentence,i,"NOUN") and pattern_cpos(sentence,i+1,"DET") and pattern_dep(sentence,i+1,i):
            ratios.det = ratios.det[0], ratios.det[1]+1
        if pattern_cpos(sentence,i,"DET") and pattern_cpos(sentence,i+1,"NOUN") and pattern_dep(sentence,i,i+1):
            ratios.det = ratios.det[0]+1, ratios.det[1]+1

        if pattern_cpos(sentence,i,"NOUN") and pattern_cpos(sentence,i+1,"NUM") and pattern_dep(sentence,i+1,i):
            ratios.num = ratios.num[0], ratios.num[1]+1
        if pattern_cpos(sentence,i,"NUM") and pattern_cpos(sentence,i+1,"NOUN") and pattern_dep(sentence,i,i+1):
            ratios.num = ratios.num[0]+1, ratios.num[1]+1

    # for h in sentence[2][1:]:
    #     if h == None:
    #         pdb.set_trace()

    return sentence


def reorder_sentence(sentence, order):
    assert len(list(set(order))) == len(order)
    assert order and order[0] == 0 and order[-1] == len(order)-1

    words, features, heads, labels = sentence

    revorder = [new for _,new in sorted((old,new) for new,old in enumerate(order))]
    heads = [revorder[heads[old]] if heads[old] is not None else None for old in order]

    words = [words[old] for old in order]
    labels = [labels[old] for old in order]
    if type(features) == dict:
        features = {k: [v[old] for old in order] for k,v in features.items()}
    else:
        features = [features[old] for old in order]

    return words, features, heads, labels
