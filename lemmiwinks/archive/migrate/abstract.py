import abc
import pathlib
import httplib
import logging
import urllib.parse
import asyncio


def _task(func):
    def wrapper(*args, **kwargs):
        task = asyncio.get_event_loop().create_task(func(*args, **kwargs))
        return task
    return wrapper


class Migrate(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    async def migrate(self):
        raise NotImplemented


class UpdateEntity(metaclass=abc.ABCMeta):
    def __init__(self, client, path_gen, src_register):
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._client = client
        self._downloader = httplib.provider.HTTPClientDownloader(client)
        self._path_gen = path_gen
        self._src_register = src_register

    @_task
    async def update_recursive_entity(self, handler, entity, **kwargs):
        await self.__update_entity_with_handler(handler, entity, **kwargs)

    @_task
    async def update_entity(self, entity, **kwargs):
        await self.__update_entity_with_handler(self.__migrate_source, entity, **kwargs)

    async def __update_entity_with_handler(self, handler, entity, **kwargs):
        try:
            url = self._get_url_from(entity, **kwargs)
            if url not in self._src_register.keys():
                await handler(url)
            self._update_entity(url, entity, **kwargs)
        except Exception as e:
            self._logger.exception(e)
            self._logger.error(e)
            self._logger.error(f"entity: {entity}")
            self._logger.error(f"entity attributes: {kwargs}")

    @abc.abstractmethod
    def _get_url_from(self, entity, **kwargs):
        raise NotImplemented

    async def __migrate_source(self, url):
        self.register_path_for(url)
        path = self._src_register.get(url).abspath
        await self._downloader.download(url, path)

    def register_path_for(self, url):
        url_path = urllib.parse.urlparse(url).path
        path = self._path_gen.generate_filepath_with(pathlib.Path(url_path).suffix)
        self._src_register.update({url: path})

    @abc.abstractmethod
    def _update_entity(self, url, entity, **kwargs):
        raise NotImplemented


class EssentialPart(metaclass=abc.ABCMeta):
    def __init__(self, parser, resolver, path_gen, essential_location,
                 res_location, recursion_limit):
        self._parser = parser
        self._resolver = resolver
        self._path_gen = path_gen
        self._recursion_limit = recursion_limit
        self._res_location = res_location
        self._essential_location = essential_location

    @property
    def parser(self):
        return self._parser

    @property
    def path_gen(self):
        return self._path_gen

    @property
    def resolver(self):
        return self._resolver

    @property
    def recursion_limit(self):
        return self._recursion_limit

    @property
    def resource_location(self):
        return self._res_location

    @property
    def essential_location(self):
        return self._essential_location

    @abc.abstractmethod
    def export(self):
        raise NotImplemented


class MigrationSettings(metaclass=abc.ABCMeta):
    @property
    def html_parser(self):
        raise NotImplemented

    @property
    def css_parser(self):
        raise NotImplemented

    @property
    def path_gen(self):
        raise NotImplemented

    @property
    def http_client(self):
        raise NotImplemented

    @property
    def http_js_pool(self):
        raise NotImplemented

    @property
    def resolver(self):
        raise NotImplemented
