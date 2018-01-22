import logging
import asyncio
import os

from typing import List, Dict
from urllib.parse import urlparse

# local imports
import http_client.exception as http_exception

from filepath_generator import FilePathGenerator
from parser.abstract import HTMLParser, CSSParser, Tag
from http_client.resolver import URLResolver
#from http_client.provider import HTTPClientDownloader


# type aliases
ElementFilter = Dict[str, List[str]]
Element_List = List[Tag]


class CSSMigrator:
    def __init__(self,
                 css_parser: CSSParser,
                 http_downloader,
                 filepath_gen: FilePathGenerator,
                 url_resolver: URLResolver,
                 element_filter: ElementFilter):
        self._logger


class InlineCss:
    def __init__(self, parser, http_client, destination, resolver):
        pass


class HTMLElements:
    def __init__(self,
                 html_parser: HTMLParser,
                 http_downloader,
                 filepath_gen: FilePathGenerator,
                 url_resolver: URLResolver,
                 element_filter: ElementFilter):

        self._logger = logging.getLogger(f"{__name__}.{__class__.__name__}")
        self._html_parser = html_parser
        self._http_downloader = http_downloader
        self._filepath_gen = filepath_gen
        self._url_resolver = url_resolver
        self._element_filter = self.__element_filter_to_list(element_filter)
        self._html_resources = dict()

    @staticmethod
    def __element_filter_to_list(element_filter):
        return [(name, attr) for name, attr_list in element_filter.items() for attr in attr_list]

    async def migrate_dependencies(self) -> None:
        tasks = list()
        for name, attr in self._element_filter:
            elements = self._html_parser.find_elements(name, {attr: True})
            migrations = self.__migrate_elements_attribute_resource(elements, attr)
            task = asyncio.get_event_loop().create_task(migrations)
            tasks.append(task)

        await asyncio.gather(*tasks)

    async def __migrate_elements_attribute_resource(self, element_list: List[Tag], attr_name: str):
        tasks = list()

        for element in element_list:
            migration = self.__migrate_one_element_attribute_resource(element, attr_name)
            task = asyncio.get_event_loop().create_task(migration)
            tasks.append(task)

        await asyncio.gather(*tasks)

    async def __migrate_one_element_attribute_resource(self, element: Tag, attribute: str):
        try:
            url = self._url_resolver.resolve(element.attrs[attribute])
            path = self._filepath_gen.generate_unique_filepath_from(urlparse(url).path)
            rel_path = self._filepath_gen.generate_relative_path_from(path)

            if url not in self._html_resources.keys():
                self._html_resources.update({url: rel_path})
                await self._http_downloader.dovnload(url, path)

            element.attrs[attribute] = self._html_resources.get(url)
        except http_exception.URLResolverError as e:
            self._logger.info(e)
        except Exception as e:
            self._logger.error(f"msg: {e}\nelement: {element}")
            self._html_resources.pop(url)
            # TODO: choose better exception


class JavaScriptInlineMigrator:
    def __init__(self, parser, http_client, destination, resolver):
        pass
