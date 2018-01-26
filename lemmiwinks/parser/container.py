import tinycss2
import bs4

from . import parser


class CSSParserContainer:
    @staticmethod
    def timycss_parser(data):
        try:
            if hasattr(data, "read"): # is file like object
                css_parser = tinycss2.parse_stylesheet(data)
            else:
                css_parser = tinycss2.parse_declaration_list(data)
        except Exception as e:
            print(e)
        else:
            return parser.TinyCSSParser(css_parser)


class HTMLParserContainer:
    @staticmethod
    def bs_parser(data):
        soup = bs4.BeautifulSoup(data, 'lxml')
        return parser.BsHTMLParser(soup)
