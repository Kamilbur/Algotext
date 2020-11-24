from collections import defaultdict


class State:
    EPSILON = ''

    def __init__(self):
        self.trans = defaultdict(lambda: list())
        self.idx = None

    def __setitem__(self, key, value):
        self.trans[key] += [value]

    def __getitem__(self, item):
        return self.trans[item]

    def __contains__(self, item):
        return item in self.trans

    def get(self, key, default):
        return self.trans[key] if (key in self.trans) else default

    def keys(self):
        return self.trans.keys()

    def values(self):
        return self.trans.values()
