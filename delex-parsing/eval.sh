#!/bin/bash

mode=$1

srcs="cs hr nl sv la hi fi shk"
# srcs="hi"

if [ $mode != "rord" ]; then
	echo "lexicalized"
	cat data/shk.$mode.conllu | udpipe --parse --accuracy models/shk.$mode.lex.udpipe
fi

for lang in $srcs; do
	echo "$lang"
	cat data/shk.$mode.conllu | udpipe --parse --accuracy models/$lang.$mode.udpipe
	udpipe --parse --input=conllu models/$lang.$mode.udpipe < data/shk.$mode.conllu > parses/$lang-shk.$mode.conllu
done