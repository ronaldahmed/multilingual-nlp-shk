import pdb
import pickle

import re


punct = re.compile('[#$%&()+,-./:;<=>?@[\]^_`{|}~!]+')
numbers = re.compile("[0-9]+")


ud_tagset = [
  "ADJ",
  "ADV",
  "CONJ",
  "DET",
  "INTJ",
  "NOUN",
  "PROPN",
  "NUM",
  "ONOM",
  "INTW",
  "POSTP",
  "PRON",
  "PUNCT",
  "SYM",
  "VERB",
  "AUX",
]

## clitConcPart: VERB, ADV
## clitFreePos: VERB, CONJ, ADJ, NOUN

# as seen in tagged sentences
morph_code = {
  "Sufijo nominal" : "+n",
  "Sufijo verbal"  : "+v",
  "Prefijo" : "PREF",
  "Clít. nominal" : "+clitN",
  "Clít. de segunda posición" : "+clitPos2",
  "Clít. de posición libre" : "+clitPosFree",
  "Clít. concord. de particip." : "+clitPartAg"
}


subpos_code ={
  "no contable" : "UC",
  "contable" : "C",
  "locación" : "LOC",
  "tiempo" : "TEMP",
  "manera" : "Man",
  "cantidad": "Qnt",
  "espacial": "Spa",
  "subordinanate": "Subord",
  "subordinante" : "Subord",
  "coordinante": "Coor",
  "transitivo": "T",
  "intransitivo": "I",
  "copulativo": "COP",
  "cuantificador": "Qnt",
  "posesivo" : "POS",
  "demostrativo" : "Dem",
  "calificativo" : "Qlf",
  "indefinido" : "Indf",
  "enfático" : "EM",
  "personal" : "PROPN",
  "parte del cuerpo" : "Pref",
  "":""
}

# as seen in dictionary
dictpos2udmorph = {
  "conj." : "CONJ",
  "pf. modif." : "PREF",
  "sf. pos." : "POS1",
  "adj." : "ADJ",
  "posp." : "POSTP",
  "posp. conj." : "POSTP",
  "s." : "NOUN",
  "sf. de part." : "+clit",
  "adv." : "ADV",
  "part. de v. t." : "VERB[PP1]",
  "sf. interrog." : "INT",
  "sf. adv.": "+ADV",
  "sf. adj.": "+ADJ",
  "v. i." : "VERB[I]",
  "sf. de lugar": "LOC",
  "sf. s." : "+NOUN",
  "pron." : "PRON",
  "v. t." : "VERB[T]",
  "sf. modif." : "ADV",
  "sf. de tiempo" : "ADV",
  "sf. posp." : "POSTP",
  "sf. vbl." : "+NOUN",
  "sf. de derivación vbl." : "VBLZ",
  "sf. conj." : "CONJ",
  "sf. neg." : "NEG",
  "sf. honor." : "VOC",
  "sf. de v." : "+VERB",
  "sf. v. t." : "+VERB",
  "interj." : "INTJ",
  "sf. de s." : "+NOUN",
  "sf. de modo" : "ADV",
  "sf. imperat." : "IMP"

}



def shp2ud_tagset( pos ):
  if pos == "Adjetivo" : return "ADJ"
  if pos == "Adverbio" : return "ADV"
  if pos == "Conjunción" : return "CONJ"
  if pos == "Determinante" : return "DET"
  if pos == "Interjección" : return "INTJ"
  if pos == "Nombre" : return "NOUN"
  if pos == "Nombre Propio" : return "PROPN"
  if pos == "Numeral" : return "NUM"
  if pos == "Onomatopeya" : return "ONOM"
  if pos == "Palabra Interrogativa" : return "INTW"
  if pos == "Postposición" : return "POSTP"
  if pos == "Pronombre" : return "PRON"
  if pos == "Puntuación" : return "PUNCT"
  if pos == "Símbolo" : return "SYM"
  if pos == "Verbo" : return "VERB"
  if pos == "Verbo Auxiliar" : return "AUX"

def is_annot_sent( sentence ):
  # False for incorrectly annotated sentences
  for word in sentence:
    posTag = word.get("posTag")
    token = word.get("token")
    
    print("   ",posTag,token)

    if posTag==None or \
          any([
            #posTag == "Clítico",
            "ERR" in posTag,
            "ERR" in token,
            "error" in token ]):
      #pdb.set_trace()
      return False
  return True


def is_valid_annotation(word):
  token = word.get("token")
  pos = word.get("posTag")
  return "ERR" not in token and \
    "error" not in token and \
    pos!=None and \
    "ERR" not in pos and \
    pos != "Clítico"


def clean_lemma(lem):
  text = lem
  prv = "-1"
  while prv!=text:
    prv = text
    text = punct.sub("",text)
  return text


def saveObject(obj, name='model'):
  with open(name + '.pickle', 'wb') as fd:
    pickle.dump(obj, fd, protocol=pickle.HIGHEST_PROTOCOL)


def uploadObject(obj_name):
  # Load tagger
  with open(obj_name + '.pickle', 'rb') as fd:
    obj = pickle.load(fd)
  return obj


def dump_foma_format(fn,data,define_name,inside_tag,extra_comment='',pre_space=False):
  outfile = open(fn,'w')
  if extra_comment!='':
    outfile.write("# %s\n\n" % extra_comment)
  outfile.write("define %s [\n" % define_name)
  extra_space = ' ' if inside_tag=='Pref+' else ''
  pre_space = " " if pre_space else ''
  first = True
  for item in data:
    if not first:
      outfile.write('|')
    else:
      first = False
    outfile.write(' [ "%s%s[%s]%s" : {%s} ]\n' % (pre_space,item,inside_tag,extra_space,item))
  #
  outfile.write('] ;')
  outfile.close()
