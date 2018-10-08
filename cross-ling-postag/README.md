
0. concatenate source texts [from top dir]

cat parallel_batch1/cuentos_SHP.txt \
parallel_batch1/kindergardBook_SHP.txt \
parallel_batch1/legal_SHP.txt \
parallel_batch2/educativo.shp \
parallel_batch2/flashcards.shp \
parallel_batch2/bible_SHP.txt > hw03/data/all_SHP.txt


cat parallel_batch1/cuentos_SPA.txt \
parallel_batch1/kindergardBook_SPA.txt \
parallel_batch1/legal_SPA.txt \
parallel_batch2/educativo.es \
parallel_batch2/flashcards.es \
parallel_batch2/bible_SPA_utf8.txt > hw03/data/all_SPA.txt


#all*.txt: 29809 parallel sentences




------------------------------------------------------

1. preparation
## tokenization

# parallel corpus
~ms/tokenizer/tokenizer.perl -l es < data/all_SPA.txt > data/all.tok.spa
~ms/tokenizer/tokenizer.perl -l es < data/all_SHP.txt > data/all.tok.shp



## truecasing
# use monolingual data to train truecaser
~ms/recaser/train-truecaser.perl --model tokenizer/truecase-model.spa --corpus data/all.tok.spa
~ms/recaser/train-truecaser.perl --model tokenizer/truecase-model.shp --corpus data/all.tok.shp


# apply model to parallel data
~ms/recaser/truecase.perl --model tokenizer/truecase-model.spa < data/all.tok.spa > data/all.true.spa
~ms/recaser/truecase.perl --model tokenizer/truecase-model.shp < data/all.tok.shp > data/all.true.shp


## lowercasing
cat data/all.tok.spa | ~/playground/scripts/lowercase.pl > data/all.low.spa
cat data/all.tok.shp | ~/playground/scripts/lowercase.pl > data/all.low.shp



## clean & limit sent len to 80
~ms/training/clean-corpus-n.perl data/all.true spa shp data/all.clean 1 80

  # Input sentences: 29810  Output sentences:  29755

#  clean low data
~ms/training/clean-corpus-n.perl data/all.low spa shp data/all.low.clean 1 80




## (14) target LM

~ms/../bin/lmplz -o 3 < data/all.low.shp > extra/shp.all.low.lm

~ms/../bin/lmplz -o 3 < data/all.true.shp > extra/shp.all.true.lm



############################################################################

# udpipe model: spanish-ancora-ud-2.0-170801.udpipe

1. tag SPA

udpipe --tag --input=horizontal ~/udpipe-ud-2.0-170801/spanish-ancora-ud-2.0-170801.udpipe < data/all.clean.spa > data/all.clean.spa.conllu.tagged

udpipe --tag --input=horizontal ~/udpipe-ud-2.0-170801/spanish-ancora-ud-2.0-170801.udpipe < data/all.low.clean.spa > data/all.low.clean.spa.conllu.tagged


2. "tokenize" SHP w udpipe & output=connlu

udpipe --tokenize --tokenizer=presegmented --input=horizontal --output=conllu ~/udpipe-ud-2.0-170801/spanish-ancora-ud-2.0-170801.udpipe < data/all.clean.shp > data/all.clean.shp.conllu

udpipe --tokenize --tokenizer=presegmented --input=horizontal --output=conllu ~/udpipe-ud-2.0-170801/spanish-ancora-ud-2.0-170801.udpipe < data/all.low.clean.shp > data/all.low.clean.shp.conllu

edit manually: num-num : multiword-exp  :(


3.. fast align formating

python3 dump_fa_fomat.py data/all.clean.spa data/all.clean.shp > data/all.clean.fa

python3 dump_fa_fomat.py data/all.low.clean.spa data/all.low.clean.shp > data/all.low.clean.fa

4.. aligning with FA

fast_align -i data/all.clean.fa -d -o -v > alignment/spa-shp.clean.fa-ali
fast_align -i data/all.low.clean.fa -d -o -v > alignment/spa-shp.low.clean.fa-ali

## reverse
fast_align -i data/all.clean.fa -d -o -v -r > alignment/spa-shp.clean.fa-ali.rev
fast_align -i data/all.low.clean.fa -d -o -v -r > alignment/spa-shp.low.clean.fa-ali.rev


# vis
paste data/all.clean.spa \
data/all.clean.shp \
alignment/spa-shp.clean.fa-ali | ./alitextview.pl | less

paste data/all.low.clean.spa \
data/all.low.clean.shp \
alignment/spa-shp.low.clean.fa-ali | ./alitextview.pl | less


# vis reverse
paste data/all.clean.spa \
data/all.clean.shp \
alignment/spa-shp.clean.fa-ali.rev | ./alitextview.pl | less


# intersection simmetrization
atools -i alignment/spa-shp.clean.fa-ali -j alignment/spa-shp.clean.fa-ali.rev -c intersect > alignment/spa-shp.clean.fa-ali.intersect

atools -i alignment/spa-shp.low.clean.fa-ali -j alignment/spa-shp.low.clean.fa-ali.rev -c intersect > alignment/spa-shp.low.clean.fa-ali.intersect



5. project alignments

# truecase
python project_align.py --ts data/all.clean.spa.conllu.tagged --ut data/all.clean.shp.conllu --a alignment/spa-shp.clean.fa-ali.intersect

# lowercase
python project_align.py --ts data/all.low.clean.spa.conllu.tagged --ut data/all.low.clean.shp.conllu --a alignment/spa-shp.low.clean.fa-ali.intersect

# truecase w lowercase alignment model
python project_align.py --ts data/all.clean.spa.conllu.tagged --ut data/all.clean.shp.conllu --a alignment/spa-shp.low.clean.fa-ali.intersect


6. Prepare gold
a) dump pickle w gold data [do @ local machine]

python3 dump_gold.py

b) train tokenizer
# separate untagged data into train,val

ipython3 split_tokenizer.py data/all.clean.shp.conllu

ipython3 split_tokenizer.py data/all.low.clean.shp.conllu

# train udpipe tokenizer
sh train_tok.sh

      # command line test
        PREF=tokenizer/no_bible.spa-shp.clean.shp.conllu.tok

        udpipe --train tokenizer/model.run. \
        --tagger=none --parser=none \
        --heldout="$PREF"_val \
        --tokenizer epochs=2 \
        "$PREF"_train

        udpipe --train tokenizer/model.test \
        --tagger=none --parser=none \
        --heldout="$PREF"_val \
        --tokenizer run=2 \
        "$PREF"_train

        #eval

        udpipe --accuracy --tokenizer --input=conllu tokenizer/model.run. tokenizer/no_bible.spa-shp.clean.shp.conllu.tok_val



c) 10CV experiments
	for each iter
		baseline: 8 folds -> training
		proposed: projected + 8 folds -> training
		1 fold -> val
		1 fold -> test
        for this train,val,test:
            -> val_runs : pick best on val -> report test
                for upos | lemma
        -> acummulate best_test_upos | best_test_lemma
        

	avg test score / acc - f1

# test run
udpipe --train tagger/tuning/model.run.1 \
--input=conllu --heldout=tagger/val.conllu \
--tokenizer=none --parser=none \
tagger/train.conllu

udpipe --accuracy --tagger --input=conllu tagger/tuning/model.run.1 tagger/val.conllu

-------------
d) single training: mono

udpipe --train tagger/model.mono \
--input=conllu --heldout=tagger/val.conllu \
--tokenizer=none --parser=none \
tagger/train.fold.gold.conllu

- ext

udpipe --train tagger/model.ext \
--input=conllu --heldout=tagger/val.conllu \
--tokenizer=none --parser=none \
--tagger iterations=5 \
tagger/train.conllu


test:
udpipe --accuracy --tagger --input=conllu tagger/model.mono tagger/test.conllu

udpipe --accuracy --tagger --input=conllu tagger/model.ext tagger/test.conllu
