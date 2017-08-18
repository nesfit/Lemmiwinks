from scrapy import resolver

import maff
import os.path
from typing import List
import extract
import resolver
import parsers
import metainfo
import metainfo_tab

class GetPage:
    def __init__(self, tab_list: List, pathname: str, regex_list=[]):
        self.__tab_list = tab_list
        self.__url = tab_list[0]
        self.__screen = tab_list[1]
        self.__maff = maff.MAFF(tab_list, pathname)
        self.__scraper = metainfo.Scraper(regex_list)
        meta_dst = self.__maff.get_page_dir(tab_list[2])
        self.__meta = metainfo_tab.MetaInfoTab(meta_dst)

    def __create_rdf(self, url: str, filename: str, time=None):
        basename = os.path.basename(filename)
        html = parsers.HTMLParser(filename)
        try:
            title = html.get_title()
            charset = resolver.get_file_encoding(filename)
            self.__maff.add_rdf_info(url, title, basename, charset['encoding'])
        except Exception:
            self.__maff.add_rdf_info(url, "unknown", basename, "UTF-8")

    def __create_metainfo(self, filename=None, time=None):
        image_dst = self.__maff.get_page_dir(self.__screen) + "/index.png"
        ipv4, ipv6 = metainfo.get_netinfo(self.__url)
        self.__meta.add_img_hash(metainfo.hash_file(image_dst))
        self.__meta.add_url(self.__url)
        self.__meta.add_ipv4(ipv4)
        self.__meta.add_ipv6(ipv6)
        self.__meta.add_scraped_info(self.__scraper.get_discovered())
        self.__meta.export2html()

    def save_page(self):
        page_dst = self.__maff.get_page_dir(self.__url)
        image_dst = self.__maff.get_page_dir(self.__screen)

        page = extract.Page(self.__url, page_dst, image_dst, self.__scraper.search_file)
        filename = page.save_page()
        self.__create_metainfo()

        self.__create_rdf(self.__url, filename)

        self.__maff.compress()
