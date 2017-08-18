from bs4 import BeautifulSoup
import re


class HTMLParser:
    def __init__(self, filename: str):
        self.__filename = filename
        with open(filename) as fp:
            self.__soup = BeautifulSoup(fp, "lxml")

    def elements(self, tag: str, attr=None):
        elements = self.__soup.find_all(
            tag) if attr is None else self.__soup.find_all(tag, {attr: True})
        return elements

    def get_charset(self):
        elem = self.__soup.find_all("meta")
        for e in elem:
            try:
                # HTML 5 standard to define charset
                if "charset" in e:
                    return e.get("charset")
                # support for HTML 4 meta tag has http-equiv attribute with
                # content-type value
                elif e.get("http-equiv").lower() == "content-type":
                    # this regex matches a charset in content attribute
                    # example : content="text/html;charset=UTF-8"
                    # regex will match everything from '=' to $ or ';'
                    return re.search("(?<==).*?(?=;|$)",
                                     e.get("content")).group(0)
            except Exception:
                continue
        # default charset
        return "UTF-8"

    def get_title(self):
        title = self.__soup.title.string
        return title if title else "unknown"

    def base(self):
        return self.__soup.base

    def text(self):
        soup = self.__soup.__copy__()
        [s.extract() for s in soup(['style', 'script', '[document]', 'head', 'title'])]
        return soup.getText()

    def save(self):
        with open(self.__filename, "wb") as fp:
            fp.write(self.__soup.prettify("utf-8"))