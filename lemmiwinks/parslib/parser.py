from typing import List, Dict

# third party imports
import tinycss2

# local imports
from . import abstract
from . import exception

DEFAULT_ENCODING = "utf-8"


class TinyCSSParser(abstract.CSSParser):
    def __init__(self, parser):
        logger_name = f"{__name__}.{self.__class__.__name__}"
        super().__init__(parser, logger_name)

    def parse_tokens(self):
        try:
            for rule in self._parser:
                self.__search_tokens_in(rule)
        except Exception as e:
            self._logger.error(e)

    def __search_tokens_in(self, rule):
        try:
            if self.__is_declaration(rule):
                [self.__process_rule(component_value) for component_value in rule.value]
            # @import url;
            # @import url list-of-media-queries;
            elif self.__is_import(rule):
                self.__process_import(rule)
            elif self.__is_at_rule(rule) or self.__is_qualified_rule(rule):
                [self.__process_rule(component_value) for component_value in rule.prelude]
                [self.__process_rule(rule) for rule in rule.content]
        except TypeError:
            # (Some object are not iterable for example <AtRule @import … { … }>)
            pass
        except AttributeError:
            # The exception is raised during the parsing when
            # the parser processes the CSS token which is not stored.
            pass
        except Exception as e:
            self._logger.error("Unexpected error during parsing {}\n{}".format(e, rule))
            raise exception.ParserError(e)

    @staticmethod
    def __is_declaration(rule):
        return rule.type == "declaration"

    @staticmethod
    def __is_at_rule(rule):
        return rule.type == "at-rule"

    @staticmethod
    def __is_qualified_rule(rule):
        return rule.type == "qualified-rule"

    def __process_rule(self, rule):
        try:
            # url("http://mysite.example.com/mycursor.png")
            # url('http://mysite.example.com/mycursor.png')
            # url(http://mysite.example.com/mycursor.png)
            if self.__is_url_token(rule):
                self.__process_url_token(rule)
            # indirect recursion, parse rule to sub-rules and analyze
            else:
                [self.__process_rule(value) for value in rule.value]
        except Exception:
            pass

    @staticmethod
    def __is_import(rule):
        return rule.type == "at-rule" and rule.lower_at_keyword == "import"

    def __process_import(self, rule):
        # Component value:
        # |-|---- Preserved token -----|-|
        #      |----- {} block -----|
        #      |----- () block -----|
        #      |----- [] block -----|
        #      |-- Function block --|
        #
        # Preserved tokens:
        # Any token produced by the tokenizer except for <function-token>s,
        # <{-token>s, <(-token>s, and <[-token>s.
        for component_value in rule.prelude:
            self.__process_component_value(component_value)

    def __process_component_value(self, component_value):
        if self.__is_string_token(component_value) or self.__is_url_token(
                component_value):
            self._import_token_list.append(TinyToken(component_value))
        else:
            self.__search_tokens_in(component_value)

    @staticmethod
    def __is_string_token(rule):
        return rule.type == "string"

    @staticmethod
    def __is_url_token(rule):
        return rule.type == "url"

    def __process_url_token(self, token):
        if self.__is_token_value_url(token):
            self._url_token_list.append(TinyToken(token))

    @staticmethod
    def __is_token_value_url(token):
        # An image can be represented as raw data written inside the URL.
        # In this case, URL starts with "data:image" prefix.
        return token.value.lower().startswith("data:image") is False

    def __process_declaration(self, rule):
        for component_value in rule.value:
            self.__search_tokens_in(component_value)

    def export(self):
        return tinycss2.serialize(self._parser)


class BsHTMLParser(abstract.HTMLParser):
    def __init__(self, parser):
        logger_name = f"{__name__}.{__class__.__name__}"
        super().__init__(logger_name)
        self._soup = parser

    def find_elements(self, tag, attribute: Dict = {}) -> List[abstract.Element]:
        elements = self._soup.find_all(tag, attribute)
        element_list = self.__convert_to_bselement_list(elements)
        return element_list

    @staticmethod
    def __convert_to_bselement_list(elements):
        return [BsElement(element) for element in elements]

    @property
    def title(self):
        if self._soup.title is None:
            return None
        else:
            return BsElement(self._soup.title)

    @property
    def base(self):
        if self._soup.base is None:
            return None
        else:
            return BsElement(self._soup.base)

    @base.deleter
    def base(self):
        if self._soup.base is not None:
            self._soup.base.decompose()

    @property
    def charset(self):
        try:
            return self._soup.find("meta", {"charset": True}).get("charset")
        except Exception as e:
            self._logger.info(e)
            return None

    @property
    def text(self):
        return self._soup.text

    def export(self):
        return self._soup.prettify(DEFAULT_ENCODING)


class BsElement(abstract.Element):
    def __init__(self, element):
        super().__init__(element)

    def __str__(self):
        return str(self._element)

    def __getitem__(self, item):
        return self._element.attrs.get(item)

    def __setitem__(self, key, value):
        self._element.attrs.update({key: value})

    @property
    def name(self):
        return self._element.name

    @property
    def string(self):
        return self._element.string

    @string.setter
    def string(self, string):
        self._element.string = string

    @property
    def attrs(self):
        return self._element.attrs


class TinyToken(abstract.Token):
    def __init__(self, token):
        super().__init__(token)

    def __str__(self):
        return str(self._token)

    @property
    def value(self):
        return self._token.value

    @value.setter
    def value(self, value):
        self._token.value = value
