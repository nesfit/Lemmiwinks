import logging
import asyncio
import asyncio_extras

# third party imports
import dependency_injector.providers as providers
import dependency_injector.containers as containers
from selenium.webdriver import DesiredCapabilities

# local imports
from . import client
from . import exception
from .container import InstanceStatus
import lemmiwinks.singleton as singleton


class ClientFactory:
    def __init__(self, cls, **kwargs):
        self.__cls = cls
        self.__kwargs = kwargs

    @property
    def client(self):
        return providers.Factory(self.__cls, **self.__kwargs)

    @property
    def singleton_client(self):
        return providers.ThreadSafeSingleton(self.__cls, **self.__kwargs)


class ClientFactoryProvider(containers.DeclarativeContainer):
    aio_factory = ClientFactory(client.AIOClient)

    selenium_factory = ClientFactory(client.SeleniumClient)

    phantomjs_factory = ClientFactory(client.SeleniumClient,
                                      browser_info=DesiredCapabilities.PHANTOMJS)

    firefox_factory = ClientFactory(client.SeleniumClient,
                                    browser_info=DesiredCapabilities.FIREFOX)

    chrome_factory = ClientFactory(client.SeleniumClient,
                                   browser_info=DesiredCapabilities.CHROME)


class HTTPClientDownloader:
    def __init__(self, http_client: object):
        self._logger = logging.getLogger(f"{__name__}{__class__.__name__}")
        self.__http_client = http_client

    async def download(self, url: str, dst: str) -> None:
        try:
            response = await self.__http_client.get_request(url)
            self.__save_response_content_to(response, dst)
        except Exception as e:
            self._logger.error(f"error: {e}")
            self._logger.error(f"url: {url}")
            self._logger.error(f"dst: {dst}")

    @staticmethod
    def __save_response_content_to(response, destination):
        with open(destination, "wb") as fd:
            fd.write(response.content_descriptor.read())


class HTTPClientDownloadProvider:
    @staticmethod
    def aio_downloader():
        http_client = ClientFactoryProvider.aio_factory.client()
        return HTTPClientDownloader(http_client)


class ClientPool(metaclass=singleton.ThreadSafeSingleton):
    def __init__(self, factory, max_pool=10, **kwargs):
        self.__logger = logging.getLogger(__name__+"."+__class__.__name__)
        self._max_pool = max_pool
        self._assign_dict = dict()

        self._factory = factory
        self._kwargs = kwargs

        self._lock = asyncio.Lock()
        self._semaphore = asyncio.Semaphore(max_pool)

    def __del__(self):
        for key in self._assign_dict:
            del key

    @asyncio_extras.async_contextmanager
    async def get_client(self):
        try:
            http_client = await self.acquire()
            yield http_client
        finally:
            self.release(http_client)

    async def acquire(self):
        await self._semaphore.acquire()
        with await self._lock:
            instance = self.__acquire_instance()

        return instance

    def __acquire_instance(self):
        if self.__is_instance_awaliable():
            instance = self.__get_awaliable_instance()
            self.__update_instance_state_to(instance, InstanceStatus.RESERVED)
        else:
            instance = self._factory.client(**self._kwargs)
            self.__update_instance_state_to(instance, InstanceStatus.RESERVED)

        return instance

    def __is_instance_awaliable(self):
        return InstanceStatus.AWALIABLE in self._assign_dict.values()

    def __get_awaliable_instance(self):
        try:
            instance = (inst for inst, status in self._assign_dict.items()
                        if status is InstanceStatus.AWALIABLE).__next__()
        except Exception as e:
            self.__logger.critical(e)
            raise exception.PoolError(e)
        else:
            return instance

    def __update_instance_state_to(self, instance, state: InstanceStatus):
        self._assign_dict.update({instance: state})

    def release(self, instance):
        self.__update_instance_state_to(instance, InstanceStatus.AWALIABLE)
        self._semaphore.release()
