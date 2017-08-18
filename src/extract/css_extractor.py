import resolver
import parsers
import urllib3

class CSSExtractor(resolver.NameGenerator):
    def __init__(self, html_parser, http_client, url_res, dst: str, rel_dir=None):
        self.__html_parser = html_parser
        self.__client = http_client
        self.__url_res = url_res
        self.__dst = dst
        self.__rel_dir = rel_dir

    def __css_resources(self, parser, url_res, rel_dir=None):
        for token in parser.external_res():
            try:
                uri = url_res.resolve(token.value)
                name = super().gen_name("css", resolver.ext_from_url(uri))
                self.__client.sync_download("nojs", uri, self.__dst + "/" + name)
                token.value = rel_dir + "/" + name if rel_dir else name
            except urllib3.exceptions.MaxRetryError:
                continue
            except RuntimeWarning:
                continue

    def __css_imports(self, parser, url_res, rel_dir=None):
        for token in parser.import_res():
            try:
                uri = url_res.resolve(token.value)
                name = super().gen_name("css", resolver.ext_from_url(uri))
                self.__client.sync_download("nojs", uri, self.__dst + "/" + name)
                token.value = rel_dir + "/" + name if rel_dir else name
                self.__css_file(self.__dst + "/" + name, uri)
            except RuntimeWarning:
                continue

    def __css_file(self, filename: str, url: str):
        format = resolver.get_file_encoding(filename) # TODO
        with open(filename, "r", encoding=format["encoding"]) as fd:
            css_parser = parsers.CSSParser(fd.read())

        url_res = resolver.URL(url)
        self.__css_resources(css_parser, url_res)
        self.__css_imports(css_parser, url_res)

        with open(filename, "w") as fd:
            try:
                fd.write(css_parser.export())
            except Exception:
                print(filename)
                print(url)

    def css_inline(self):
        for element in self.__html_parser.elements(True, "style"):
            css_parser = parsers.CSSParser(element["style"], True)
            self.__css_resources(css_parser,self.__url_res, self.__rel_dir)
            self.__css_imports(css_parser, self.__url_res, self.__rel_dir)
            element["style"] = css_parser.export()

    def css_style(self):
        for element in self.__html_parser.elements("style"):
            try:
                css_parser = parsers.CSSParser(element.string)
                self.__css_resources(css_parser, self.__url_res, self.__rel_dir)
                self.__css_imports(css_parser, self.__url_res, self.__rel_dir)
                element.string = css_parser.export()
            except TypeError:
                # element.string is None
                continue

    def css_link(self):
        for element in self.__html_parser.elements("link", "href"):
            try:
                if "stylesheet" not in element.get("rel"):
                    continue

                uri = self.__url_res.resolve(element.get("href"))
                name = super().gen_name("css", resolver.ext_from_url(uri))
                self.__client.sync_download("nojs", uri, self.__dst + "/" + name)
                element["href"] = self.__rel_dir + "/" + name if self.__rel_dir else name
                self.__css_file(self.__dst + "/" + name, uri)
            except Exception as e:
                print(e.value)
                print(element)
                print(uri)
                continue
