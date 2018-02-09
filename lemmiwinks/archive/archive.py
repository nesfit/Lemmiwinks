from . import abstract
from . import maff


class SaveResponseLetter(abstract.BaseLetter):
    def __init__(self, response):
        self.__response = response
        self.__index_file_name = ""
        self.__url = response.accessed_url

    async def write_to(self, location):
        self.__create_index_files_dir_in(location)
        await self.__save_response_to(location)
        self.__generate_rdf()

    def __create_index_files_dir_in(self, location):
        pass

    async def __save_response_to(self, location):
        pass

    def __generate_rdf(self):
        pass


class Envelop(list):
    pass


class Archive:
    @classmethod
    async def archive_as_maff(cls, envelop: Envelop):
        with maff.MozillaArchiveFormat as archive:
            for letter in envelop:
                location = archive.create_tab()
                await letter.write_to(location)