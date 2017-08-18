import urllib.parse
import validators
import validators.utils

class URL:
    def __init__(self, baseurl):
        self.__baseurl = self.__format(baseurl)

    def resolve(self, url):
        url = urllib.parse.urljoin(self.__baseurl, self.__format(url))
        if not validators.url(url):
            raise RuntimeWarning
        return url

    def __format(self, url):
        return urllib.parse.quote(url, safe="%/:=&?~#+!$,;'@()*[]")

    def set_baseurl(self, url):
        self.__baseurl = self.__format(url)