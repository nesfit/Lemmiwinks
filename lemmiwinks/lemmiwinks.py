import abc
import asyncio
import enum


class AdvanceAIOClientSettings(abc.ABCMeta):
    @property
    def pool_limit(cls):
        raise NotImplemented

    @property
    def timeout(cls):
        raise NotImplemented

    @property
    def proxy(cls):
        raise NotImplemented

    @property
    def headers(cls):
        raise NotImplemented

    @property
    def cookies(cls):
        raise NotImplemented


class AdvanceJSClientPoolSettings(abc.ABCMeta):
    @property
    def workers(cls):
        raise NotImplemented

    @property
    def timeout(cls):
        raise NotImplemented

    @property
    def executor_url(cls):
        raise NotImplemented

    def factory(cls):
        raise NotImplemented


class LemmiwinksMode(enum.Enum):
    JS_MODE = enum.auto()
    NORMAL_MODE = enum.auto()


class Lemmiwinks:
    def __init__(self):
        self.__extractors = list()
        self.__urls = list()
        self.__settings = None

    @property
    def extractors(self):
        return self.__extractors

    @extractors.setter
    def extractors(self, extractors: list):
        self.extractors = extractors

    @property
    def urls(self):
        return self.__urls

    @urls.setter
    def urls(self, urls):
        self.__urls = urls

    @property
    def settings(self):
        return self.__settings

    @settings.setter
    def settings(self, settings):
        self.__settings = settings

    async def task_executor(self):
        raise NotImplemented

    async def run(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.task_executor())
