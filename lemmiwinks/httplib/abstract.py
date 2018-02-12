import abc
import logging
from . import container


class AsyncClient(metaclass=abc.ABCMeta):
    def __init__(self, logger_name: str):
        self._logger = logging.getLogger(logger_name)
        self._cookies = None
        self._headers = None
        self._proxy = None
        self._timeout = None

    @property
    def cookies(self):
        return self._cookies

    @cookies.setter
    def cookies(self, cookies):
        self._cookies = cookies

    @property
    def headers(self):
        return self._headers

    @headers.setter
    def headers(self, headers):
        self._headers = headers

    @property
    def timeout(self):
        return self._timeout

    @timeout.setter
    def timeout(self, timeout):
        self._timeout = timeout

    @property
    def proxy(self):
        return self._proxy

    @proxy.setter
    @abc.abstractmethod
    def proxy(self, proxy: container.Proxy):
        pass

    @abc.abstractmethod
    async def get_request(self, url) -> container.Response:
        pass

    @abc.abstractmethod
    async def post_request(self, url, data):
        pass


class AsyncJsClient(metaclass=abc.ABCMeta):

    def __init__(self, logger_name: str):
        self._logger = logging.getLogger(logger_name)
        self._cookies = None
        self._timeout = None

    @property
    def timeout(self):
        return self._timeout

    @timeout.setter
    def timeout(self, timeout):
        self._timeout = timeout

    @property
    def cookies(self):
        return self._cookies

    @cookies.setter
    @abc.abstractmethod
    def cookies(self, cookies):
        pass

    @abc.abstractmethod
    async def get_request(self, url):
        pass

    @abc.abstractmethod
    async def save_screenshot_to(self, filepath):
        pass
