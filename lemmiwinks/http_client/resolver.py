import logging
import urllib.parse

import validators

from . import exception


class URLResolver:
    def __init__(self, base):
        logger_name = "{}.{}".format(__name__, __class__.__name__)
        self._logger = self._logger = logging.getLogger(logger_name)
        self.__base = self.__format(base)

    @staticmethod
    def __format(url):
        return urllib.parse.quote(url, safe="%/:=&?~#+!$,;'@()*[]")

    def resolve(self, url):
        try:
            url = urllib.parse.urljoin(self.__base, self.__format(url))
            validators.url(url)
        except validators.ValidationFailure as e:
            self._logger.error(
                "URL {} is not valid. The base URL is {}".format(url, self.__base))
            raise exception.UrlValidationError(e)
        except Exception as e:
            self._logger.error(e)
            raise exception.URLResolverError(e)
        else:
            return url

    @property
    def base(self):
        return self.__base

    @base.setter
    def base(self, url):
        self.__base = self.__format(url)
