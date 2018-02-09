class ElementFilterRules:
    __element_sources = {"img": [{"src": True}, {"data-src": True}],
                         "video": [{"src": True}, {"poster": True}],
                         "embed": [{"src": True}],
                         "source": [{"src": True}],
                         "audio": [{"src": True}],
                         "input": [{"src": True}],
                         "object": [{"data": True}, {"codebase": True}],
                         "track": [{"src": True}]}
    __stylesheet_link = {"link": [{"href": True, "rel": "stylesheet"}]}
    __js_script = {"script": [{"src": True}]}
    __script = {"script": [None]}
    __style = {"style": [None]}
    __description_style = {True: [{"style": True}]}
    __frames = {"frame": [{"src": True}],
                "iframe": [{"src": True}]}
    __events = ["onafterprint", "onbeforeprint", "onbeforeunload", "onerror",
                "onhashchange", "onload", "onmessage", "onoffline", "ononline",
                "onpagehide", "onpageshow", "onpopstate", "onresize",
                "onstorage", "onunload", "onblur", "onchange", "oncontextmenu",
                "onfocus", "oninput", "oninvalid", "onreset", "onsearch",
                "onselect", "onsubmit", "onkeydown", "onkeypress", "onkeyup",
                "onclick", "ondblclick", "onmousedown", "onmousemove",
                "onmouseout", "onmouseover", "onmouseup", "onmousewheel",
                "onwheel", "ondrag", "ondragend", "ondragenter", "ondragleave",
                "ondragover", "ondragstart", "ondrop", "onscroll", "oncopy",
                "oncut", "onpaste", "onabort", "oncanplay", "oncanplaythrough",
                "oncuechange", "ondurationchange", "onemptied", "onended",
                "onerror", "onloadeddata", "onloadedmetadata", "onloadstart",
                "onpause", "onplay", "onplaying", "onprogress", "onratechange",
                "onseeked", "onseeking", "onstalled", "onsuspend",
                "ontimeupdate", "onvolumechange", "onwaiting", "onshow",
                "ontoggle"]

    @property
    def elements(self):
        return self.__flatten(ElementFilterRules.__element_sources)

    @property
    def stylesheet_link(self):
        return self.__flatten(ElementFilterRules.__stylesheet_link)

    @property
    def js_script(self):
        return self.__flatten(ElementFilterRules.__js_script)

    @property
    def script(self):
        return self.__flatten(ElementFilterRules.__script)

    @property
    def events(self):
        return self.__format_events(ElementFilterRules.__events)

    @property
    def style(self):
        return self.__flatten(ElementFilterRules.__style)

    @property
    def description_style(self):
        return self.__flatten(ElementFilterRules.__description_style)

    @property
    def frames(self):
        return self.__flatten(ElementFilterRules.__frames)

    @staticmethod
    def __flatten(rules):
        flatten_rules = [(element_name, attr_dict) for element_name, attr_list in rules.items()
                         for attr_dict in attr_list]
        return flatten_rules

    @staticmethod
    def __format_events(event_list):
        formatted_rules = [(True, {attr_name: True}) for attr_name in event_list]
        return formatted_rules


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

    @property
    def js_script(self):
        return self.__get_element_list_from(self._filter_rules.js_script)

    @property
    def script(self):
        return self.__get_element_list_from(self._filter_rules.script)

    @property
    def elements_event(self):
        return self.__get_element_list_from(self._filter_rules.events)

    @property
    def style(self):
        return self.__get_element_list_from(self._filter_rules.style)

    @property
    def description_style(self):
        return self.__get_element_list_from(self._filter_rules.description_style)

    @property
    def frames(self):
        return self.__get_element_list_from(self._filter_rules.frames)

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
        try:
            attr = (attr for attr, value in attrs.items() if value is True).__next__()
        except Exception:
            attr = None
        finally:
            return attr
