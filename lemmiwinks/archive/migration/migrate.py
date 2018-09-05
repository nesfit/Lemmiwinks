import asyncio
import logging
import urllib.parse
import pathlib

import dependency_injector.providers as di_provider

import lemmiwinks.httplib as httplib
import lemmiwinks.singleton as singleton
import lemmiwinks.taskwrapper as taskwrapper

from . import abstract
from . import container


class SrcRegister(dict, metaclass=singleton.ThreadSafeSingleton):
    pass


class UpdateTokenValue(abstract.UpdateEntity):
    def __init__(self, resolver, path_gen):
        super().__init__()
        self.__resolver = resolver
        self.__path_gen = path_gen

    def _get_data_from(self, entity, **kwargs):
        return self.__resolver.resolve(entity.value)

    def _update_entity(self, data, entity, **kwargs):
        entity.value = self.__path_gen.get_relpath_from(data)


class UpdateElementString(abstract.UpdateEntity):
    def __init__(self):
        super().__init__()

    def _get_data_from(self, entity, **kwargs):
        return entity.string

    def _update_entity(self, data, entity, **kwargs):
        entity.string = data


class UpdateElementAttribute(abstract.UpdateEntity):
    def __init__(self):
        super().__init__()

    def _get_data_from(self, entity, **kwargs):
        return entity[kwargs["attr"]]

    def _update_entity(self, data, entity, **kwargs):
        entity[kwargs["attr"]] = data


class UpdateElementAttributeSource(abstract.UpdateEntity):
    def __init__(self, resolver, path_gen):
        super().__init__()
        self.__resolver = resolver
        self.__path_gen = path_gen

    def _get_data_from(self, entity, **kwargs):
        return self.__resolver.resolve(entity[kwargs["attr"]])

    def _update_entity(self, data, entity, **kwargs):
        entity[kwargs["attr"]] = self.__path_gen.get_relpath_from(data)


class DownloadHandler(abstract.DataHandler):
    def __init__(self, entity_property, settings):
        self.__logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.__downloader = httplib.provider.HTTPClientDownloader(settings.http_client())
        self.__path_gen = entity_property.path_gen
        self.__src_register = SrcRegister()

    async def process(self, url):
        try:
            if url not in self.__src_register.keys():
                await self.__download(url)

            path = self.__src_register.get(url)
        except Exception as e:
            self.__log_error(e=e, url=url)
            return ""
        else:
            return path

    def __log_error(self, **kwargs):
        self.__logger.error(f'url: {kwargs["url"]}')
        self.__logger.exception(kwargs["e"])

    async def __download(self, url):
        try:
            self.__register_path_for_url(url)
            path = self.__src_register.get(url)
            await self.__downloader.download(url, path)
        except Exception as e:
            self.__log_error(e=e, url=url)

    def __register_path_for_url(self, url):
        url_path = urllib.parse.urlparse(url).path
        path = self.__path_gen.generate_filepath_with(pathlib.Path(url_path).suffix)
        self.__src_register.update({url: path})


class _RecursiveEntityHandler(abstract.DataHandler):
    """
    Abstract class used for migration of recursive file such as CSS or HTML.
    It implements generic concrete implementation expect of methods
    _get_response_from(self, url), _register_path_for(self, url), and
    _process_entity_recursively_from(self, response).

    The _get_response_from(self, url) method should implement get request
    on server specified by url. It returns response object.

    The _register_path_for(self, url) method generate filepath for new
    resources with file extension. the url and path are added to src_register
    dictionary.

    The _process_entity_recursively_from(self, response) contains of recursive
    call of CSS or HTML migration.
    """

    def __init__(self, recursion_limit):
        self.__logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        self._recursion_limit = recursion_limit
        self._src_register = SrcRegister()

    async def process(self, url):
        try:
            if url not in self._src_register.keys():
                await self.__migrate_entity_from(url)
        except Exception as e:
            self.__log_error(e=e, url=url)
        finally:
            return self._src_register.get(url)

    async def __migrate_entity_from(self, url):
        self._register_path_for(url)
        response = await self._get_response_from(url)
        self._update_path_for(url, response.accessed_url, response.requested_url)
        await self.__process_response(response)

    def __log_error(self, **kwargs):
        self.__logger.exception(kwargs["e"])
        self.__logger.error(kwargs["e"])
        self.__logger.error(f'url: {kwargs["url"]}')

    def _register_path_for(self, url):
        raise NotImplemented

    def _update_path_for(self, urlkey, accessed_url, requested_url):
        path = self._src_register.get(urlkey)
        self._src_register.update({accessed_url: path})
        self._src_register.update({requested_url: path})

    async def _get_response_from(self, url):
        raise NotImplemented

    async def __process_response(self, response):
        if self._recursion_limit > 0:
            await self._process_entity_recursively_from(response)
        else:
            self.__save_response(response)

    async def _process_entity_recursively_from(self, response):
        raise NotImplemented

    def __save_response(self, response):
        url = response.requested_url
        path = self._src_register.get(url)

        with open(path, "wb") as fd:
            fd.write(response.content_descriptor.read())


class CSSFileHandler(_RecursiveEntityHandler):
    def __init__(self, entity_property, settings):
        super().__init__(entity_property.recursion_limit)
        self.__client = settings.http_client()
        self.__path_gen = entity_property.path_gen
        self.__settings = settings

    def _register_path_for(self, url):
        path = self.__path_gen.generate_filepath_with(".css")
        self._src_register.update({url: path})

    async def _get_response_from(self, url):
        return await self.__client.get_request(url)

    async def _process_entity_recursively_from(self, response):
        url = response.requested_url
        path = self._src_register.get(url)

        css_file = CssFile(response, path,
                           self.__settings, self._recursion_limit - 1)

        await css_file.migrate_external_sources()
        css_file.export()


class _HTMLEntityHandler(_RecursiveEntityHandler):
    def __init__(self, entity_property):
        super().__init__(entity_property.recursion_limit)
        self.__path_gen = entity_property.path_gen

    def _register_path_for(self, url):
        path = self.__path_gen.generate_filepath_with(".html")
        self._src_register.update({url: path})


class HTMLFileWithJsExecutionHandler(_HTMLEntityHandler):
    def __init__(self, entity_property, settings):
        super().__init__(entity_property)
        self.__http_js_pool = settings.http_js_pool()
        self.__resource_location = entity_property.resource_location
        self.__settings = settings

    async def _get_response_from(self, url):
        async with self.__http_js_pool.get_client() as client:
            response = await client.get_request(url)

        return response

    async def _process_entity_recursively_from(self, response):
        url = response.accessed_url
        path = self._src_register.get(url)

        index_file = IndexFileContainer.index_file_with_js_execution(
            response=response,
            filepath=path,
            res_location=self.__resource_location,
            settings=self.__settings,
            recursion_limit=self._recursion_limit)

        await index_file.migrate_external_sources()
        index_file.export()


class HTMLFileHandler(_HTMLEntityHandler):
    def __init__(self, entity_property, settings):
        super().__init__(entity_property)
        self.__client = settings.http_client()
        self.__resource_location = entity_property.resource_location
        self.__settings = settings

    async def _get_response_from(self, url):
        return await self.__client.get_request(url)

    async def _process_entity_recursively_from(self, response):
        url = response.requested_url
        path = self._src_register.get(url)

        index_file = IndexFileContainer.index_file(
            response=response,
            filepath=path,
            res_location=self.__resource_location,
            settings=self.__settings,
            recursion_limit=self._recursion_limit)

        await index_file.migrate_external_sources()
        index_file.export()


class CssStyleHandler(abstract.DataHandler):
    def __init__(self, entity_property, settings):
        self.__url = entity_property.resolver.base
        self.__style_location = entity_property.entity_location
        self.__resource_location = entity_property.resource_location
        self.__recursion_limit = entity_property.recursion_limit
        self.__settings = settings

    async def process(self, data):
        css_style = CSSStyle(data, self.__url, self.__style_location,
                             self.__resource_location, self.__settings,
                             self.__recursion_limit)

        await css_style.migrate_external_sources()

        return css_style.export()


class CssDeclarationHandler(abstract.DataHandler):
    def __init__(self, entity_property, settings):
        self.__url = entity_property.resolver.base
        self.__declaration_location = entity_property.entity_location
        self.__resource_location = entity_property.resource_location
        self.__recursion_limit = entity_property.recursion_limit
        self.__settings = settings

    async def process(self, data):
        css_declaration = CSSDeclaration(data, self.__url, self.__declaration_location,
                                         self.__resource_location, self.__settings,
                                         self.__recursion_limit)

        await css_declaration.migrate_external_sources()

        return css_declaration.export()


class JSFileHandler(abstract.DataHandler):
    def __init__(self, entity_property):
        self.__path_gen = entity_property.path_gen

    async def process(self, data):
        path = self.__path_gen.generate_filepath_with(".js")
        pathlib.Path(path).touch()
        return path


class InlineJSHandler(abstract.DataHandler):
    def __init__(self):
        pass

    async def process(self, data):
        return ""


class _BaseElementTaskContainer:
    def __init__(self, entity_property, settings):
        self._element_string_updater = UpdateElementString()
        self._element_attr_updater = UpdateElementAttribute()
        self._element_src_attr_updater = UpdateElementAttributeSource(
            entity_property.resolver, entity_property.path_gen)

        self._download_source = DownloadHandler(entity_property, settings)
        self._css_file_handler = CSSFileHandler(entity_property, settings)
        self._css_style_handler = CssStyleHandler(entity_property, settings)
        self._css_declaration_handler = CssDeclarationHandler(entity_property, settings)

    def update_source_attr(self, element, attr):
        return self._element_src_attr_updater.update_entity(
            self._download_source, element, attr=attr)

    def update_link_stylesheet_ref(self, element, attr):
        return self._element_src_attr_updater.update_entity(
            self._css_file_handler, element, attr=attr)

    def update_css_style(self, element):
        return self._element_string_updater.update_entity(
            self._css_style_handler, element)

    def update_css_declaration(self, element, attr):
        return self._element_attr_updater.update_entity(
            self._css_declaration_handler, element, attr=attr)


class ElementTaskContainer(_BaseElementTaskContainer):
    def __init__(self, entity_property, settings):
        super().__init__(entity_property, settings)

        self._html_file_handler = HTMLFileHandler(entity_property, settings)

    def update_iframe_source(self, element, attr):
        return self._element_src_attr_updater.update_entity(
            self._html_file_handler, element, attr=attr)


class ElementTaskContainerWithJsExecution(_BaseElementTaskContainer):
    def __init__(self, entity_property, settings):
        super().__init__(entity_property, settings)

        self._js_file_handler = JSFileHandler(entity_property)
        self._inline_js_handler = InlineJSHandler()
        self._html_file_handler = HTMLFileWithJsExecutionHandler(entity_property, settings)

    def update_script_source(self, element, attr):
        return self._element_src_attr_updater.update_entity(
            self._js_file_handler, element, attr=attr)

    def update_inline_script(self, element):
        return self._element_string_updater.update_entity(
            self._inline_js_handler, element)

    def update_event_attr(self, element, attr):
        return self._element_attr_updater.update_entity(
            self._inline_js_handler, element, attr=attr)

    def update_iframe_source(self, element, attr):
        return self._element_src_attr_updater.update_entity(
            self._html_file_handler, element, attr=attr)


class TokenTaskContainer:
    def __init__(self, entity_property, settings):
        self.__token_value_updater = UpdateTokenValue(
            entity_property.resolver, entity_property.path_gen)

        self.__download_token = DownloadHandler(entity_property, settings)
        self.__css_file_handler = CSSFileHandler(entity_property, settings)

    def update_url_token(self, token):
        return self.__token_value_updater.update_entity(self.__download_token, token)

    def update_import_token(self, token):
        return self.__token_value_updater.update_entity(self.__css_file_handler, token)


class CSSMigration(abstract.BaseMigration):
    def __init__(self, css_entity, settings: abstract.MigrationSettings):
        self.__css_entity = css_entity
        self.__task = TokenTaskContainer(css_entity, settings)

    async def migrate(self):
        await asyncio.gather(self.__update_url_tokens(),
                             self.__update_import_tokens())

    @taskwrapper.task
    async def __update_url_tokens(self):
        tasks = [self.__task.update_url_token(token)
                 for token in self.__css_entity.parser.url_tokens]
        await asyncio.gather(*tasks)

    @taskwrapper.task
    async def __update_import_tokens(self):
        tasks = [self.__task.update_import_token(token)
                 for token in self.__css_entity.parser.import_tokens]
        await asyncio.gather(*tasks)


class _BaseHTMLMigration:
    def __init__(self, index_entity, task):
        self._html_filter = container.HTMLFilter(index_entity.parser)
        self._task = task

    @taskwrapper.task
    async def _migrate_html_elements_sources(self):
        tasks = [self._task.update_source_attr(element, attr)
                 for element, attr in self._html_filter.elements]

        await asyncio.gather(*tasks)

    @taskwrapper.task
    async def _migrate_css_file(self):
        tasks = [self._task.update_link_stylesheet_ref(element, attr)
                 for element, attr in self._html_filter.stylesheet_link]

        await asyncio.gather(*tasks)

    @taskwrapper.task
    async def _migrate_css_style(self):
        tasks = [self._task.update_css_style(element)
                 for element, _ in self._html_filter.style]

        await asyncio.gather(*tasks)

    @taskwrapper.task
    async def _migrate_css_declaration(self):
        tasks = [self._task.update_css_declaration(element, attr)
                 for element, attr in self._html_filter.description_style]

        await asyncio.gather(*tasks)

    @taskwrapper.task
    async def _migrate_iframes(self):
        tasks = [self._task.update_iframe_source(element, attr)
                 for element, attr in self._html_filter.frames]

        await asyncio.gather(*tasks)


class HTMLMigration(_BaseHTMLMigration, abstract.BaseMigration):
    def __init__(self, index_entity, settings):
        task = ElementTaskContainer(index_entity, settings)
        super().__init__(index_entity, task)

    async def migrate(self):
        await asyncio.gather(self._migrate_html_elements_sources(),
                             self._migrate_css_file(),
                             self._migrate_css_style(),
                             self._migrate_css_declaration(),
                             self._migrate_script_source(),
                             self._migrate_iframes())

    @taskwrapper.task
    async def _migrate_script_source(self):
        tasks = [self._task.update_source_attr(element, attr)
                 for element, attr in self._html_filter.js_script]

        await asyncio.gather(*tasks)


class HTMLMigrationWithJSExecution(_BaseHTMLMigration, abstract.BaseMigration):
    def __init__(self, index_entity, settings):
        task = ElementTaskContainerWithJsExecution(index_entity, settings)
        super().__init__(index_entity, task)

    async def migrate(self):
        await asyncio.gather(self._migrate_html_elements_sources(),
                             self._migrate_css_file(),
                             self._migrate_css_style(),
                             self._migrate_css_declaration(),
                             self._migrate_script_source(),
                             self._migrate_js_events(),
                             self._migrate_inline_script(),
                             self._migrate_iframes())

    @taskwrapper.task
    async def _migrate_script_source(self):
        tasks = [self._task.update_script_source(element, attr)
                 for element, attr in self._html_filter.js_script]

        await asyncio.gather(*tasks)

    @taskwrapper.task
    async def _migrate_js_events(self):
        tasks = [self._task.update_event_attr(element, attr)
                 for element, attr in self._html_filter.elements_event]

        await asyncio.gather(*tasks)

    @taskwrapper.task
    async def _migrate_inline_script(self):
        tasks = [self._task.update_inline_script(element)
                 for element, _ in self._html_filter.script]

        await asyncio.gather(*tasks)


class CssFile(abstract.BaseEntity):
    def __init__(self, response, filepath, settings, recursion_limit=3):
        self._filepath = filepath

        parser = settings.css_parser(response.content_descriptor)
        parser.parse_tokens()

        resolver = settings.resolver(response.accessed_url)
        essential_location = pathlib.Path(filepath).parent
        path_gen = settings.path_gen(essential_location, essential_location)

        super().__init__(parser, resolver, path_gen, essential_location,
                         essential_location, recursion_limit)

        self._css_migration = CSSMigration(self, settings)

    async def migrate_external_sources(self):
        await self._css_migration.migrate()

    def export(self):
        with open(self._filepath, "w") as fd:
            fd.write(self.parser.export())


class CSSStyle(abstract.BaseEntity):
    def __init__(self, data, url, style_location, resource_location,
                 settings, recursion_limit=3):
        parser = settings.css_parser(data)
        parser.parse_tokens()

        resolver = settings.resolver(url)
        path_gen = settings.path_gen(resource_location, style_location)

        super().__init__(parser, resolver, path_gen, style_location,
                         resource_location, recursion_limit)

        self._css_migration = CSSMigration(self, settings)

    async def migrate_external_sources(self):
        await self._css_migration.migrate()

    def export(self):
        return self.parser.export()


class CSSDeclaration(abstract.BaseEntity):
    def __init__(self, data, url, declaration_location, resource_location,
                 settings, recursion_limit=3):
        parser = settings.css_parser(data, declaration=True)
        parser.parse_tokens()

        resolver = settings.resolver(url)
        path_gen = settings.path_gen(resource_location, declaration_location)

        super().__init__(parser, resolver, path_gen, declaration_location,
                         resource_location, recursion_limit)

        self._css_migration = CSSMigration(self, settings)

    async def migrate_external_sources(self):
        await self._css_migration.migrate()

    def export(self):
        return self.parser.export()


class IndexFile(abstract.BaseEntity):
    def __init__(self, response, filepath, res_location, settings, migration, recursion_limit=3):
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._filepath = filepath
        self._settings = settings
        self.__parser = settings.html_parser(response.content_descriptor)

        index_location = pathlib.Path(filepath).parent
        resolver = self.__init_resolver(response.accessed_url)
        path_gen = settings.path_gen(res_location, index_location)

        super().__init__(self.__parser, resolver, path_gen,
                         index_location, res_location, recursion_limit)

        self._html_migration = migration(self, settings)
        del self.parser.base

    def __init_resolver(self, url):
        resolver = self._settings.resolver(url)

        try:
            resolver.base = resolver.resolve(self.__parser.base["href"])
        except Exception as e:
            self._logger.info(e)

        return resolver

    async def migrate_external_sources(self):
        await self._html_migration.migrate()

    def export(self):
        with open(self._filepath, "wb") as fd:
            fd.write(self.parser.export())


class IndexFileContainer:
    index_file = di_provider.Factory(IndexFile, migration=HTMLMigration)

    index_file_with_js_execution = di_provider.Factory(
        IndexFile, migration=HTMLMigrationWithJSExecution)
