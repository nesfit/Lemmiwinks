import os.path
import mimetypes
from typing import Callable

# third party import
import magic

import parser.container
from http_client.provider import HTTPClientDownloader
import http_client.resolver as resolver
from . import migrate


class HTMLElementFilters:
    element_filter = {"img": ["src", "data-src"],
                      "video": ["src", "poster"],
                      "embed": ["src"],
                      "source": ["src"],
                      "audio": ["src"],
                      "input": ["src"],
                      "object": ["data", "codebase"],
                      "track": ["src"]}
    link_filter = {"link": ["href"]}
    js_filter = {"script": ["src"]}


class WebPageMigration:
    def __init__(self,
                 dst: str,
                 file: object,
                 url: str,
                 filepath_gen: Callable,
                 http_downloader: HTTPClientDownloader,
                 html_parser: Callable):
        self._index_path = self.__get_index_filepath(file.name, dst)
        self._index_files_path = os.path.join(dst, "index_files")
        self._html_parser = html_parser(file)
        self._http_downloader = http_downloader
        self._filepath_gen = filepath_gen(self._index_files_path, "index_files")
        self._resolver = resolver.URLResolver(url)

    @staticmethod
    def __get_index_filepath(filename, dst):
        mime = magic.from_file(filename, mime=True)
        ext = mimetypes.guess_extension(mime)
        return os.path.join(dst, f"index{ext}")

    async def migrate_html_elements(self):
        html_elements = migrate.HTMLElements(html_parser=self._html_parser,
                                             http_downloader=self._http_downloader,
                                             filepath_gen=self._filepath_gen,
                                             url_resolver=self._resolver,
                                             element_filter=HTMLElementFilters.element_filter)
        await html_elements.migrate_dependencies()

    async def migrate_css(self):
        html_elements = migrate.HTMLElements(html_parser=self._html_parser,
                                             http_downloader=self._http_downloader,
                                             filepath_gen=self._filepath_gen,
                                             url_resolver=self._resolver,
                                             element_filter=HTMLElementFilters.link_filter)
        await html_elements.migrate_dependencies()

    async def migrate_iframes(self):
        pass

    async def migrate_js(self):
        html_elements = migrate.HTMLElements(html_parser=self._html_parser,
                                             http_downloader=self._http_downloader,
                                             filepath_gen=self._filepath_gen,
                                             url_resolver=self._resolver,
                                             element_filter=HTMLElementFilters.js_filter)
        await html_elements.migrate_dependencies()

    def save_index(self):
        with open(self._index_path, "wb") as fd:
            fd.write(self._html_parser.export())
