class ElementFilter:
    _element_sources = {"img": [{"src": True}, {"data-src": True}],
                        "video": [{"src": True}, {"poster": True}],
                        "embed": [{"src": True}],
                        "source": [{"src": True}],
                        "audio": [{"src": True}],
                        "input": [{"src": True}],
                        "object": [{"data": True}, {"codebase": True}],
                        "track": [{"src": True}]}
    _link_stylesheet = {"link": [{"href": True, "rel": "stylesheet"}]}
    _js_style = {"script": [{"src": True}]}

    @property
    def element(self):
        return self.__flatten(ElementFilter._element_sources)

    @property
    def links_stylesheets(self):
        return self.__flatten(ElementFilter._link_stylesheet)

    @property
    def js_style(self):
        return self.__flatten(ElementFilter._js_style)

    @staticmethod
    def __flatten(rules):
        flatten_rules = [(name, attr) for name, attrs in rules.items() for attr in attrs]
        return flatten_rules
