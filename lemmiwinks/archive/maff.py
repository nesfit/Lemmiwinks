import tempfile
import logging
import zipfile
import os
import xml.etree.ElementTree as ET


class MozillaArchiveFormat:
    def __init__(self, filepath: str):
        self._filepath = filepath
        self._tabs = list()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.make_archive()

    def create_tab(self):
        tab = tempfile.TemporaryDirectory()
        self._tabs.append(tab)

        return tab.name

    def make_archive(self):
        archive_name = f"{self._filepath}.maff"

        with zipfile.ZipFile(archive_name, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            self.__zip_directory_to(zip_file)

    def __zip_directory_to(self, zip_file):
        for tab in self._tabs:
            for dirpath, _, file_names in os.walk(tab.name):
                for file_name in file_names:
                    filepath = os.path.join(dirpath, file_name)
                    arcname = os.path.relpath(filepath, os.path.dirname(tab.name))
                    zip_file.write(filepath, arcname)


class RDF:
    def __init__(self, filepath):
        self._filepath = filepath
        self._xml = None
        self._description = None
        self.__init_xml()
        self.__init_description()

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

    def __init_description(self):
        self._description = ET.SubElement(self._xml, "RDF:Description")
        self._description.set("RDF:about", "urn:root")

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
        return self._description.find(tag)

    def __update_element(self, tag: str, value: str):
        try:
            element = self.__find_element_by(tag)
            element.set("RDF:resource", value)
        except AttributeError:
            self.__create_node(tag, value)

    def __create_node(self, tag: str, attr_value: str):
        ET.SubElement(self._description, tag, {"RDF:resource": attr_value})

    def save(self):
        element_tree = ET.ElementTree(element=self._xml)
        element_tree.write(self._filepath, encoding="unicode")
