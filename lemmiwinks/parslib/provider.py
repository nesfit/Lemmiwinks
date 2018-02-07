import tinycss2
import bs4
import logging
from . import parser


class CSSParserProvider:
    @classmethod
    def tinycss_parser(cls, data, declaration=False):
        try:
            if declaration:
                css_parser = tinycss2.parse_declaration_list(
                    data, skip_comments=True, skip_whitespace=True)
            else:
                css_parser = CSSParserProvider.__create_tynicss_stylesheet(data)
        except Exception as e:
            logging.error(f"CSSParserProvider error: {e}")
        else:
            return parser.TinyCSSParser(css_parser)

    @classmethod
    def __create_tynicss_stylesheet(cls, data):
        if hasattr(data, "read"):  # is file like object
            css_parser, _ = tinycss2.parse_stylesheet_bytes(
                data.read(), skip_comments=True, skip_whitespace=True)
        else:
            css_parser = tinycss2.parse_stylesheet(
                data, skip_comments=True, skip_whitespace=True)
        return css_parser


class HTMLParserProvider:
    @classmethod
    def bs_parser(cls, data):
        soup = bs4.BeautifulSoup(data, 'lxml')
        return parser.BsHTMLParser(soup)
