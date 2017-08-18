from http_clients.dwnld_intf import DwnldIntf
from selenium import webdriver
import time

class SeleniumClient(DwnldIntf):
    def __init__(self):
        self.__driver = webdriver.PhantomJS('../lib/phantomjs')
        self.__driver.set_window_size(1920, 1080)
        self.__driver.set_page_load_timeout(3000)
        self.__driver.set_script_timeout(3000)

    def sync_req(self, uri: str, path: str, timeout: float):
        self.__driver.get(uri)
        time.sleep(3)
        self.safe_2_file(self.__driver.page_source.encode('utf-8'), path)
        return self.__driver.current_url

    def snapshot(self, path: str):
        self.__driver.save_screenshot(path+"/index.png")
