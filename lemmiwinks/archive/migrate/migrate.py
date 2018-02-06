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
        tasks = [self._token_updater.update_entity(token)
                 for token in self._css_type.parser.url_tokens]

        tasks += [self._token_updater.update_recursive_entity(
            self.__migrate_recursive_source, token)
            for token in self._css_type.parser.import_tokens]

        await asyncio.gather(*tasks)

    def update_url_tokens(self):
        tasks = [self._token_updater.update_entity(token)
                 for token in self._css_type.parser.url_tokens]
        return tasks

    def update_import_tokens(self):
        tasks = [self._token_updater.update_recursive_entity(
            self.__migrate_recursive_source, token)
            for token in self._css_type.parser.import_tokens]
        return tasks

    async def __migrate_recursive_source(self, url):
        self._token_updater.register_path_for(url)
        response = await self._client.get_request(url)
        await self.__process_response(response)

    async def __process_response(self, response):
        if self._css_type.recursion_limit > 0:
            await self.__migrate_response_recursively(response)
        else:
            self.__save_response(response)

    async def __migrate_response_recursively(self, response):
        path = self._src_register.get(response.requested_url).abspath

        css_file = CSSStylesheetFile(response, self._settings,
                                     path, self._css_type.recursion_limit - 1)

        css_migrate = CSSMigration(css_file, self._settings)

        await css_migrate.migrate()
        css_file.export()

    def __save_response(self, response):
        url = response.requested_url
        path = self._src_register.get(url).abspath

        with open(path, "wb") as fd:
            fd.write(response.content_descriptor.read())


class CSSStylesheetFile(abstract.EssentialPart):
    def __init__(self, data, settings, filepath, recursion_limit=3):
        self._filepath = filepath

        parser = settings.css_parser(data.content_descriptor)
        parser.parse_tokens()
        resolver = settings.resolver(data.accessed_url)
        essential_location = pathlib.Path(filepath).parent
        path_gen = settings.path_gen(essential_location, essential_location)

        super().__init__(parser, resolver, path_gen,essential_location,
                         essential_location, recursion_limit)

        self._css_migration = CSSMigration(self, settings)

    async def migrate(self):
        tasks = self._css_migration.update_url_tokens()
        tasks += self._css_migration.update_import_tokens()

        await asyncio.gather(*tasks)

    def export(self):
        with open(self._filepath, "w") as fd:
            fd.write(self.parser.export())


class CSSInlineStylesheet(abstract.EssentialPart, abstract.Migrate):
    def __init__(self, data, url, essential_location, res_location, settings, recursion_limit=3):
        parser = settings.css_parser(data)
        parser.parse_tokens()
        resolver = settings.resolver(url)
        path_gen = settings.path_gen(res_location, essential_location)

        super().__init__(parser, resolver, path_gen, essential_location,
                         res_location, recursion_limit)

        self._css_migration = CSSMigration(self, settings)

    async def migrate(self):
        tasks = self._css_migration.update_url_tokens()
        tasks += self._css_migration.update_import_tokens()

        await asyncio.gather(*tasks)

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

        self._css_migration = CSSMigration(self, settings)

    async def migrate(self):
        tasks = self._css_migration.update_url_tokens()
        tasks += self._css_migration.update_import_tokens()

        await asyncio.gather(*tasks)

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
        return di_providers.Factory(CSSStylesheetFile, settings=self._settings)

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

    def migrate_html_elements_sources(self):
        tasks = [self._element_updater.update_entity(element, attr=attr)
                 for element, attr in self._html_filter.elements]

        return tasks

    def migrate_css_file_stylesheet(self):
        tasks = [self._element_updater.update_recursive_entity(
            self.__migrate_css_file, element, attr=attr)
            for element, attr in self._html_filter.stylesheet_link]

        return tasks

    async def __migrate_css_file(self, url):
        self._element_updater.register_path_for(url)

        response = await self._client.get_request(url)
        path = self._src_register.get(url).abspath

        css_file = self._css_container.css_file(data=response, filepath=path)
        await css_file.migrate()
        css_file.export()

    def migrate_css_style(self):
        tasks = [self.__update_element_style_attribute(element)
                 for element, _ in self._html_filter.style]

        return tasks

    @abstract._task
    async def __update_element_style_attribute(self, element):
        css_style = self._css_container.css_inline(data=element.string)
        await css_style.migrate()
        element.string = css_style.export()

    def migrate_css_declaration(self):
        tasks = [self.__update_element_style_attribute(element, attr)
                 for element, attr in self._html_filter.description_style]

        return tasks

    @abstract._task
    async def __update_element_style_attribute(self, element, attr):
        css_declaration = self._css_container.css_declaration(data=element[attr])
        await css_declaration.migrate()
        element[attr] = css_declaration.export()


class HTMLMigrationWithJS(HTMLMigration):
    def __init__(self, index_file, settings):
        super().__init__(index_file, settings)

    def migrate_javascript(self):
        tasks = [self._element_updater.update_entity(element, attr=attr)
                 for element, attr in self._html_filter.js_style]

        return tasks

    def migrate_frames(self):
        tasks = [self._element_updater.update_recursive_entity(
            self.__migrate_frames, element, attr=attr)
            for element, attr in self._html_filter.frames]

        return tasks

    async def __migrate_frames(self, url):
        self._element_updater.register_path_for(url)
        response = await self._client.get_request(url)
        path = self._src_register.get(url).abspath
        html_file = IndexFile(response, path, self._index_file.resource_location,
                              self._settings, self._index_file.recuriosn_limit-1)
        await html_file.migrate()
        html_file.export()


class IndexFile(abstract.EssentialPart, abstract.Migrate):
    def __init__(self, response, filepath, res_location, settings, recursion_limit=3):
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._filepath = filepath
        self._settings = settings

        essential_location = pathlib.Path(filepath).parent
        parser = settings.html_parser(response.content_descriptor)
        resolver = self.__init_resolver(response.accessed_url)
        path_gen = settings.path_gen(res_location, essential_location)

        super().__init__(parser, resolver, path_gen,
                         essential_location, res_location, recursion_limit)

        self._html_migration = HTMLMigrationWithJS(self, settings)
        del self.parser.base

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

    async def migrate(self):
        tasks = self._html_migration.migrate_css_declaration()
        tasks += self._html_migration.migrate_css_style()
        tasks += self._html_migration.migrate_html_elements_sources()
        tasks += self._html_migration.migrate_css_file_stylesheet()
        tasks += self._html_migration.migrate_frames()
        tasks += self._html_migration.migrate_javascript()

        await asyncio.gather(*tasks)

    def export(self):
        with open(self._filepath, "wb") as fd:
            fd.write(self.parser.export())



