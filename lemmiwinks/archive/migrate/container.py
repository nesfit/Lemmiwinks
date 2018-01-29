class ElementFilterRules:
    _element_sources = {"img": [{"src": True}, {"data-src": True}],
                        "video": [{"src": True}, {"poster": True}],
                        "embed": [{"src": True}],
                        "source": [{"src": True}],
                        "audio": [{"src": True}],
                        "input": [{"src": True}],
                        "object": [{"data": True}, {"codebase": True}],
                        "track": [{"src": True}]}
    _stylesheet_link = {"link": [{"href": True, "rel": "stylesheet"}]}
    _js_style = {"script": [{"src": True}]}

    @property
    def elements(self):
        return self.__flatten(ElementFilterRules._element_sources)

    @property
    def stylesheet_link(self):
        return self.__flatten(ElementFilterRules._stylesheet_link)

    @property
    def js_style(self):
        return self.__flatten(ElementFilterRules._js_style)

    @staticmethod
    def __flatten(rules):
        flatten_rules = [(name, attr) for name, attrs in rules.items() for attr in attrs]
        return flatten_rules


class HTMLFilter:
    def __init__(self, html_parser):
        self._filter_rules = ElementFilterRules()
        self._parser = html_parser

    @property
    def elements(self):
        return self.__get_element_list_from(self._filter_rules.elements)

    @property
    def stylesheet_link(self):
        return self.__get_element_list_from(self._filter_rules.stylesheet_link)

    def js_style(self):
        return self.__get_element_list_from(self._filter_rules.js_style)

    def __get_element_list_from(self, rules):
        element_rules = [(element, attr) for name, attrs in rules
                         for element, attr in self.__convert_to_list(name, attrs)]
        return element_rules

    def __convert_to_list(self, name, attrs: dict):
        attr = self.__get_depended_attribute(attrs)
        elements = self._parser.find_elements(name, attrs)
        return [(element, attr) for element in elements]

    @staticmethod
    def __get_depended_attribute(attrs):
        attr = (attr for attr, value in attrs.items() if value is True).__next__()
        return attr
