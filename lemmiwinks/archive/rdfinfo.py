import pathlib
import lemmiwinks.pathgen as pathgen
import logging
import urllib.parse
from time import strftime, localtime


class ResponseMaffRDFInfo:
    def __init__(self, response):
        self.__logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.__response = response

    @property
    def index_name(self):
        try:
            response_path = self.__response.content_descriptor.name
            url = self.__response.accessed_url

            mime = pathgen.MimeFileExtension(response_path, url)

            index_name = mime.add_extension_to("index")
        except Exception as e:
            self.__logger.exception(e)
            return "index.unknown"
        else:
            return index_name

    @property
    def title(self):
        try:
            url_path = urllib.parse.urlparse(self.__response.accessed_url).path
            title = pathlib.Path(url_path).name
        except Exception as e:
            self.__logger.exception(e)
            return ""
        else:
            return title

    @property
    def url(self):
        try:
            url = self.__response.accessed_url
        except Exception as e:
            self.__logger.exception(e)
            return ""
        else:
            return url

    @property
    def charset(self):
        return ""


class ParserMaffRDFInfo:
    def __init__(self, parser):
        self.__logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.__parser = parser

    @property
    def title(self):
        try:
            title = self.__parser.title.string

            if title is None:
                title = ""

        except Exception as e:
            self.__logger.exception(e)
            return ""
        else:
            return title

    @property
    def charset(self):
        try:
            charset = self.__parser.charset

            if charset is None:
                charset = ""

        except Exception as e:
            self.__logger.exception(e)
            return ""
        else:
            return charset


class TimeMaffRDFInfo:
    def __init__(self):
        self.__logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @property
    def time(self):
        try:
            time = strftime("%a, %d %b %Y %H:%M:%S %z", localtime())
        except Exception as e:
            self.__logger.exception(e)
            return ""
        else:
            return time


