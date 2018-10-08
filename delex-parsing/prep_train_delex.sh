#!/bin/bash

mode=$1

# cs is done separetely, data is too big
langs="hi hr fi la nl sv"


for lang in $langs; do
	echo "lang: $lang"
	cat data/$lang.raw.conllu | grep -vP "^[0-9]+[.]" | grep -vP "^[0-9]+[-]" > data/tmp
	mv data/$lang.raw.conllu

	python3  clean_deprels.py data/$lang.raw.conllu > data/$lang.clean.conllu

	cd rewrite_wals/
	./rewrite_wals.py $lang shk ../data/$lang.clean.conllu ../data/$lang.rord.conllu
	cd ..

	cat data/$lang.$mode.conllu | udpipe --train --parser='embedding_form=0;embedding_feats=0;' \
	--tokenizer=none --tagger=none models/$lang.$mode.udpipe

done

if [ $mode = "clean" ]; then
	echo "delex baseline"
	python3 clean_deprels.py data/shk.raw.conllu > data/shk.clean.conllu
	cat data/shk.clean.conllu | udpipe --train --parser='embedding_form=0;embedding_feats=0;' \
	--tokenizer=none --tagger=none models/shk.clean.udpipe

	echo "lex baseline"
	cat data/shk.clean | udpipe --train --parser --tokenizer=none --tagger=none models/shk.clean.lex.udpipe
fi