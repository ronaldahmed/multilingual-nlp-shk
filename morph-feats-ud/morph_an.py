from lex_utils import get_affix_dict


class MorphAn(object):
  def __init__(self):
    self.affix_dict = get_affix_dict()
    self.closed_words = {}
    self.dict_lemmas = {}
    self.read_closed_words()
    self.read_dict_lemmas()
    self.closed_tags = ['CONJ','INTJ','POSTP','PRON','INTW']
    self.open_tags = ['NOUN','VERB','ADJ','ADV']
    
  def read_closed_words(self):
    '''
    Reads closed-class words from external lists
    '''
    self.closed_words["CONJ"] = open("closed/conj",'r').read().strip("\n").split("\n")
    self.closed_words["ADJ"]  = open("closed/dem",'r').read().strip("\n").split("\n")
    self.closed_words["NOUN"] = open("closed/group_nouns",'r').read().strip("\n").split("\n")
    self.closed_words["INTJ"]  = open("closed/interj",'r').read().strip("\n").split("\n")
    self.closed_words["POSTP"]  = open("closed/postpos",'r').read().strip("\n").split("\n")
    self.closed_words["PREF"]  = open("closed/pref",'r').read().strip("\n").split("\n")
    self.closed_words["PRON"]  = open("closed/pron",'r').read().strip("\n").split("\n")
    self.closed_words["ADJ"].extend(open("closed/quant",'r').read().strip("\n").split("\n"))
    self.closed_words["INTW"]  = open("closed/wh",'r').read().strip("\n").split("\n")

  def read_dict_lemmas(self):
    '''
    Reads lemmas extracted from dictionary
    '''
    for line in open('lexicon/dictionary.lex','r'):
      wform,lemma,pos = line.strip('\n').split('\t')
      if wform not in self.dict_lemmas:
        self.dict_lemmas[wform] = []
      self.dict_lemmas[wform].append(pos)

  def get_valid_codes(self,curr_stem,pos):
    '''
    @param curr_stem: current stem
    @param pos      : POS tag
    return
      The function will search for affixes that match the end of the stem,
      from the longest one to the shortest one. Only affixes known to be
      associated with the given POS tag are tested.
      Returns the longest affix matched along with its morpho-syntactic code.
    '''
    for af,_codes in self.affix_dict[pos].items():
      na = len(af)
      if na < len(curr_stem) and curr_stem[-na:]==af:
        codes = [(af,x) for x in _codes]
        return set(codes)
    return set()
  
  def collapse_affixes(self,wform,init_pos='*',depth=0):
    '''
    @param wform   : word form to segment
    @param init_pos: POS tag of wform (* : not defined)
    @param depth   : how many suffixes were extracted before
    return
      A list of candidate segmentations, each one in the format
        (lemma,POS),(suf_1,code_1), ..., (suf_n,code_n)
      where code_i is the morpho-syntactic code of suf_1, 'n' is the number of
      suffixes that were segmented.
      Note: this function is used for raw data.
    '''
    # if word form is in dictionary,
    # discard if initial POS tag is not among those in the entry in the dictionary
    if wform in self.dict_lemmas and init_pos not in self.dict_lemmas[wform]:
      return []

    # candidates are build incrementaly
    prev_incompletes = [] # yet incomplete candidates
    completes = []        # complete candidates

    # the initial call over a word form is done with init_pos=*
    # (when this function is called from outside the class);
    # this way, all posible POS tags are considered as starting points
    if init_pos=='*':
      # get segmentations for every initial POS tag
      for pos,af_dict in self.affix_dict.items():
        com = self.collapse_affixes(wform,pos)
        completes.extend(com)
    # case when the function is called with a specified POS tag
    else:
      curr_stem = wform
      ## convention: NOUN:P <> NP
      # all blocks are phrases unless proved otherwise (when segmentation is finished)
      curr_pos = init_pos if ':' not in init_pos else init_pos[:-2]
      
      # main loop
      while True:
        # obtain valid (affix,morph_code) pairs (check function documentation)
        codes = self.get_valid_codes(curr_stem,curr_pos)
        # if no valid affix was found, try testing if it is a clitic
        # clitics can precede at most 2 suffixes.
        if depth<=2 and len(codes)==0:
          codes = self.get_valid_codes(curr_stem,"clit")
        # It seems that the stem has no affixes, check if it is closed-class word
        if len(codes)==0:
          found = False
          for _pos,cw_list in self.closed_words.items():
            if curr_stem in cw_list:
              _pos = 'NOUN' if _pos=='clit' else _pos
              for i,a in enumerate(prev_incompletes):
                prev_incompletes[i] = [(curr_stem,_pos)] + prev_incompletes[i]
              found = True
              break
          # stem is not a closed-class word, output candidate with current stem
          # and previously gathered affixes
          if not found:
            # by default, a stem is a NOUN
            curr_pos = "NOUN" if curr_pos=='clit' else curr_pos
            for i,a in enumerate(prev_incompletes):
              prev_incompletes[i] = [(curr_stem,curr_pos)] + prev_incompletes[i]
          break
        #####
        # Zero-morph derivations
        res = []
        if curr_pos=='NOUN':
          # NP -> VP
          if curr_stem in ['keen','shiwan']: # known cases of zero-morph derivation
            res = self.collapse_affixes(curr_stem,'VERB:P',depth)
          # NP -> ADVP
          res_adv = self.collapse_affixes(curr_stem,'ADV:P',depth)
          res.extend(res_adv)
        elif curr_pos=='ADJ':
          # ADJP -> VP
          res_adj = self.collapse_affixes(curr_stem,'VERB:P',depth)
          res.extend(res_adj)
        elif curr_pos=='ADV':
          # ADVP -> VP
          res_adv = self.collapse_affixes(curr_stem,'VERB:P',depth)
          res.extend(res_adv)
        completes.extend(res)
        #####
        # Check if it's already a closed word
        for _pos,cw_list in self.closed_words.items():
          if curr_stem in cw_list:
            _pos = 'NOUN' if _pos=='clit' else _pos
            if len(prev_incompletes)>0:
              for i,a in enumerate(prev_incompletes):
                completes.append( [(curr_stem,_pos)] + prev_incompletes[i] )
            else:
              completes.append( [(curr_stem,_pos)] )
        #####
        ## Search for POS changing suffixes
        found_sub_complete = False
        new_incomp = []
        na = 0
        for af,code in codes:
          prev_pos = curr_pos
          inc,com = [],[]
          na = len(af)
          res = []
          # check if affix is derivational
          # if so, call this function on 'underived' previous stem
          ## NOUNS
          if curr_pos=='NOUN':
            # VP -> NP
            if af=='ti' and code=='NMLZ':
              res = self.collapse_affixes(curr_stem[:-na],'VERB:P',depth+1)
            elif af in ['a','ai']:
              res = self.collapse_affixes(curr_stem[:-na],'VERB:P',depth+1)
          ## VERBS
          elif curr_pos=='VERB':
            # NP -> VP
            if af=='n' and code=='CAUS':
              res = self.collapse_affixes(curr_stem[:-na],'NOUN:P',depth+1)
          # ADJ
          elif curr_pos=='ADJ':
            # NP -> ADJP
            if af in ['ya','oma','nto']:
              res = self.collapse_affixes(curr_stem[:-na],'NOUN:P',depth+1)
            # VP -> ADJP
            elif af in ['a','ai']:
              res = self.collapse_affixes(curr_stem[:-na],'VERB:P',depth+1)
          #END-IF
          # if any derivation is valid, add it to set of completes
          if len(res)!=0:
            completes.extend(res)
          # otherwise, add it to set of incompletes
          else:
            if len(prev_incompletes)==0:
              new_incomp.append([(af,code)])
            else:
              for inc in prev_incompletes:
                new_incomp.append([(af,code)] + inc)
        #END-FOR-CODES

        prev_incompletes = new_incomp
        new_incomp = []
        # discard suffix already analized
        curr_stem = curr_stem[:-na]
        # stop criteria: empty stem or empty list of new candidates
        if len(curr_stem)==0:
          break
        if len(prev_incompletes) == 0:
          break
        # augment depth for next iteration
        depth += 1
      #END-WHILE
      completes.extend( prev_incompletes )
    #END-IF
    ######
    # Filter candidates
    filtered = []
    closed_cat = []
    for com in completes:
      # filter out character unigram stems
      if len(com[0][0])<=1:
        continue
      # filter out AUX verbs not starting with 'ak' or 'ik' (mandatory)
      if com[0][1]=='AUX' and any([com[0][0].find('ak')!=0, com[0][0].find('ik')!=0]):
        continue
      # filter out those not in Open POS tag list
      if com[0][1] not in self.open_tags:
        continue
      filtered.append(com)
      # save closed-class stems separetely
      if len(com)==1 and com[0][1] in self.closed_tags and com[0][0]==wform:
        closed_cat.append(com)
    # if closed-class stems == word_form, discard all segmentation
    if len(closed_cat)!=0:
      filtered=[]

    # keep only unique derivations
    if len(filtered)>0:
      nf = len(filtered)
      temp = [filtered[0]]
      for j in range(1,nf):
        found = False
        for tt in temp:
          if filtered[j]==tt:
            found = True
            break
        if not found:
          temp.append(filtered[j])
      filtered = temp

    return filtered

############################################################

  def oracle_collapse_affixes(self,wtype,wform,init_pos,depth=0):
    '''
    @param wtype   : WordType object
    @param wform   : word form to segment
    @param init_pos: POS tag of wform (* : not defined)
    @param depth   : how many suffixes were extracted before
    return
      A list of candidate segmentations, each one in the format
        (lemma,POS),(suf_1,code_1), ..., (suf_n,code_n)
      where code_i is the morpho-syntactic code of suf_1, 'n' is the number of
      suffixes that were segmented.
      This function is used for words with morphological annotation, stored
      in the WordType object.
      WordType contains:
        - lemma
        - pos_tag
        - word_form
        - list of pairs (affix,and morpho-syntactic code)
      This function is always called with an specific POS tag, since the true initial tag
      is known from the annotation
    '''
    # if word form is in dictionary,
    # discard if initial POS tag is not among those in the entry in the dictionary
    if wform in self.dict_lemmas and init_pos not in self.dict_lemmas[wform]:
      return []
    prev_incompletes = []
    completes = []

    curr_stem = wform
    ## convention: NOUN:P -> NP
    curr_pos = init_pos if ':' not in init_pos else init_pos[:-2]
    curr_pos = 'NOUN' if curr_pos=='PROPN' else curr_pos
    naffs = len(wtype.affixes)
    
    # main loop
    while True:
      idx = naffs-depth-1
      # All suffixes were already explored (end of sequence)
      if depth == naffs:
        # check if stem is closed class word
        found = False
        for _pos,cw_list in self.closed_words.items():
          if curr_stem in cw_list:
            _pos = 'NOUN' if _pos=='clit' else _pos
            for i,a in enumerate(prev_incompletes):
              prev_incompletes[i] = [(curr_stem,_pos)] + prev_incompletes[i]
            found = True
            break
        # stem is not a closed-class word, output candidate with current stem
        # and previously gathered affixes
        if not found:
          curr_pos = "NOUN" if curr_pos=='clit' else curr_pos
          for i,a in enumerate(prev_incompletes):
            prev_incompletes[i] = [(curr_stem,curr_pos)] + prev_incompletes[i]
        break
      #####
      # Zero-morph derivations
      res = []
      if curr_pos=='NOUN':
        # NP -> VP
        if curr_stem in ['keen','shiwan']: # known cases of zero-morph derivation
          res = self.oracle_collapse_affixes(wtype,curr_stem,'VERB:P',depth)
        # NP -> ADVP
        res_adv = self.oracle_collapse_affixes(wtype,curr_stem,'ADV:P',depth)
        res.extend(res_adv)
      elif curr_pos=='ADJ':
        # ADJP -> VP
        res_adj = self.oracle_collapse_affixes(wtype,curr_stem,'VERB:P',depth)
        res.extend(res_adj)
      elif curr_pos=='ADV':
        # ADVP -> VP
        res_adv = self.oracle_collapse_affixes(wtype,curr_stem,'VERB:P',depth)
        res.extend(res_adv)
      completes.extend(res)
      #####
      # Check if it's already a closed word
      for _pos,cw_list in self.closed_words.items():
        if curr_stem in cw_list:
          _pos = 'NOUN' if _pos=='clit' else _pos
          if len(prev_incompletes)>0:
            for i,a in enumerate(prev_incompletes):
              completes.append( [(curr_stem,_pos)] + prev_incompletes[i] )
          else:
            completes.append( [(curr_stem,_pos)] )
      #####
      # Check if current (affix,code) -known from annotation- is valid
      # for current POS-tag dict or for clitics dict
      found_sub_complete = False
      new_incomp = []
      na = 0
      af,code = wtype.affixes[idx]
      if curr_pos in self.affix_dict and any([af in self.affix_dict[curr_pos],
              "clit" in wtype.orig_code[idx] and af in self.affix_dict['clit']]):
        na = len(af)
        ## Check if affix is derivational
        res = []
        if curr_pos=='NOUN':
          # VP -> NP
          if af=='ti' and code=='NMLZ':
            res = self.oracle_collapse_affixes(wtype,curr_stem[:-na],'VERB:P',depth+1)
          elif af in ['a','ai']:
            res = self.oracle_collapse_affixes(wtype,curr_stem[:-na],'VERB:P',depth+1)
        elif curr_pos=='VERB':
          # NP -> VP
          if af=='n' and code=='CAUS':
            res = self.oracle_collapse_affixes(wtype,curr_stem[:-na],'NOUN:P',depth+1)
        elif curr_pos=='ADJ':
          # NP -> ADJP
          if af in ['ya','oma','nto']:
            res = self.oracle_collapse_affixes(wtype,curr_stem[:-na],'NOUN:P',depth+1)
          # VP -> ADJP
          elif af in ['a','ai']:
            res = self.oracle_collapse_affixes(wtype,curr_stem[:-na],'VERB:P',depth+1)
        #END-IF
        # if any derivation is valid, add it to set of completes
        if len(res)!=0:
          completes.extend(res)
        # otherwise, add it to set of incompletes
        else:
          if len(prev_incompletes)!=0:
            for inc in prev_incompletes:
              new_incomp.append([(af,code)] + inc)
          else:
            new_incomp.append([(af,code)])
      ##END-IF-IN

      prev_incompletes = new_incomp
      new_incomp = []
      curr_stem = curr_stem[:-na]
      # stop criteria: empty stem or empty list of new candidates
      if len(curr_stem)==0:
        break
      if len(prev_incompletes) == 0:
        break
      depth += 1
    #END-WHILE
    completes.extend( prev_incompletes )
    #####
    # Filter candidates
    filtered = []
    closed_cat = []
    for com in completes:
      # filter out character unigram stems
      if len(com[0][0])<=1:
        continue
      # filter out AUX verbs not starting with 'ak' or 'ik' (mandatory)
      if com[0][1]=='AUX' and any([com[0][0].find('ak')!=0, com[0][0].find('ik')!=0]):
        continue
       # filter out those not in Open POS tag list
      if com[0][1] not in self.open_tags:
        continue
      filtered.append(com)
      # save closed-class stems separetely
      if len(com)==1 and com[0][1] in self.closed_tags and com[0][0]==wform:
        closed_cat.append(com)
    # if closed-class stems == word_form, discard all segmentation
    if len(closed_cat)!=0:
      filtered=[]

    # keep only unique derivations
    if len(filtered)>0:
      nf = len(filtered)
      temp = [filtered[0]]
      for j in range(1,nf):
        found = False
        for tt in temp:
          if filtered[j]==tt:
            found = True
            break
        if not found:
          temp.append(filtered[j])
      filtered = temp

    return filtered
