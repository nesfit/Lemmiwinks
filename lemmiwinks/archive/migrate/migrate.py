import asyncio
import logging
import pathlib

import dependency_injector.providers as di_providers

from . import abstract
from . import container
import singleton


class SrcRegister(dict, metaclass=singleton.ThreadSafeSingleton):
    pass


class UpdateElement(abstract.UpdateEntity):
    def __init__(self, resolver, path_gen, client):
        self.__resolver = resolver
        self.__src_register = SrcRegister()
        super().__init__(client, path_gen, self.__src_register)

    def _get_url_from(self, entity, **kwargs):
        return self.__resolver.resolve(entity[kwargs["attr"]])

    def _update_entity(self, url, entity, **kwargs):
        entity[kwargs["attr"]] = self.__src_register.get(url).relpath


class UpdateToken(abstract.UpdateEntity):
    def __init__(self, resolver, path_gen, client):
        self.__resolver = resolver
        self.__src_register = SrcRegister()
        super().__init__(client, path_gen, self.__src_register)

    def _get_url_from(self, entity, **kwargs):
        return self.__resolver.resolve(entity.value)

    def _update_entity(self, url, entity, **kwargs):
        entity.value = self.__src_register.get(url).relpath


class CSSMigration(abstract.Migrate):
    def __init__(self, css_type, settings: abstract.MigrationSettings):
        self._css_type = css_type
        self._settings = settings

        self._src_register = SrcRegister()
        self._client = settings.http_client()

        self._token_updater = UpdateToken(css_type.resolver, css_type.path_gen, self._client)

    async def migrate(self):
        print(self._css_type.parser.import_tokens)
        tasks = [self._token_updater.update_entity(token)
                 for token in self._css_type.parser.url_tokens]

        tasks += [self._token_updater.update_recursive_entity(
            self.__migrate_recursive_source, token)
            for token in self._css_type.parser.import_tokens]

        await asyncio.gather(*tasks)

    async def __migrate_recursive_source(self, url):
        self._token_updater.register_path_for(url)
        response = await self._client.get_request(url)
        await self.__process_response(response)

    async def __process_response(self, response):
        if self._css_type.recursion_limit > 0:
            await self.__migrate_response_recursively(response)
        else:
            print(f"recursion {self._css_type.recursion_limit} save")
            self.__save_response(response)

    async def __migrate_response_recursively(self, response):
        path = self._src_register.get(response.requested_url).abspath

        css_file = CSSFileStylesheet(response, self._settings,
                                     path, self._css_type.recursion_limit - 1)

        print("tu som")
        css_migrate = CSSMigration(css_file, self._settings)

        await css_migrate.migrate()
        css_file.export()

    def __save_response(self, response):
        url = response.requested_url
        path = self._src_register.get(url).abspath

        with open(path, "wb") as fd:
            fd.write(response.content_descriptor.read())


class CSSFileStylesheet(abstract.EssentialPart):
    def __init__(self, data, settings, filepath, recursion_limit=3):
        self._filepath = filepath

        parser = settings.css_parser(data.content_descriptor)
        parser.parse_tokens()
        resolver = settings.resolver(data.accessed_url)
        essential_location = pathlib.Path(filepath).parent
        path_gen = settings.path_gen(essential_location, essential_location)

        super().__init__(parser, resolver, path_gen,essential_location,
                         essential_location, recursion_limit)

    def export(self):
        with open(self._filepath, "w") as fd:
            fd.write(self.parser.export())


class CSSInlineStylesheet(abstract.EssentialPart):
    def __init__(self, data, url, essential_location, res_location, settings, recursion_limit=3):
        parser = settings.css_parser(data)
        parser.parse_tokens()
        resolver = settings.resolver(url)
        path_gen = settings.path_gen(res_location, essential_location)

        super().__init__(parser, resolver, path_gen, essential_location,
                         res_location, recursion_limit)

    def export(self):
        return self.parser.export()


class CSSDeclaration(abstract.EssentialPart):
    def __init__(self, data, url, essential_location, res_location, settings, recursion_limit=3):
        parser = settings.css_parser(data, declaration=True)
        parser.parse_tokens()
        resolver = settings.resolver(url)
        path_gen = settings.path_gen(res_location, essential_location)

        super().__init__(parser, resolver, path_gen, essential_location,
                         res_location, recursion_limit)

    def export(self):
        return self.parser.export()


class CSSContainer:
    def __init__(self, url, essential_location, res_location, settings):
        self._url = url
        self._res_location = res_location
        self._essential_location = essential_location
        self._settings = settings

    @property
    def css_file(self):
        return di_providers.Factory(CSSFileStylesheet, settings=self._settings)

    @property
    def css_inline(self):
        return di_providers.Factory(CSSInlineStylesheet, url=self._url,
                                    essential_location=self._essential_location,
                                    res_location=self._res_location,
                                    settings=self._settings)

    @property
    def css_declaration(self):
        return di_providers.Factory(CSSDeclaration, url=self._url,
                                    essential_location=self._essential_location,
                                    res_location=self._res_location,
                                    settings=self._settings)


class HTMLMigration:
    def __init__(self, index_file, settings):
        self._index_file = index_file
        self._settings = settings

        self._client = settings.http_client()

        self._element_updater = UpdateElement(
            index_file.resolver, index_file.path_gen, self._client)

        self._css_container = CSSContainer(index_file.resolver.base,
                                           index_file.essential_location,
                                           index_file.resource_location,
                                           settings)

        self._html_filter = container.HTMLFilter(index_file.parser)
        self._src_register = SrcRegister()

    async def migrate(self):
        await self._migrate_html_elements_sources()
        await self._migrate_css_file_stylesheet()

    async def _migrate_html_elements_sources(self):
        tasks = [self._element_updater.update_entity(element, attr=attr)
                 for element, attr in self._html_filter.elements]

        await asyncio.gather(*tasks)

    async def _migrate_css_file_stylesheet(self):
        tasks = [self._element_updater.update_recursive_entity(
            self.__migrate_css_file, element, attr=attr)
            for element, attr in self._html_filter.stylesheet_link]

        await asyncio.gather(*tasks)

    async def __migrate_css_file(self, url):
        self._element_updater.register_path_for(url)
        response = await self._client.get_request(url)
        path = self._src_register.get(url).abspath
        css_file = self._css_container.css_file(data=response, filepath=path)
        await CSSMigration(css_file, self._settings).migrate()
        css_file.export()



class IndexFileMigration:
    def __init__(self, response,
                 settings: abstract.MigrationSettings,
                 filepath: str):
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
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
    def __init__(self, response, filepath, res_location, settings, recursion_limit=3):
        self._filepath = filepath
        self._settings = settings

        essential_location = pathlib.Path(filepath).parent
        parser = settings.html_parser(response.content_descriptor)
        resolver = self.__init_resolver(response.accessed_url)
        path_gen = settings.path_gen(res_location, essential_location)

        super().__init__(parser, resolver, path_gen, essential_location, res_location, recursion_limit)

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

    def export(self):
        with open(self._filepath, "wb") as fd:
            fd.write(self.parser.export())

