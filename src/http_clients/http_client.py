from http_clients.dwnld_intf import DwnldIntf
import urllib3
import urllib3.util
from twisted.web.client import getPage
from twisted.internet import reactor


class HttpClient(DwnldIntf):
    def __init__(self):
        self.__timeout = urllib3.util.Timeout(connect=2.0, read=7.0)
        self.__http = urllib3.PoolManager()
        self.__reactor = reactor

    def sync_req(self, uri, path: str):
        r = self.__http.request('GET', uri, preload_content=False, timeout=self.__timeout)
        self.safe_2_file(r.data, path)

    def async_req_list(self, uri: str, filename: str):
        deferred = getPage(uri)
        deferred.addCallback(self.__save_content, path)

    def async_run(self):
        self.__reactor.run()

    def __save_content(self, content, filename: str):
        with open(filename, "wb") as fd:
            fd.write(content)


