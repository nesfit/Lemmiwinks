import abc


class BaseExtractor(metaclass=abc.ABCMeta):
    @abc.abstractclassmethod
    def extract(self):
        raise NotImplemented
