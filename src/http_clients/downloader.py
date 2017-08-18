from http_clients.http_client import HttpClient
from http_clients.selenium_client import SeleniumClient

class Downloader:

    def __init__(self):
        self.__client = HttpClient()
        self.__selenium = SeleniumClient()

    def sync_download(self, type: str, uri, path: str, timeout=None):
        if type == "nojs":
            self.__client.sync_req(uri, path)
        elif type == "js":
            return self.__selenium.sync_req(uri, path, timeout)
        else:
            raise ValueError("illegal option")

    def get_snapshot(self, path: str):
        self.__selenium.snapshot(path)

    def async_list(self, uri):
        pass

    def async_run(self):
        pass


