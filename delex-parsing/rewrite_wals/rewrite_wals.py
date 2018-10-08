#!/usr/bin/python3

import pdb

def rewrite_wals(source, target, src_filename, tgt_filename):
    from subprocess import check_output
    ops = check_output("grep -P '^{}\t{}\t' ./pair_ops".format(source,target), shell=True).decode("utf-8").split("\t")[2].strip()

    from pan4.transform import rewrite_wals
    from pan4.preprocess import check_projectivity
    from conll.io import rt, wt, feat2col

    with open(src_filename, 'rt', encoding='utf-8', errors='replace') as fh, open(tgt_filename, 'wt', encoding='utf-8', errors='replace') as out:
        dataset = rt(fh, multiroots=True, truncate_label=False)
        dataset = filter(lambda s: check_projectivity(s[2]), dataset)
        dataset = rewrite_wals(dataset, ops)
        wt(out, dataset, preprocess=feat2col)

if __name__ == '__main__':
    import sys
    rewrite_wals(*sys.argv[1:])
