import http_clients
import parsers
import resolver
import os.path
from extract.css_extractor import CSSExtractor
from extract.js_extractor import JSExtractor
from extract.html_extractor import HTMLLExtractor


class Page(resolver.NameGenerator):
    __max_recursion = 3

    def __init__(self, url: str, dst: str, screen_dst=None, scraper=None):
        self.__client = http_clients.Downloader()
        self.__url = url
        self.__dst = dst
        self.__screen_dst = screen_dst
        self.__scraper = scraper

    def screen_shot(self):
        pass

    def __index(self, url, dst, filename=None):
        filename = filename if filename else super().gen_name("index")
        curl = self.__client.sync_download("js", url, dst + "/" + filename)
        name = resolver.set_file_ext(dst + "/" + filename)

        return name, curl

    def save_page(self):
        filename, curl = self.__index(self.__url, self.__dst, "index")

        if self.__screen_dst is not None:
            self.__client.get_snapshot(self.__screen_dst)

        self.__save_dependencies(curl, filename, self.__dst + "/index_files", "index_files")
        self.__client.async_run()

        return filename

    def __save_dependencies(self, url: str, filename: str, dst: str, rpath=None, rec_level=0):
        if rec_level == Page.__max_recursion:
            return

        html = parsers.HTMLParser(filename)
        url_res = resolver.URL(url)
        base = html.base()

        if base:
            url_res = resolver.URL(url_res.resolve(base["href"]))
            base.decompose()


        if self.__scraper is not None:
            self.__scraper(html.text())

        html_e = HTMLLExtractor(html, self.__client, url_res, dst, rpath)
        js_e = JSExtractor(html, self.__client, dst, rpath)
        css_e = CSSExtractor(html, self.__client, url_res, dst, rpath)
        html_e.html_resources()
        js_e.js_events()
        js_e.js_script()
        css_e.css_inline()
        css_e.css_link()
        css_e.css_style()

        for frame in html_e.html_frames():
            filename, curl = self.__index(frame[0], dst)
            frame[1]["src"] = rpath + "/" + os.path.basename(filename) if rpath else os.path.basename(filename)
            rec_level += 1
            self.__save_dependencies(curl, filename, dst, None, rec_level)
        html.save()
