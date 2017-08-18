from xml.etree.ElementTree import Element, SubElement
from xml.etree import ElementTree


class RDF:
    def __init__(self, filename):
        self.__filename = filename
        self.__root = Element("RDF:RDF")
        self.__root.set("xmlns:MAF", "http://maf.mozdev.org/metadata/rdf#")
        self.__root.set("xmlns:NC", "http://home.netscape.com/NC-rdf#")
        self.__root.set("xmlns:RDF",
                        "http://www.w3.org/1999/02/22-rdf-syntax-ns#")
        self.__desc = SubElement(self.__root, "RDF:Description")
        self.__desc.set("RDF:about", "urn:root")

    def add(self, type, value):
        if type == "originalurl":
            e = SubElement(self.__desc, "MAF:originalurl")
        elif type == "title":
            e = SubElement(self.__desc, "MAF:title")
        elif type == "archivetime":
            e = SubElement(self.__desc, "MAF:archivetime")
        elif type == "indexfilename":
            e = SubElement(self.__desc, "MAF:indexfilename")
        elif type == "charset":
            e = SubElement(self.__desc, "MAF:charset")
        else:
            raise ValueError("Illegal parameter")
        e.set("RDF:resource", value)

    def save(self):
        with open(self.__filename, "wb") as fd:
            fd.write(ElementTree.tostring(self.__root, 'utf-8'))
