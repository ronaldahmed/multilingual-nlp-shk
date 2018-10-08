from collections import namedtuple

Pan4 = namedtuple('Pan4', 'words tags heads labels')
Pan2 = namedtuple('Pan2', 'words tags')
Morpho = namedtuple('Morpho', 'cpos fpos lemma ufeats')

def pad_tokens(tokens):
    tokens.insert(0, '<start>')
    tokens.append('ROOT')
    return tokens

def root_at_start(words=None, tags=None, heads=None, labels=None):
    if (words and words[0] == 'ROOT'
        or tags and type(tags)==list and (tags[0].cpos if type(tags[0])==tuple and 'cpos' in dir(tags[0]) else tags[0]) == 'ROOT'
        or heads and heads[-1]):
        return words, tags, heads, labels
    if words:
        words = words[-1:] + words[1:-1]
    if tags:
        tags = tags[-1:] + tags[1:-1]
    if heads:
        heads = [0 if h==len(heads)-1 else h for h in heads[:-1]]
    if labels:
        labels = labels[-1:] + labels[1:-1]
    return Pan4(words, tags, heads, labels)

def root_at_end(words=None, tags=None, heads=None, labels=None):
    if (words and words[0] == '<start>'
        or tags and tags[0] == '<start>'):
        return
    if words:
        words.append(words[0])
        words[0] = '<start>'
    if tags:
        tags.append(tags[0])
        tags[0] = '<start>'
    if heads:
        for c,h in enumerate(heads):
            if h==0:
                heads[c]=len(heads)
        heads.append(0)
    if labels:
        labels.append(labels[0])
        labels[0] = None
