# third party imports
import tinycss2
from tinycss2.ast import URLToken, StringToken
# local imports
from . import abstract
from . import exception


class TinyCSSParser(abstract.CSSParser):
    def __init__(self, parser):
        logger_name = "{}.{}".format(__name__, __class__.__name__)
        super().__init__(parser, logger_name)

    def __del__(self):
        pass

    def parse_tokens(self):
        for rule in self._parser:
            self.__search_tokens_in(rule)

    def __search_tokens_in(self, rule):
        try:
            for rule in rule.content:
                self.__process_rule(rule)
        except TypeError:
            # Some object can't be iterable for example <AtRule @import … { … }>
            self.__process_rule(rule)
        except AttributeError:
            # The exception is raised during the parsing when
            # the parser processes the CSS token which is not stored.
            pass
        except Exception as e:
            self._logger.error("Unexpected error during parsing {}\n{}".format(e, rule))
            raise exception.ParserError(e)

    def __process_rule(self, rule):
        if self.__is_import(rule):
            self.__process_import(rule)
        elif self.__is_url_token(rule):
            self.__process_url_token(rule)
        # declaration rule can be found in HTML style attribute
        elif self.__is_declaration(rule):
            self.__process_declaration(rule)
        else:
            self.__search_tokens_in(rule)

    def __is_import(self, rule):
        return rule.type == "at-rule" and rule.lower_at_keyword == "import"

    def __process_import(self, rule):
        for component_value in rule.prelude:
            self.__process_component_value(component_value)

    def __process_component_value(self, component_value):
        if self.__is_string_token(component_value) or self.__is_url_token(component_value):
            self._import_token_list.append(component_value)
        else:
            self.__search_tokens_in(component_value)

    def __is_string_token(rule):
        return rule.type == "string"

    def __is_url_token(self, rule):
        return rule.type == "url"

    def __process_url_token(self, token):
        if self.__is_token_value_url(token):
            self._url_token_list.append(token.value)

    def __is_token_value_url(self, token):
        # An image can be represented as raw data written inside the URL.
        # In this case, URL starts with "data:image" prefix.
        return token.value.lower().startswith("data:image") is False


    def __is_declaration(self, rule):
        return rule.type == "declaration"

    def __process_declaration(self, rule):
        for component_value in rule.value:
            self.__search_tokens_in(component_value)
