import resolver
import validators

class HTMLLExtractor(resolver.NameGenerator):
    __html_tag = {"img": ["src", "data-src"], "video": ["src", "poster"], "embed": ["src"],
                "source": ["src"], "audio": ["src"], "input": ["src"],
                "object": ["data", "codebase"], "track": ["src"]}

    def __init__(self, html_parser, http_client, url_res, dst: str, rel_dir=None):
        self.__html_parser = html_parser
        self.__client = http_client
        self.__url_res = url_res
        self.__dst = dst
        self.__rel_dir = rel_dir

    def html_resources(self):
        for tag, attributes in HTMLLExtractor.__html_tag.items():
            for attr in attributes:
                for element in self.__html_parser.elements(tag, attr):
                    try:
                        ref = element.get(attr)

                        if ref.lower().startswith("data:image"):
                            continue

                        uri = self.__url_res.resolve(ref)
                        name = super().gen_name("res", resolver.ext_from_url(uri))

                        self.__client.sync_download("nojs", uri, self.__dst + "/" + name)
                        element[attr] = self.__rel_dir + "/" + name if self.__rel_dir else name
                    except RuntimeWarning:
                        continue


    def html_frames(self):
        frames = list()
        for element in self.__html_parser.elements(["frame", "iframe"], "src"):
            try:
                ref = element.get("src")
                uri = self.__url_res.resolve(ref)
                frames.append((uri, element))
            except RuntimeWarning:
                continue

        return frames
