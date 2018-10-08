#!/usr/bin/python3

# launch eg. as UDPATH='~/data/universal_dependencies/ud-treebanks-*' ./pair_ops.py
# or UDPATH=~/data/universal_dependencies/ud-treebanks-v2.0 ./pair_ops.py
from os import environ
UDPATH = environ['UDPATH']

from subprocess import check_output

with open("codes","rt") as codes, open("crawled_features","wt") as out:
    for line in codes:
        line = line.strip().split()
        language, lg, family = line if len(line)==3 else [line[0], "", ""]
        line = [language, family] + ["{} {}".format(f, check_output("2>/dev/null wget http://wals.info/valuesets/{}-{} -O - | grep 'Value:' | grep -oP '<td>.*</td>' | cut -c5- | rev | cut -c6- | rev".format(f,lg), shell=True).decode('utf-8').strip()) for f in ['37A','38A','85A','86A','87A','88A','89A']]
        print("\t".join(line), file=out)


featmap = dict()
with open("wals_mapping","rt") as fh:
    for line in fh:
        line = line.strip().split("\t")
        featmap[line[0]] = line[1]

with open("crawled_features","rt") as fh:
    data = [line.strip().split("\t") for line in fh]
    data = [line[:2] + [featmap.get(f,f) for f in line[2:]] for line in data]
    data = [[check_output("(ls "+UDPATH+"/UD_{} | grep 'conllu' | sed 's/-ud-.*//'; echo '_') | head -1".format(line[0]), shell=True).decode('utf-8').strip()] + line for line in data]

with open("language_features","wt") as out:
    for line in data: print("\t".join(line), file=out)

from itertools import groupby
from operator import itemgetter
main_language = { line[1]: line[2:] for line in data if '-' not in line[1] }
genus_values = { k:list(v) for k,v in groupby(sorted(data, key=itemgetter(2)), key=itemgetter(2)) }
defaults = ["","","_","all-def","all-ind","adp-50","ngen-50","adj-50","det-50","num-50"]

# dialects and subtreebanks
data = [(line, main_language.get(line[1].split('-')[0])) for line in data]
data = [line[:2] + (line[2:] if line[2] or main is None else main) for line, main in data]
data = [line[:2] + [line[2] if line[2] else defaults[2]] + line[3:] for line in data]
data = [line[:3] + [([f] if f in featmap.values() else [l[i] for l in genus_values.get(line[2],[]) if l[i] in featmap.values() and not (l[i]=="del-d" and ("all-def" in line or "all-ind" in line))], defaults[i]) for i,f in enumerate(line[3:], start=3)] for line in data]
data = [line[:3] + [max(set(vote), key=vote.count) if vote else default for vote, default in line[3:]] for line in data]

with open("completed_language_features","wt") as out:
    for line in data: print("\t".join(line), file=out)


wals = dict()
with open("completed_language_features","rt") as fh:
    for line in fh:
        line = line.strip().split("\t")
        if line[0] != '_': wals[line[0]] = line[3:]


ops = dict()
with open("ops","rt") as fh:
    for line in fh:
        line = line.strip().split("\t")
        ops[line[0],line[1]] = line[2]

pairs = set()
with open("pair_ops","wt") as fh:
    lgs = sorted(wals.keys())
    for src in lgs:
        for tgt in lgs:
            o = [ops[x.strip(),y.strip()] for x,y in zip(wals[src],wals[tgt])]
            o = sorted(list(set(op for op in o if op != 'noop')))
            print("{}\t{}\t".format(src,tgt) + "+".join(o), file=fh)
