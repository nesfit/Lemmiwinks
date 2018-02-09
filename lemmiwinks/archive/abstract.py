import abc


class BaseLetter(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def write_to(self, location):
        raise NotImplemented
