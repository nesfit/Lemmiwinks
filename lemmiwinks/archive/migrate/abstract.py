import abc
import pathlib
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
    def __init__(self, downloader, path_gen, src_register):
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._downloader = downloader
        self._path_gen = path_gen
        self._src_register = src_register

    async def update_entity(self, entity, **kwargs):
        try:
            url = self._get_url_from(entity, **kwargs)
            if url not in self._src_register.keys():
                await self.__migrate_source(url)
            self._update_entity(url, entity, **kwargs)
        except Exception as e:
            self._logger.error(e)
            self._logger.error(f"entity: {entity}")
            self._logger.error(f"entity attributes: {kwargs}")

    @abc.abstractmethod
    def _get_url_from(self, entity, **kwargs):
        raise NotImplemented

    async def __migrate_source(self, url):
        url_path = urllib.parse.urlparse(url).path
        path = self._path_gen.generate_filepath_with(pathlib.Path(url_path).suffix)
        self._src_register.update({url: path})
        await self._downloader.download(url, path.abspath)

    @abc.abstractmethod
    def _update_entity(self, url, entity, **kwargs):
        raise NotImplemented


class UpdateRecursiveEntity(metaclass=abc.ABCMeta):
    def __init__(self, client, path_gen, src_register):
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._path_gen = path_gen
        self._src_register = src_register
        self._client = client

    @_task
    async def _update_recursive_entity(self, entity, **kwargs):
        try:
            url = self._get_url_from(entity, **kwargs)

            if url not in self._src_register.keys():
                await self.__migrate_entity(url)

            self._update_entity(url, entity, **kwargs)
        except Exception as e:
            self._logger.error(e)
            self._logger.error(f"entity: {entity}")
            self._logger.error(f"entity attributes: {kwargs}")

    @abc.abstractmethod
    def _get_url_from(self, entity, **kwargs):
        raise NotImplemented

    async def __migrate_entity(self, url):
        self._register_path_for(url)
        response = await self._client.get_request(url)
        await self._process_response(response)

    @abc.abstractmethod
    async def _process_response(self, response):
        raise NotImplemented

    def _register_path_for(self, url):
        url_path = urllib.parse.urlparse(url).path
        path = self._path_gen.generate_filepath_with(pathlib.Path(url_path).suffix)
        self._src_register.update({url: path})

    @abc.abstractmethod
    def _update_entity(self, path, entity, **kwargs):
        raise NotImplemented


class EssentialPart(metaclass=abc.ABCMeta):
    def __init__(self, parser, url, dir_dst, suffix_path, settings, recursion_limit):
        self._parser = parser
        self._parser.parse_tokens()
        self._resolver = settings.resolver(url)
        self._path_gen = settings.path_gen(dir_dst, suffix_path)
        self._recursion_limit = recursion_limit

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
