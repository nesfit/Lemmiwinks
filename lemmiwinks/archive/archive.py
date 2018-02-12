import logging
import pathlib
import enum

import magic

from . import maff
from . import abstract
from . import migration
from . import rdfinfo


class _HTMLResponseLetter(abstract.BaseLetter):
    def __init__(self, response, settings, index_migration):
        self.__logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.__settings = settings
        self.__response = response

        self.__index_file = None
        self.__index_migration = index_migration

        self.__archive_time = rdfinfo.TimeMaffRDFInfo()
        self.__file_info = rdfinfo.ResponseMaffRDFInfo(response)

    async def write_to(self, location):
        self.__create_index_files_dir_in(location)
        await self.__save_response_to(location)
        self.__create_rdf_to(location)

    @staticmethod
    def __create_index_files_dir_in(location):
        dir_path = pathlib.Path(location).joinpath("index_files")
        dir_path.mkdir(parents=True, exist_ok=True)

    async def __save_response_to(self, location):
        try:
            await self.__save_index_htm_to(location)
        except Exception as e:
            self.__logger.exception(e)

    async def __save_index_htm_to(self, location):
        index_name = self.__file_info.index_name
        filepath = str(pathlib.Path(location).joinpath(index_name))
        res_location = str(pathlib.Path(location).joinpath("index_files"))

        self.__index_file = self.__index_migration(
            self.__response, filepath, res_location, self.__settings)

        await self.__index_file.migrate_external_sources()

        self.__index_file.export()

    def __create_rdf_to(self, location):
        rdf_path = str(pathlib.Path(location).joinpath("index.rdf"))

        with maff.RDF(rdf_path) as rdf_file:
            self.__init_attributes_of(rdf_file)

    def __init_attributes_of(self, rdf_file):
        html_info = rdfinfo.ParserMaffRDFInfo(self.__index_file.parser)

        rdf_file.title = html_info.title
        rdf_file.url = self.__file_info.url
        rdf_file.index_file_name = self.__file_info.index_name
        rdf_file.archive_time = self.__archive_time.time
        rdf_file.charset = html_info.charset


class _ResponseLetter(abstract.BaseLetter):
    def __init__(self, response):
        self.__response = response
        self.__file_info = rdfinfo.ResponseMaffRDFInfo(response)
        self.__archive_time = rdfinfo.TimeMaffRDFInfo()

    async def write_to(self, location):
        self.__save_response_to(location)
        self.__create_rdf_to(location)

    def __save_response_to(self, location):
        index_name = self.__file_info.index_name
        index_path = str(pathlib.Path(location).joinpath(index_name))

        with open(index_path, "wb") as fd:
            fd.write(self.__response.content_descriptor.read())

    def __create_rdf_to(self, location):
        rdf_path = str(pathlib.Path(location).joinpath("index.rdf"))

        with maff.RDF(rdf_path) as rdf_file:
            self.__init_attributes_of(rdf_file)

    def __init_attributes_of(self, rdf_file):
        rdf_file.title = self.__file_info.title
        rdf_file.url = self.__file_info.url
        rdf_file.index_file_name = self.__file_info.index_name
        rdf_file.charset = self.__file_info.charset
        rdf_file.archive_time = self.__archive_time.time


class SaveResponseLetter(abstract.BaseLetter):
    def __init__(self, response, settings, mode):
        self.__logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.__response = response
        self.__settings = settings
        self.__mode = mode

    async def write_to(self, location):
        try:
            response_letter = self.__get_response_letter()
            await response_letter.write_to(location)
        except Exception as e:
            self.__logger.exception(e)
            self.__logger.error(self.__mode)

    def __get_response_letter(self):
        if self.__is_response_html() and self.__is_js_mode():
            return self.__html_letter_with_js_execution()
        elif self.__is_response_html() and self.__is_no_js_mode():
            return self.__html_letter()
        else:
            return _ResponseLetter(self.__response)

    def __is_response_html(self):
        try:
            mime = magic.from_file(
                self.__response.content_descriptor.name, mime=True)
        except Exception as e:
            self.__logger.exception(e)
            self.__logger.error(self.__response.content_descriptor.name)
            return False
        else:
            return mime == "text/html"

    def __is_js_mode(self):
        return self.__mode is Mode.FULL_JS_EXECUTION

    def __is_no_js_mode(self):
        return self.__mode is Mode.NO_JS_EXECUTION

    def __html_letter_with_js_execution(self):
        index_migration = migration.IndexFileContainer.index_file_with_js_execution
        html_letter = _HTMLResponseLetter(
            self.__response, self.__settings, index_migration)

        return html_letter

    def __html_letter(self):
        index_migration = migration.IndexFileContainer.index_file
        html_letter = _HTMLResponseLetter(
            self.__response, self.__settings, index_migration)

        return html_letter


class Mode(enum.Enum):
    FULL_JS_EXECUTION = enum.auto()
    NO_JS_EXECUTION = enum.auto()


class Envelop(list):
    pass


class Archive:
    @classmethod
    async def archive_as_maff(cls, envelop, archive_filepath):
        with maff.MozillaArchiveFormat(archive_filepath) as archive:
            for letter in envelop:
                location = archive.create_tab()
                await letter.write_to(location)
