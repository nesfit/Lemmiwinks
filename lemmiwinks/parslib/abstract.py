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

    @abc.abstractmethod
    def export(self):
        pass


class HTMLParser(metaclass=abc.ABCMeta):
    def __init__(self, logger_name):
        self._logger = logging.getLogger(logger_name)

    @abc.abstractmethod
    def find_elements(self, tag, attribute):
        pass

    @property
    @abc.abstractmethod
    def title(self):
        pass

    @property
    @abc.abstractmethod
    def base(self):
        pass

    @base.deleter
    @abc.abstractmethod
    def base(self):
        pass

    @property
    @abc.abstractmethod
    def charset(self):
        pass

    @property
    @abc.abstractmethod
    def text(self):
        pass

    @abc.abstractmethod
    def export(self):
        pass


class Token(metaclass=abc.ABCMeta):
    def __init__(self, token):
        self._token = token

    @abc.abstractmethod
    def __str__(self):
        pass

    @property
    @abc.abstractmethod
    def value(self):
        pass

    @value.setter
    @abc.abstractmethod
    def value(self, value):
        pass


class Element(metaclass=abc.ABCMeta):
    def __init__(self, element):
        self._element = element

    @abc.abstractmethod
    def __str__(self):
        raise NotImplemented

    @abc.abstractclassmethod
    def __getitem__(self, item):
        raise NotImplemented

    @abc.abstractclassmethod
    def __setitem__(self, key, value):
        raise NotImplemented

    @property
    @abc.abstractmethod
    def name(self):
        raise NotImplemented

    @property
    @abc.abstractmethod
    def string(self):
        raise NotImplemented

    @string.setter
    @abc.abstractmethod
    def string(self, string):
        raise NotImplemented

    @property
    @abc.abstractmethod
    def attrs(self):
        raise NotImplemented
