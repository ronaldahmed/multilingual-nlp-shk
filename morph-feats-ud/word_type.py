from utils import shp2ud_tagset,\
                  morph_code,\
                  subpos_code,\
                  clean_lemma
import pdb

class WordType(object):
  def __init__(self,et_node,affix_dict):
    self.lemma   =  "_"  if et_node.get("lemma")==None else clean_lemma(et_node.get("lemma").lower())
    
    self.pos  = shp2ud_tagset(et_node.get("posTag"))
    self.sub_pos = "_" if et_node.get("subPosTag")==None else subpos_code[et_node.get("subPosTag").lower()]
    self.xpos = et_node.get("posTag") 
    if self.sub_pos:
      self.xpos += "." + self.sub_pos
    self.form    = et_node.get("token").lower()
    self.affixes = []
    self.orig_code = []

    if self.lemma == 'wai ati':
      self.lemma = 'wai'

    for affix in et_node:
      if self.form == 'ja': # 'ja' is not divisible
        continue
      morph,pre_code = self.normalize_morph_code(affix.get("text"),affix.get("type"))
      if morph=='riva': morph = 'riba' # typo in original data
      code = pre_code
      self.orig_code.append(pre_code)
      pos = 'NOUN' if self.pos=='PROPN' else self.pos
      # normalization of clitics: {Nominals, 2nd pos, Free Pos} -> clit
      pos = 'clit' if 'clit' in pre_code else pos
      if pre_code=='+n':
        pos = 'NOUN'
      elif pre_code=='+v':
        pos = 'VERB'
      affix_dict_pos = ''
      # if no specific affixes are annotated for POS,
      # try with clitic affixes
      if pos not in affix_dict:
        affix_dict_pos = affix_dict['clit']
      else:
        affix_dict_pos = affix_dict[pos]
      #####
      # morph-code disambiguation
      if morph in affix_dict_pos:
        # more than one code for said morph
        if len(affix_dict_pos[morph])>1:
          if morph=='a' and code in ['+v_4','+v_+iki','+v','+v_2','+clitPartAg_4']: # assumed
            code = 'PP2'
          if morph=='a' and code=='+v_3':
            code = 'NMLZ'
          if morph=='a' and code=='+n_3':
            code = 'PSSS'
          #if morph=='n':
          #  code = 'ERG'
          if morph=='ai' and code=='+v_2':
            code = 'INC'

          if morph=='ai' and code in ['+v_1','+v']:
            code = 'PP1'
          if pre_code=="clitPos2" and morph=="ki":
            code = "INT"
          if pre_code.startswith('+clitN'):
            if morph == 'a':
              code = 'ABS'
            else:
              code = 'ERG'
        # only one option for said morph
        else:
          code = affix_dict_pos[morph][0]
        # if none of the above, choose first option
        if '+' in code:
          code = affix_dict_pos[morph][0]
      # morph is not in dictionary for this POS tag
      # try Clitics
      else:
        if morph in affix_dict['clit']:
          code = affix_dict['clit'][morph][0]
        else:
          pos = 'NOUN' if self.pos=='PROPN' else self.pos
          if morph in affix_dict[pos]:
            code = affix_dict[pos][morph][0]
      #END-IF
      self.affixes.append( (morph,code) )
    #END-FOR
    self.affixes = tuple(self.affixes)

  def compare(self,word_type):
    if self.form != word_type.form:
      return False
    if len(self.affixes) != len(word_type.affixes):
      return False
    for af1,af2 in zip(self.affixes,word_type.affixes):
      if af1 != af2:
        return False
    return True

  def __eq___(self,w2):
    return self.compare(w2)

  def __ne___(self,w2):
    return not self.compare(w2)  

  def __repr__(self):
    return "type:%s|%s|%s|%d" % (self.lemma,self.form,self.pos,len(self.affixes))

  def __hash__(self):
    return hash(self.lemma) ^ hash(self.pos) ^ hash(self.form) ^ hash(self.affixes)

  def visualize(self):
    print("\t%s | %s | %s" % (self.form,self.pos,self.sub_pos))
    for aff,_ty in self.affixes:
      print("\t\t> %s : %s" % (aff,_ty))
    return

  def normalize_morph_code(self,morph,code):
    if "FALTA" in morph:
      morph = morph[:-5]
    code = morph_code[code]
    if morph in ["a+iki","a + iki","ai + iki"]:
      morph = "a"
      code += "_+iki"
    idx = morph.find("#")
    if idx != -1:
      morph,case_num = morph.split("#")
      code = code + "_" + case_num
    return morph,code

  def encode_morphs(self):
    morphs = ["%s[%s]"  % (morph,code) for morph,code in self.affixes]
    return ' '.join(morphs)

  def encode_pos(self):
    return self.pos + ("["+self.sub_pos+"]" if self.sub_pos!="" else "")