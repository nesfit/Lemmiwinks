import asyncio
import logging
import pathlib
import urllib.parse

from . import abstract
from . import container
import httplib
import singleton


class SrcRegister(dict, metaclass=singleton.ThreadSafeSingleton):
    pass


class UpdateElement(abstract.UpdateEntity):
    def __init__(self, resolver, path_gen, client):
        self.__resolver = resolver
        self.__src_register = SrcRegister()
        downloader = httplib.provider.HTTPClientDownloader(client)
        super().__init__(downloader, path_gen, self.__src_register)

    def _get_url_from(self, entity, **kwargs):
        return self.__resolver.resolve(entity[kwargs["attr"]])

    def _update_entity(self, url, entity, **kwargs):
        entity[kwargs["attr"]] = self.__src_register.get(url).relpath


class UpdateToken(abstract.UpdateEntity):
    def __init__(self, resolver, path_gen, client):
        self.__resolver = resolver
        self.__src_register = SrcRegister()
        downloader = httplib.provider.HTTPClientDownloader(client)
        super().__init__(downloader, path_gen, self.__src_register)

    def _get_url_from(self, entity, **kwargs):
        return self.__resolver.resolve(entity.value)

    def _update_entity(self, url, entity, **kwargs):
        entity.value = self.__src_register.get(url).relpath


class CSSMigration(abstract.UpdateRecursiveEntity, abstract.Migrate):
    def __init__(self, css_type, settings: abstract.MigrationSettings):
        self._css_type = css_type
        self._settings = settings

        self._src_register = SrcRegister()
        client = self._settings.http_client()

        self._token_updater = UpdateToken(self._css_type.resolver,
                                          self._css_type.path_gen, client)

        super().__init__(client, self._css_type.path_gen, self._src_register)

    async def migrate(self):
        tasks = [self._token_updater.update_entity(token)
                 for token in self._css_type.parser.url_tokens]

        tasks += [self._update_recursive_entity(token)
                  for token in self._css_type.parser.import_tokens]

        await asyncio.gather(*tasks)

    def _get_url_from(self, entity, **kwargs):
        return self._css_type.resolver.resolve(entity.value)

    async def _process_response(self, response):
        if self._css_type.recursion_limit > 0:
            await self.__migrate_response_recursively(response)
        else:
            self.__save_response(response)

    async def __migrate_response_recursively(self, response):
        path = self._src_register.get(response.requested_url).abspath

        css_file = CSSFileStylesheet(response.content_descriptor, self._settings,
                                     path, self._css_type.recursion_limit - 1)

        css_migrate = CSSMigration(css_file, self._settings)

        await css_migrate.migrate()
        css_file.export()

    def __save_response(self, response):
        url = response.requested_url
        path = self._src_register.get(url).abspath

        with open(path, "wb") as fd:
            fd.write(response.content_descriptor.read())

    def _update_entity(self, url, entity, **kwargs):
        entity.value = self._src_register.get(url).relpath


class CSSFileStylesheet(abstract.EssentialPart):
    def __init__(self, data, settings, filepath, recursion_limit=3):
        self._filepath = filepath

        url = data.accessed_url
        dir_dst = pathlib.Path(filepath).parent
        parser = settings.css_parser(data.content_descriptor)
        super().__init__(parser, url, dir_dst, dir_dst, settings, recursion_limit)

    def export(self):
        with open(self._filepath, "w") as fd:
            fd.write(self.parser.export())


class CSSInlineStylesheet(abstract.EssentialPart):
    def __init__(self, data, url, dir_dst, suffix_path, settings, recursion_limit=3):
        parser = settings.css_parser(data)
        super().__init__(parser, url, dir_dst, suffix_path, settings, recursion_limit)

    def export(self):
        return self.parser.export()


class CSSDeclaration(abstract.EssentialPart):
    def __init__(self, data, url, dir_dst, suffix_path, settings, recursion_limit=3):
        parser = settings.css_parser(data, declaration=True)
        super().__init__(parser, url, dir_dst, suffix_path, settings, recursion_limit)

    def export(self):
        return self.parser.export()


class IndexFileMigration:
    def __init__(self, response,
                 settings: abstract.MigrationSettings,
                 filepath: str):
        self._logger  = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._settings = settings
        self._src_register = SrcRegister()

        self._parser = settings.html_parser(response.content_descriptor)
        self._html_filter = container.HTMLFilter(self._parser)
        self._filepath = filepath
        self._base_dst = pathlib.Path(filepath).parent
        self._resources_dst = pathlib.Path(self._base_dst).joinpath("index_files")
        self._path_gen = settings.path_gen(self._resources_dst, self._base_dst)
        self._client = settings.http_client()
        self._resolver = self.__init_resolver(response.accessed_url)
        self._element_updater = UpdateElement(self._resolver, self._path_gen, self._client)

        # remove base tag
        del self._parser.base

    def __init_resolver(self, url):
        try:
            resolver = self._settings.resolver(url)
            resolver.base = resolver.resolve(self._parser.base["href"])
        except Exception as e:
            self._logger.info(f"{e}")
            self._logger.info(f"Base url was {url}")
            self._logger.info(f"Base tag is {self._parser.base}")
        finally:
            return resolver

    async def migrate_html_elements_sources(self):
        tasks = [self._element_updater.update_entity(element, attr=attr)
                 for element, attr in self._html_filter.elements]
        await asyncio.gather(*tasks)

    async def migrate_css_stylesheets(self):
        for element, attr in self._html_filter.stylesheet_link:
            url = self._resolver.resolve(element[attr])
            response = await self._client.get_request(url)
            path = self._path_gen.generate_filepath_with(".css")
            css_file = CSSFileStylesheet(response, self._settings, path.abspath)
            migrator = CSSMigration(css_file, self._settings)
            await migrator.migrate()
            css_file.export()
            element[attr] = path.relpath

    def save(self):
        with open(self._filepath, "wb") as fd:
            fd.write(self._parser.export())


class IndexFile(abstract.EssentialPart):
    def __init__(self, response, filepath, resources_dst, settings, recursion_limit=3):
        self._filepath = filepath
        base_dst = pathlib.Path(filepath).parent
        parser =  settings.html_parser(response.content_descriptor)

        super().__init__(parser, base_dst, resources_dst, settings, recursion_limit)

    def export(self):
        with open(self._filepath, "w") as fd:
            fd.write(self.parser.export())


class HTMLMigrate(abstract.UpdateRecursiveEntity, abstract.Migrate):
    def __init__(self, ):
        pass

    def migrate(self):
        pass

