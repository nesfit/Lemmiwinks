

class MetaInfoTab:
    def __init__(self, dst):
        self.__dst = dst
        self.__info = dict()
        self.__table = ""
        self.__data = '<!doctype html>\n' \
                      '<head>\n' \
                      '<meta charset="utf-8">\n' \
                      '<title>Meta info</title>\n' \
                      '<style>\n' \
                      'table {\n' \
                      'font-family: arial, sans-serif;\n' \
                      'border-collapse: collapse;\n' \
                      'width: 100%;\n' \
                      '}\n' \
                      'td, th {\n' \
                      'border: 1px solid #dddddd;\n' \
                      'text-align: left;\n' \
                      'padding: 8px;\n' \
                      '}\n' \
                      'tr:nth-child(even){\n' \
                      'background-color: #dddddd;\n' \
                      '}\n' \
                      '</style>\n' \
                      '</head>\n'

    def __add_body(self):
        self.__data += '<body>\n' + self.__table +'</body>\n'

    def add_img_hash(self, hash: str):
        self.__info["Screenshot hash"] = hash

    def add_time(self, time: str):
        self.__info["Time"] = time

    def add_url(self, url):
        self.__info["URL"] = url

    def add_ipv4(self, ip: str):
        self.__info["IP4 Address"] = ip

    def add_ipv6(self, ip: str):
        self.__info["IP6 Address"] = ip

    def add_encoding(self, enc: str):
        self.__info["Encoding"] = enc

    def add_scraped_info(self, info):
        self.__info["Parsed Information"] = info

    def export2html(self):
        self.__table += '<table>\n'
        for key, value in self.__info.items():
            self.__table += '<tr>\n<td><b>' + key + '</b></td>\n'
            if isinstance(value, list) or isinstance(value, set):
                self.__table += '<td>'
                for v in value:
                    self.__table += v + '<br/>\n'
                self.__table += '</td>\n'
            else:
                self.__table += '<td>' + value + '</td>\n'
            self.__table += '</tr>\n'
        self.__table += '</table>\n'
        self.__add_body()

        with open(self.__dst + '/index.htm', "w") as fd:
            fd.write(self.__data)