from misc.io import read_tabular_file
from pan4.format import pad_tokens, Pan4, Morpho

import pdb


check_roots = False

def rt(filehandler, max_sent=None, multiroots=False, count_lines=False, truncate_label=True):
    header = "ID FORM LEMMA CPOS FPOS FEATURES HEAD LABEL CONSTRAINT TOK".split()

    line=1
    root_issues=0
    size=0

    if check_roots:
        print("\n" + filehandler.name, file=sys.stderr)

    for ex in read_tabular_file(filehandler, header, max_sent, count_lines=count_lines):
        if count_lines: n, ex = ex
        # TODO keep track of multi-tokens
        ex = [e for e in ex if '-' not in e["ID"]]
        def col(c): return [e[c] for e in ex]

        words = pad_tokens(col("FORM"))

        # TODO keep track of second part of the label
        labels = [None] + [(l.split(":")[0] if truncate_label else l) if l and l!="_" else None for l in col("LABEL")] + [None]

        heads = (None if e=="_" else int(e) for e in col("HEAD"))
        heads = [None] + [h if h != 0 else len(ex) + 1 for h in heads] + [0]

        constraints = col("CONSTRAINT")
        import re
        if not all(e=="_" for e in constraints) and all(all(re.match(c, "([_01]|([+-]\d*){1,2})$") for c in e) for e in constraints):
            constraints = ['_'] + constraints + ['1']
            constraints = [True if cstr=='1' else False if cstr=='0' or cstr=='_' else tuple(None if not i else int(i) for i in ((-1, cstr[1:]) if cstr[0] != '-' else (cstr[1:].split('+') + [-1])[:2])) for cstr in constraints]
            constraints = [(h if c else None) if type(c)==bool else c for h,c in zip(heads,constraints)]
            heads = heads, constraints

        cpos, fpos, lemma = col("CPOS"), col("FPOS"), col("LEMMA")
        ufeats = [[tuple(feat.split("=")) if "=" in feat else (feat,"") for feat in e.split('|') if feat!="_"] for e in col("FEATURES")]
        ufeats = [{key: (val.split(",") if "," in val else val) for key,val in feats} for feats in ufeats]

        tags = [Morpho(*tok) for tok in zip(*map(pad_tokens, (cpos, fpos, lemma, ufeats)))]

        line+=len(words)
        size+=1

        roots = sum(1 for h in heads if h == len(ex) + 1)
        if roots != 1 and "_" not in col("HEAD"):
            if check_roots:
                print("{} ROOT at lines {}-{}".format(sum(1 for h in heads if h==len(ex)+1), line-len(heads), line-2), file=sys.stderr)
            root_issues += 1
            if roots < 1 or not multiroots:
                continue
            #raise Exception("Did not detect ROOT")

        for h in heads[1:]:
            if h == None:   pdb.set_trace()

        ex = Pan4(words, tags, heads, labels)
        yield (n, ex) if count_lines else ex
    if check_roots:
        print("Total: {} root issues out of {} examples".format(root_issues, size), file=sys.stderr)

def wt(filehandler, dataset, preprocess=lambda x:x):
    for _ in lazy_wt(filehandler, dataset, preprocess=preprocess): pass

def lazy_wt(filehandler, dataset, preprocess=lambda x:x):
    from itertools import tee
    dataset, out = tee(dataset)
    for ex, ex_col in zip(dataset, preprocess(out)):
        if filehandler:
            tokens = ("\t".join(str(x) for x in (i,) + tuple(token)) for i,token in enumerate(ex_col) if i)
            for token in tokens:
                filehandler.write(token + "\n")
            filehandler.write("\n")
        yield ex

def lazy_rt(f_load, filename, forced=False, **kwargs):
    open = partial(open, encoding="utf-8", errors="replace")
    try:
        if forced: raise FileNotFoundError
        with open(filename, "rt") as fh:
            yield from rt(fh)
    except FileNotFoundError:
        with open(filename, "wt") as fh:
            yield from lazy_wt(fh, f_load(), **kwargs)

def feat2tag(dataset, pos_type="cpos"):
    for ex in dataset:
        yield ex._replace(tags=[t.__dict__[pos_type] for t in ex.tags]) if '_replace' in dir(ex) else ex[:1] + ([t.__dict__[pos_type] for t in ex[1]],) + ex[2:]

def tag2feat(dataset, pos_type="cpos"):
    keys = ["cpos","fpos","lemma","feats"]
    keys.remove(pos_type)
    cpos, fpos, lemma, feats = (pos_type,) + tuple(keys)
    for words, tags, heads, labels in dataset:
        yield Pan4(words, [Morpho(**{cpos: tag, fpos: "_", lemma: "_", feats: "_"}) for tag in tags], heads, labels)

def feat2col(dataset):
    from pan4.format import root_at_start
    for s in dataset:
        yield [(
            word,
            tag.lemma,
            tag.cpos,
            tag.fpos,
            "|".join("=".join(v if type(v)==str else ",".join(v) for v in f) for f in sorted(tag.ufeats.items())) if tag.ufeats and type(tag.ufeats)==dict else "_",
            head,
            label,
            "_",
            "_")
            for word, tag, head, label in zip(*root_at_start(*s))]

def tag2col(dataset, pos_type="cpos"):
    return feat2col(tag2feat(dataset, pos_type))
