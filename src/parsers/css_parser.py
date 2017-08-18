import tinycss2


class CSSParser:
    def __init__(self, stream, declaration=False):
        self.__parser = tinycss2.parse_declaration_list(
            stream) if declaration else tinycss2.parse_stylesheet(stream)
        self.__import = []
        self.__ext_dep = []
        self.__parse_dep()

    def __parse_dep(self):
        for rule in self.__parser:
            self.__rule_parser(rule)

    def __rule_parser(self, rule):
        try:
            if rule.type in ["at-rule"] and rule.lower_at_keyword == "import":
                for token in rule.prelude:
                    if token.type in ["url", "string"]:
                        self.__import.append(token)
            elif rule.type in ["qualified-rule", "at-rule", "{} block", "[] block",
                           "() block"]:
                for token in rule.content:
                    self.__rule_parser(token)
            elif rule.type == "declaration":
                for token in rule.value:
                    self.__rule_parser(token)
            elif rule.type == "url":
                if rule.value.lower().startswith("data:image") is False:
                    self.__ext_dep.append(rule)
        except TypeError:
            pass

    def import_res(self):
        return self.__import

    def external_res(self):
        return self.__ext_dep

    def export(self):
        return tinycss2.serialize(self.__parser)
