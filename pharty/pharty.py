#!/usr/bin/env python3.6

import argparse
import asyncio
import lemmiwinks
import lemmiwinks.taskwrapper as taskwrapper
import lemmiwinks.archive.migration as migration
import lemmiwinks.httplib as httplib
import lemmiwinks.pathgen as pathgen
import lemmiwinks.parslib as parslib
import lemmiwinks.archive as archive
import logging
import enum

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M')


class ArchiveSettings(migration.MigrationSettings):
    http_client = httplib.provider.ClientFactoryProvider.aio_factory.singleton_client
    css_parser = parslib.provider.CSSParserProvider.tinycss_parser
    html_parser = parslib.provider.HTMLParserProvider.bs_parser
    resolver = httplib.resolver.URLResolver
    path_gen = pathgen.FilePathProvider.filepath_generator
    http_js_pool = httplib.ClientPool


class LemiMode(enum.Enum):
    JS = enum.auto()
    NORMAL = enum.auto()


class AIOLemmiwinks(lemmiwinks.Lemmiwinks):
    def __init__(self, url, archive_name, mode):

        if mode == LemiMode.JS:
            self.__pool = httplib.ClientPool(httplib.ClientFactoryProvider.firefox_factory,
                                             executor_url="http://liemmiNET:4444/wd/hub")

        self.__client = httplib.ClientFactoryProvider.aio_factory.singleton_client(pool_limit=500,
                                                                                   timeout=10)

        self.__settings = ArchiveSettings()
        self.__envelop = archive.Envelop()
        self.__archive_name = archive_name
        self.__url = url
        self.__mode = mode

    async def task_executor(self):
        task = self.__archive_task(self.__url, self.__archive_name)
        await asyncio.gather(task)

    @taskwrapper.task
    async def __archive_task(self, url, archive_name):
        response = await self.__get_request(url)
        await self.__archive_response(response, archive_name)

    async def __get_request(self, url):
        if self.__mode == LemiMode.NORMAL:
            response = await self.__client.get_request(url)
        else:
            async with self.__pool.get_client() as client:
                response = await client.get_request(url)

        return response

    async def __archive_response(self, response, archive_name):
        self.__add_save_response_to_envelop(response)
        await archive.Archive.archive_as_maff(self.__envelop, archive_name)

    def __add_save_response_to_envelop(self, response):
        if self.__mode == LemiMode.JS:
            letter = archive.SaveResponseLetter(
                response, self.__settings, archive.Mode.FULL_JS_EXECUTION)
        else:
            letter = archive.SaveResponseLetter(
                response, self.__settings, archive.Mode.NO_JS_EXECUTION)
        self.__envelop.append(letter)


def main():
    mode = LemiMode.NORMAL

    command_line = argparse.ArgumentParser(
        prog='phart',
        description='This script downloads web page by specified URL and '
                    'store it as a .mff (mozilla file format) format.')

    command_line.add_argument(
        '-u', '--url', help='specify URL of site to archive', required=True)
    command_line.add_argument(
        '-o', '--output', help="name of MAFF archive", required=True)
    command_line.add_argument("-j", help="turn on js mode", action="store_true")
    args = command_line.parse_args()

    if args.j:
        mode = LemiMode.JS

    aio_archive = AIOLemmiwinks(args.url, args.output, mode)
    aio_archive.run()


if __name__ == "__main__":
    main()
