import tempfile
import zipfile
import os
import xml.etree.ElementTree as ET


class MozillaArchiveFormat:
    def __init__(self, filepath: str):
        self._filepath = filepath
        self._temp_file = tempfile.TemporaryDirectory()
        self._tabs = dict()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.make_archive()

    def add_tab(self, tab_id: str):
        tab_location = os.path.join(self._filepath, tab_id)
        os.mkdir(tab_location)
        self._tabs.update({tab_id: Tab(tab_location)})

    def get_tab(self, tab_id: str):
        return self._tabs.get(tab_id)

    def make_archive(self):
        archive_name = "{}.maff".format(self._filepath)

        with zipfile.ZipFile(archive_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            self.__zip_directory_to(zipf)

    def __zip_directory_to(self, zipf):
        for dirpath, _, file_names in os.walk(self._temp_file.name):
            for file_name in file_names:
                zipf.write(os.path.join(dirpath, file_name))


class Tab:
    def __init__(self, dirpath):
        self._dirpath = dirpath
        self._index_files_dir = set()

    @property
    def dirpath(self):
        return self._dirpath

    @property
    def index_path(self, extension):
        index_name = "index.{}".format(extension)
        return os.path.join(self._dirpath, index_name)

    @property
    def index_rdf_path(self):
        return os.path.join(self._dirpath, "index.rdf")

    def create_index_files_dir(self):
        index_files_path = os.path.join(self._dirpath, "index_files")
        os.mkdir(index_files_path)

    @property
    def index_files_path(self):
        index_files_path = os.path.join(self._dirpath, "index_files")

        if os.path.exists(index_files_path) is False:
            index_files_path = None

        return index_files_path

    def generate_new_resource_location(self, filename):
        if filename in self._index_files_dir:
            raise FileExistsError

        resource_location = os.path.join(self._dirpath, filename)
        #self._index_files_dir.append(filename)
        return resource_location

    def get_resource_location(self, filename):
        pass


class RDF:
    def __init__(self, filepath):
        self._filepath = filepath
        self._xml = None
        self._desc = None
        self.__init_xml()
        self.__init_desc()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.save()

    def __str__(self):
        return ET.tostring(self._xml, encoding="unicode")

    def __init_xml(self):
        self._xml = ET.Element("RDF:RDF")
        self._xml.set("xmlns:MAF", "http://maf.mozdev.org/metadata/rdf#")
        self._xml.set("xmlns:NC", "http://home.netscape.com/NC-rdf#")
        self._xml.set("xmlns:RDF", "http://www.w3.org/1999/02/22-rdf-syntax-ns#")

    def __init_desc(self):
        self._desc = ET.SubElement(self._xml, "RDF:Description")
        self._desc.set("RDF:about", "urn:root")

    @property
    def url(self) -> str:
        return self.__get_element_value("MAF:originalurl")

    @url.setter
    def url(self, url: str):
        self.__update_element("MAF:originalurl", url)

    @property
    def title(self) -> str:
        return self.__get_element_value("MAF:title")

    @title.setter
    def title(self, title: str):
        self.__update_element("MAF:title", title)

    @property
    def archive_time(self) -> str:
        return self.__get_element_value("MAF:archivetime")

    @archive_time.setter
    def archive_time(self, time: str):
        self.__update_element("MAF:archivetime", time)

    @property
    def index_file_name(self) -> str:
        return self.__get_element_value("MAF:indexfilename")

    @index_file_name.setter
    def index_file_name(self, index_name: str):
        self.__update_element("MAF:indexfilename", index_name)

    @property
    def charset(self) -> str:
        return self.__get_element_value("MAF:charset")

    @charset.setter
    def charset(self, charset: str):
        self.__update_element("MAF:charset", charset)

    def __get_element_value(self, tag: str):
        try:
            element = self.__find_element_by(tag)
            return element.get("RDF:resource")
        except AttributeError:
            return None

    def __find_element_by(self, tag: str):
        return self._desc.find(tag)

    def __update_element(self, tag: str, value: str):
        try:
            element = self.__find_element_by(tag)
            element.set("RDF:resource", value)
        except AttributeError:
            self.__add_node(tag, value)

    def __add_node(self, tag: str, attr_value: str):
        ET.SubElement(self._desc, tag, {"RDF:resource": attr_value})

    def save(self):
        element_tree = ET.ElementTree(element=self._xml)
        element_tree.write(self._filepath, encoding="unicode")
