class Listener:
    @staticmethod
    def iter(what):
        return what
    @staticmethod
    def msg(what, crop=None):
        if type(what) == str and crop is not None:
            what = what[:crop]
        print(what)
    @classmethod
    def msgs(cls, what, crop=None):
        if type(what)==str:
            cls.msg(l, crop)
        else:
            for l in what: cls.msg(l, crop)

class FrogressListener(Listener):
    @staticmethod
    def iter(what):
        import frogress
        return frogress.bar(what)

class SilentListener(Listener):
    @staticmethod
    def msg(what):
        pass

def read_tabular_file(filehandler, header, max_sent, count_lines=False):
    """
    Read `max_sent` sentences from a tabular file.

    Generates, for each example:
    - the position of the token in the sentence
    - the tokenized sentence
    - the features associated to each token
    - the gold heads
    - the labels of the dependency tree
    """
    cur_obser = []
    count_sent = 0
    n_lines = 1
    for n,line in enumerate(filehandler):
        line = line.strip().split('\t')

        if len(line)<len(header):
            if len(cur_obser) != 0:
                yield (n_lines,cur_obser) if count_lines else cur_obser
                cur_obser = []
                count_sent += 1
                n_lines = n + 2

                if max_sent is not None and count_sent >= max_sent:
                    return

            continue

        while len(line)>len(header):
            line[1] += line.pop(2)

        cur_obser.append(dict(zip(header, line)))

    if len(cur_obser) != 0:
        yield (n_lines,cur_obser) if count_lines else cur_obser
