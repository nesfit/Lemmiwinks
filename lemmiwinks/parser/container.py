import tinycss2
import bs4

from . import parser


class CSSParserContainer:
    @staticmethod
    def timycss_stylesheet(fd):
        stylesheet_parser = tinycss2.parse_stylesheet(fd)
        return parser.TinyCSSParser(stylesheet_parser)

    @staticmethod
    def tinycss_declaration(declaration):
        dec_parser = tinycss2.parse_declaration_list(declaration)
        return parser.TinyCSSParser(dec_parser)


class HTMLParserContainer:
    @staticmethod
    def bs_parser(data):
        soup = bs4.BeautifulSoup(data, 'lxml')
        return parser.BsHTMLParser(soup)
