#!/usr/bin/env python3.6
# standard library imports
import ast
import sys
import asyncio
import tempfile
import pathlib
import socket
from socket import AF_INET, AF_INET6
from urllib.parse import urlsplit
from distutils.dir_util import copy_tree
from datetime import datetime
import logging
# third party imports
import jinja2

# lemmiwinks imports
import lemmiwinks
from lemmiwinks import httplib
from lemmiwinks import parslib
from lemmiwinks import pathgen
from lemmiwinks import archive
from lemmiwinks import extractor
from lemmiwinks.archive import migration

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M')

BASE_LOCATION = '/Lemmiwinks/pharty2'


class WebPageScreenshotLetter(archive.abstract.BaseLetter):
    def __init__(self, tmp_file):
        self.__tmp_file = tmp_file
        self.__tmp_file.seek(0)

    async def write_to(self, location):
        index_path = str(pathlib.Path(location).joinpath("index.png"))
        with open(index_path, "wb") as fd:
            fd.write(self.__tmp_file.read())


class InfoTabLetter(archive.abstract.BaseLetter):
    def __init__(self, info):
        self.__template_loc = str(pathlib.Path(BASE_LOCATION).joinpath('tab_template'))
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(self.__template_loc))
        self.__template = env.get_template('index.html')
        self.__info = info

    async def write_to(self, location):
        index_path = str(pathlib.Path(location).joinpath("index.html"))
        rendered_template = self.__template.render(info=self.__info)

        copy_tree(self.__template_loc, location)

        with open(index_path, "w") as fd:
            fd.write(rendered_template)


class ArchiveSettings(migration.MigrationSettings):
    http_client = httplib.provider.ClientFactoryProvider.aio_factory.singleton_client
    css_parser = parslib.provider.CSSParserProvider.tinycss_parser
    html_parser = parslib.provider.HTMLParserProvider.bs_parser
    resolver = httplib.resolver.URLResolver
    path_gen = pathgen.FilePathProvider.filepath_generator
    http_js_pool = httplib.ClientPool


class AIOPharty(lemmiwinks.Lemmiwinks):
    def __init__(self, url, dst, regex, executor_url):
        self.__settings = ArchiveSettings()

        # JS Pool has to be initialized
        self.__pool = self.__settings.http_js_pool(
            factory=httplib.ClientFactoryProvider.firefox_factory,
            executor_url=executor_url,
        )

        # aio client has to be initialized
        self.__client = self.__settings.http_client(
            pool_limit=50,
            timeout=10,
        )

        self.__envelop = archive.Envelop()

        self.__url = url
        self.__dst = dst
        self.__regex = regex
        self.__info = dict()

        self.__browser = None

    @property
    def meta_info(self):
        return self.__info

    async def task_executor(self):
        await self.__create_envelop()
        await archive.Archive.archive_as_maff(self.__envelop, self.__dst)

    async def __create_envelop(self):
        self.__browser = await self.__pool.acquire()
        web_content_response = await self.__browser.get_request(self.__url)

        tasks = [
            self.__add_web_page_to_envelop(web_content_response),
            self.__add_screenshot_to_envelop(),
            self.__add_info_tab_to_envelop(web_content_response)
        ]

        await asyncio.gather(*tasks)

    async def __add_web_page_to_envelop(self, web_content_response):
        letter = archive.SaveResponseLetter(
            response=web_content_response,
            settings=self.__settings,
            mode=archive.Mode.FULL_JS_EXECUTION)
        self.__envelop.append(letter)

    async def __add_screenshot_to_envelop(self):
        tmp_file = await self.__save_screenshot_to_tmp_file()
        letter = WebPageScreenshotLetter(tmp_file)
        self.__envelop.append(letter)
        self.__pool.release(self.__browser)

    async def __save_screenshot_to_tmp_file(self):
        tmp_file = tempfile.NamedTemporaryFile()
        await self.__browser.save_screenshot_to(tmp_file.name)
        return tmp_file

    async def __add_info_tab_to_envelop(self, web_content_response):
        self.__extract_info(web_content_response)
        self.__ip_addr_info()
        self.__timestamp_info()
        letter = InfoTabLetter(self.__info)
        self.__envelop.append(letter)

    def __extract_info(self, web_content_response):
        for regex_name, pattern in self.__regex.items():
            reg_extractor = extractor.RegexExtractor(
                pattern=pattern,
                pattern_name=regex_name,
                document=web_content_response.content_descriptor
            )
            _, matches = reg_extractor.extract()
            self.__info.update({regex_name: matches})

    def __ip_addr_info(self):
        url_parser = urlsplit(self.__url)
        hostname = url_parser.hostname
        port = url_parser.port or url_parser.scheme

        net_info = socket.getaddrinfo(hostname, port)
        ip_addr = [f"{addr_info[4][0]} | {addr_info[4][1]}" for addr_info in net_info
                   if addr_info[0] == AF_INET6 or addr_info[0] == AF_INET]

        self.__info.update({"IP ADDRESS": ip_addr})

    def __timestamp_info(self):
        self.__info.update({"Timestamp": [str(datetime.now())]})


class CMDInput:
    def __init__(self):
        cmd_request = ast.literal_eval(sys.argv[1])
        self.__url_dict = cmd_request['url']
        self.__regex_dict = cmd_request["regex"]

    @property
    def url(self):
        url = next(iter(self.__url_dict.keys()))
        return url

    @property
    def location(self):
        location = next(iter(self.__url_dict.values()))
        return location

    @property
    def regex_list(self):
        return self.__regex_dict


def main():
    cmd = CMDInput()
    aio_pharty = AIOPharty(cmd.url, cmd.location, cmd.regex_list, "http://firefox:4444/wd/hub")
    aio_pharty.run()
    print(aio_pharty.meta_info)


if __name__ == "__main__":
    main()
