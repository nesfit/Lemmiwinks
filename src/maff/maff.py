import os.path
import shutil
import tempfile
import datetime
from tzlocal import get_localzone
from typing import List, Dict
from resolver import filename
from maff.rdf import RDF


class MAFF:
    def __init__(self, url_list: List[str], pathname):
        self.__path = pathname
        self.__tmp = tempfile.TemporaryDirectory()
        self.__dirs = self.__generate_dirs(url_list)

    def __generate_dirs(self, url_list: List[str]) -> Dict[str, str]:
        dirs = {}

        for url in url_list:
            dir_name = self.__tmp.name + "/" + filename.unique(self.__tmp.name)
            dirs[str(url)] = dir_name
            os.mkdir(dir_name)
        return dirs

    def get_index_files(self, url: str) -> str:
        return self.__dirs.get(url) + "/index_files"

    def get_page_dir(self, url: str) -> str:
        return self.__dirs.get(url)

    def add_rdf_info(self, url: str, title: str, index: str, charset: str):
        name = "%s/index.rdf" % self.__dirs.get(url)
        tz = get_localzone()  # local timezone
        time = datetime.datetime.now(tz).strftime('%a %d %b %Y %X %z')
        rdf_info = RDF(name)
        rdf_info.add("originalurl", url)
        rdf_info.add("title", title)
        rdf_info.add("archivetime", time)
        rdf_info.add("indexfilename", index)
        rdf_info.add("charset", charset)

        rdf_info.save()

    def compress(self):
        name = shutil.make_archive(self.__path, 'zip', self.__tmp.name)
        os.rename(name, self.__path + '.maff')
