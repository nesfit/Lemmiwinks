import parser

class RegexExtractorRule:
    def __init__(self, rule):
        self.__rule = rule

    def __getattr__(self, item):
        return getattr(self.__rule, item)


class Extractor:
    def __init__(self, rules):
        self.__rules = rules
