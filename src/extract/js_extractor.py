import resolver
class JSExtractor(resolver.NameGenerator):
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

    def __init__(self, html_parser, http_client, dst: str, rel_dir=None):
        self.__html_parser = html_parser
        self.__client = http_client
        self.__dst = dst
        self.__rel_dir = rel_dir

    def js_script(self):
        for e in self.__html_parser.elements("script"):
            try:
                e.string = "<!-- deleted by script -->"
                name = super().gen_name("js", ".js")


                with open(self.__dst + "/" + name, "w") as fd:
                    fd.write("/* removed by script */")

                e["src"] = self.__rel_dir + "/" + name if self.__rel_dir else name
            except Exception:
                continue

    def js_events(self):
        for attr in JSExtractor.__events:
            for e in self.__html_parser.elements(True, attr):
                e[attr] = None
