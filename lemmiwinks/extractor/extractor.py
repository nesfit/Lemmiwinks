import re

import lemmiwinks.parslib as parslib

from . import abstract


class RegexExtractor(abstract.BaseExtractor):
    def __init__(self, pattern, pattern_name, document):
        self.__document = document
        self.__pattern = pattern
        self.__pattern_name = pattern_name

    def __del__(self):
        self.__document.seek(0)

    def extract(self):
        parser = parslib.HTMLParserProvider.bs_parser(self.__document)
        matches = re.findall(self.__pattern, parser.text)
        return self.__pattern_name, matches
