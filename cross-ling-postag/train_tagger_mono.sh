#!/usr/bin/bash
python3 run_training.py --proj data/all.clean.shp.conllu.low_algm.proj \
--gold gold.list --cpus 7 --mode mono

python3 run_training.py --proj data/all.clean.shp.conllu.low_algm.proj \
--gold gold.list --cpus 7 --mode ext --tagger_iters 10