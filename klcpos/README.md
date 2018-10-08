NPFL120 - HW06: KLcpos3
======================================================================

Source: all UDv2.1 treebanks
Target: Shipibo Konibo (SHK)

** Running the script

usage: main.py [-h] [--src SRC] [--ud_tbk UD_TBK] [--src_sm SRC_SM]
               [--tgt_sm TGT_SM] [--force]

optional arguments:
  -h, --help            show this help message and exit
  --src SRC, -s SRC     Source treebank file
  --ud_tbk UD_TBK, -u UD_TBK
                        Directory with ud treebanks
  --src_sm SRC_SM, -ss SRC_SM
                        Smooting conf for source [add-{alpha}]
  --tgt_sm TGT_SM, -ts TGT_SM
                        Smooting conf for target [add-{alpha}]
  --force, -f           Force counting


* Example: 
python3 main.py -s ../hw04/ud-shp-v3.5.conllu.annot -u ~/ud-treebanks-v2.1 -ss add-0 -ts add-0.0001

** Result files
* lists/ : folder with results for all tested configurations of smoothing (src-tgt) in the format 
		   "shk-add-alpha_src-alpha_tgt"
* results.ods : gathers the lists in a couple of spreadsheets for better comparison

** Highlights
- smoothing only target
  independent of the smoothing parameter, the top four are consistently: Czech, Dutch, Croatian, Latin
	The most similar languages according to the metric a
  Among the top ten we have et,fi,sv

- smoothing both target and source:
  for smoothing values in the range  1e-1 - 1.0 the top 20 gets invaded by languages with few data (yue,swl,kk).
  for small enough values of smoothing the results become more reliable, as larger treebanks are ranked higher.
  Worth noting that again cs,nl,hr,la,et,sv appear high in the table.

