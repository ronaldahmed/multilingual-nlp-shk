POS & Morpho-Syntactic Harmonization of SHK
================================================================

The current version of the Shipibo treebank consists of 373 sentences without language specific POS tag or lemma annotation.
Although the annotation in the UPOS column does not entirely follow the UD guidelines, it was fixed with simple rules.


Files in directory:

* ud-shp-v3.5.conllu : Original unprocessed treebank

* ud-shp-v3.5.conllu.annot : harmonized treebank

* analyser_sk.fst : FST Morphological Analyser

* morph_map_table.tsv : Table used to map language specific morfological tags and affixes to Universal Features

* allomorphs.tsv : Maps the normalized affix (produced by the FST) to all its allomorphs.

* map_from_xml.py : XML data harmonizers. Input: XML. Output: Conllu

* map_from_conllu.py : Treebank harmonizer. Input: Conllu. Output: Conllu

Usage:
python3 map_from_conllu.py -i ud-shp-v3.5.conllu -fst analyser_sk.fst -m morph_map_table.tsv -a allomorphs.tsv
