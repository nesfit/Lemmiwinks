import logging
import abc


class CSSParser(metaclass=abc.ABCMeta):
    def __init__(self, parser, logger_name):
        self._logger = logging.getLogger(logger_name)
        self._parser = parser
        self._url_token_list = list()
        self._import_token_list = list()

    @abc.abstractmethod
    def parse_tokens(self):
        pass

    @property
    def url_tokens(self):
        return self._url_token_list

    @property
    def import_tokens(self):
        return self._import_token_list


class HTMLParser(metaclass=abc.ABCMeta):
    def __init__(self, logger_name):
        self._logger = logging.getLogger(logger_name)
        self._elements = list()

    @abc.abstractmethod
    def find_elements(self, tag, attribute):
        pass

    @abc.abstractmethod
    def get_elements(self):
        pass
