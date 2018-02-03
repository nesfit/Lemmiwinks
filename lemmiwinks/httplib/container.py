import collections
import logging
import enum
import tempfile

Proxy = collections.namedtuple("Proxy", "url login password")
AIOProxy = collections.namedtuple("_AIOProxy", "url auth")


class Response:
    def __init__(self, content_descriptor=None, url_and_status=list()):
        self.__logger = logging.getLogger("{}.{}".format(__name__, __class__.__name__))
        self.__content_descriptor = None
        self.__url_and_status = None

        self.url_and_status = url_and_status
        self.content_descriptor = content_descriptor

    def __del__(self):
        try:
            self.__content_descriptor.close()
        except Exception as e:
            self.__logger.warning(e)

    @property
    def content_descriptor(self):
        return self.__content_descriptor

    @content_descriptor.setter
    def content_descriptor(self, content_descriptor: tempfile.NamedTemporaryFile):
        self.__content_descriptor = content_descriptor
        self.__content_descriptor.seek(0)

    @property
    def url_and_status(self):
        return self.__url_and_status

    @url_and_status.setter
    def url_and_status(self, url_and_status: list):
        self.__url_and_status = url_and_status

    @property
    def requested_url(self):
        try:
            url, _ = self.url_and_status[0]
        except Exception as e:
            url = None
            self.__logger.error(e)
        finally:
            return url

    @property
    def accessed_url(self):
        try:
            url, _ = self.url_and_status[-1]
        except Exception as e:
            url = None
            self.__logger.error(e)
        finally:
            return url


class InstanceStatus(enum.Enum):
    RESERVED = enum.auto()
    AWALIABLE = enum.auto()
