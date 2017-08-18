import re
import parsers

class Scraper:
    def __init__(self, reg_list):
        self.__reg_list = self.__compile_regex(reg_list)
        self.__match_list = list()

    def __compile_regex(self, reg_list):
        regex_list = list()

        for reg in reg_list:
            regex_list.append(re.compile(reg, re.IGNORECASE))

        return regex_list

    def search_file(self, text: str):
        for line in text.split():
            for word in line.split():
                for regex in self.__reg_list:
                    self.__match_list += regex.findall(word)

    def get_discovered(self):
        return self.__match_list
