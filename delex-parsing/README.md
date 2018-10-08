NPFL120 - hw05: Delexilized Parsing
======================================================================

Results tables are summarized in ODS file results.ods.

- Source languages (chosen according to KLcPOS3 score):
  Czech, Croatian, Dutch, Swedish, Latin, Hindi, Finnish

- UD treebank version: v2.1

- Preprocessing strategies considered
	+ Original treebank ("raw" column)
	+ Dep-label trucation of sub-category (label:<sub>)  ("clean" row)
	+ Reordering of source sentences according to word ordered differentes with 
	  target language, using WALS word-order features [1] ("cln.rord" row)

- Source transfer strategies:
	+ Single source
	+ Multi-source combination with weighting method:
		- Count voting: w_edge = 1 for each parser ("binary" row)
		- KLcPOS3^-1 : w_edge = KLcPOS3^-1(tgt||src) 
			KLcPOS3^-4 was experimented, as recommended in [2], but more conservative 
			exponent gave better results


Summary of results:
- Best src: Hindi
- Best combination strat: count voting for UAS, not clear for LAS
- Slavic languages (cs,hr) are good for transfer probably because of freer word order and
  common ellipsis constructions.


[1]
@inproceedings{aufrant2016zero,
  title={Zero-resource dependency parsing: Boosting delexicalized cross-lingual transfer with linguistic knowledge},
  author={Aufrant, Lauriane and Wisniewski, Guillaume and Yvon, Fran{\c{c}}ois},
  booktitle={Proceedings of COLING 2016, the 26th International Conference on Computational Linguistics: Technical Papers},
  pages={119--130},
  year={2016}
}



[2]
@inproceedings{rosa2015klcpos3,
  title={Klcpos3-a language similarity measure for delexicalized parser transfer},
  author={Rosa, Rudolf and Zabokrtsky, Zdenek},
  booktitle={Proceedings of the 53rd Annual Meeting of the Association for Computational Linguistics and the 7th International Joint Conference on Natural Language Processing (Volume 2: Short Papers)},
  volume={2},
  pages={243--249},
  year={2015}
}