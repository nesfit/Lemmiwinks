
class CSSMigrator:
    def __init__(self, parser, http_client, destination, resolver):
        pass


class CCSInlineMigrator:
    def __init__(self, parser, http_client, destination, resolver):
        pass


class HTMLMigrator:
    def __init__(self, parser, http_client, destination, resolver):
        self._parser = parser
        self._http_client = http_client
        self._destination = destination
        self._resolver = resolver
        self._resources = dict()

    async def download_dependencies(self):
        pass


class JavaScriptInlineMigrator:
    def __init__(self, parser, http_client, destination, resolver):
        pass