def children(heads):
    children = [[] for _ in heads]
    for child, parent in enumerate(heads):
        if parent is not None:
            children[parent].append(child)
    return children

def prefix(children, root=0):
    yield root
    for node in children[root]:
        for x in prefix(children, node):
            yield x

def depths(heads, _children=None):
    depths = [-1 for _ in heads]
    if _children is None: _children = children(heads)
    for root in (c for c, h in enumerate(heads) if h is None):
        for child in prefix(_children, root):
            if heads[child] is not None:
                depths[child] = depths[heads[child]] + 1

    comp = [i if h is None else h for i,h in enumerate(heads)]
    def find(x):
        if comp[x] == x:
            return x
        comp[x] = find(comp[x])
        return comp[x]
    for c in range(len(heads)): find(c)

    last = [None for _ in comp]
    for c,h in enumerate(comp):
        last[h] = c

    add_depth = [0 for _ in comp]
    current = []
    last_seen = [None for _ in comp]
    for c,h in enumerate(comp):
        if last_seen[h] is None:
            if current:
                higher = last_seen[current[-1]]
                while not (higher > c or _children[higher] and max(_children[higher]) > c):
                    higher = heads[higher]
                add_depth[h] = depths[higher] + 2
            current.append(h)
        if last[h] == c:
            current.pop(-1)
        last_seen[h] = c
        depths[c] += add_depth[h]

    return depths

def postfix(children, root=0):
    for node in children[root]:
        for x in postfix(children, node):
            yield x
    yield root

def spans(heads, _children=None):
    farleft = [c for c, _ in enumerate(heads)]
    farright = [c for c, _ in enumerate(heads)]
    if _children is None: _children = children(heads)
    for root in (c for c, h in enumerate(heads) if h is None):
        for head in postfix(_children, root):
            if _children[head]:
                farleft[head] = min(head, min(farleft[c] for c in _children[head]))
                farright[head] = max(head, max(farright[c] for c in _children[head]))
    return farleft, farright

def infix(children, root=0):
    yield "__OPEN__"
    for node in children[root]:
        if node < root:
            for x in infix(children, node):
                yield x
    yield root
    for node in children[root]:
        if node > root:
            for x in infix(children, node):
                yield x
    yield "__CLOSE__"

def check_projectivity(heads):
    """Check whether a dependency tree is projective or not.

    This methods implements the test described in [Gomez-Ródríguez and
    Nivre, 2010].

    [Gomez-Ródríguez and Nivre, 2010] A Transition-Based Parser for
    2-Planar Dependency Structures, ACL'10
    """
    # ROOT token supposed at the end

    # removes START symbol
    edges = [(j, i) for i, j in enumerate(heads)][1:]
    import itertools
    for (i, k), (j, l) in itertools.product(edges, repeat=2):
        if i is None or j is None:
            continue

        # non-projectivity condition for partial trees: checks non-cyclicity
        if (j == k and (j > i > l or j < i < l)) or (i == l and (i > j > k or i < j < k)):
            return False

        # canonical non-projectivity condition
        if min(i, k) < min(j, l) < max(i, k) < max(j, l):
            return False

    return True
