import asyncio
import logging
import urllib.parse

import dependency_injector.providers as di_providers

import pathlib
import httplib
import singleton

from . import abstract
from . import container


class SrcRegister(dict, metaclass=singleton.ThreadSafeSingleton):
    pass


class UpdateTokenValue(abstract.UpdateEntity):
    def __init__(self, resolver):
        super().__init__()
        self.__resolver = resolver
        self.__src_register = SrcRegister()

    def _get_data_from(self, entity, **kwargs):
        return self.__resolver.resolve(entity.value)

    def _update_entity(self, url, entity, **kwargs):
        entity.value = self.__src_register.get(url).relpath


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


class DownloadHandler(abstract.DataHandler):
    def __init__(self, entity_property, settings):
        self.__logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.__downloader = httplib.provider.HTTPClientDownloader(settings.http_client())
        self.__path_gen = entity_property.path_gen
        self.__src_register = SrcRegister()

    async def process(self, url):
        try:
            if url in self.__src_register.keys():
                await self.__download(url)

            path = self.__src_register.get(url).relpath
        except Exception as e:
            self.__log_error(e=e, url=url)
            return None
        else:
            return path

    def __log_error(self, **kwargs):
        self.__logger.exception(kwargs["e"])
        self.__logger.error(kwargs["e"])
        self.__logger.error(f'url: {kwargs["url"]}')

    async def __download(self, url):
        try:
            self.__register_path_for_url(url)
            path = self.__src_register.get(url).abspath
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
            if url in self._src_register.keys():
                await self.__migrate_entity_from(url)

            path = self._src_register.get(url).relpath
        except Exception as e:
            self.__log_error(e=e, url=url)
            return None
        else:
            return path

    async def __migrate_entity_from(self, url):
        self._register_path_for(url)
        response = await self._get_response_from(url)
        await self.__process_response(response)

    def __log_error(self, **kwargs):
        self.__logger.exception(kwargs["e"])
        self.__logger.error(kwargs["e"])
        self.__logger.error(f'url: {kwargs["url"]}')

    def _register_path_for(self, url):
        raise NotImplemented

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
        path = self._src_register.get(url).abspath

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
        path = self._src_register.get(url).abspath

        css_file = CssFile(response.content_descriptor, path,
                           self.__settings, self._recursion_limit-1)

        css_file.migrate_external_sources()
        css_file.export()


class HTMLFileWithJsExecutionHandler(_RecursiveEntityHandler):
    def __init__(self, entity_property, settings):
        super().__init__(entity_property.recursion_limit)
        self.__http_js_pool = settings.http_js_pool()
        self.__path_gen = entity_property.path_gen
        self._settings = settings

    def _register_path_for(self, url):
        url_path = urllib.parse.urlparse(url).path
        path = self.__path_gen.generate_filepath_with(pathlib.Path(url_path).suffix)
        self._src_register.update({url: path})

    async def _get_response_from(self, url):
        client = self.__http_js_pool.acquire()
        response = await client.get_request(url)
        self.__http_js_pool.release(client)
        return response

    async def _process_entity_recursively_from(self, response):
        url = response.requested_url
        path = self._src_register.get(url).abspath

        index_file = IndexFile()


class HTMLFileHandler(_RecursiveEntityHandler):
    def __init__(self, entity_property, settings):
        super().__init__(entity_property.recursion_limit)
        self.__client = settings.http_client()
        self.__path_gen = entity_property.path_gen
        self._settings = settings

    def _register_path_for(self, url):
        url_path = urllib.parse.urlparse(url).path
        path = self.__path_gen.generate_filepath_with(pathlib.Path(url_path).suffix)
        self._src_register.update({url: path})

    async def _get_response_from(self, url):
        return await self.__client.get_request(url)

    async def _process_entity_recursively_from(self, response):
        pass


class CssStyleHandler(abstract.DataHandler):
    def __init__(self):
        pass

    async def process(self, data):
        pass


class CssDeclarationHandler(abstract.DataHandler):
    def __init__(self):
        pass

    async def process(self, data):
        pass


class JSScriptHandler(abstract.DataHandler):
    def __init__(self):
        pass

    async def process(self, data):
        pass


class InlineJSScriptHandler(abstract.DataHandler):
    def __init__(self):
        pass

    async def process(self, data):
        pass


class JSEventsHandler(abstract.DataHandler):
    def __init__(self):
        pass

    async def process(self, data):
        pass


class UpdateElementContainer:
    def __init__(self, entity_property, settings):
        self.__element_string_updater = UpdateElementString
        self.__element_attr_updater = UpdateElementAttribute()


class UpdateTokenContainer:
    def __init__(self, entity_property, settings):
        client = settings.http_client()
        self.__token_value_updater = UpdateTokenValue(entity_property.resolver)

        # handlers
        self.__download_token = EntityDownloadHandler(client, entity_property.path_gen)
        self.__css_file_handler = CSSFileHandler(client, entity_property.path_gen,
                                                 settings, entity_property.recurion_limit)

    def update_url_token(self, token):
        self.__token_value_updater.update_entity(self.__download_token, token)

    def update_import_token(self, token):
        self.__token_value_updater.update_entity(self.__css_file_handler, token)


class CSSMigration(abstract.BaseMigrate):
    def __init__(self, css_entity, settings: abstract.MigrationSettings):
        self.__css_entity = css_entity
        self.__updater = UpdateTokenContainer(css_entity, settings)

    async def migrate(self):
        await asyncio.gather(self.__update_url_tokens(), self.__update_import_tokens())

    @abstract._task
    async def __update_url_tokens(self):
        tasks = [self.__updater.update_url_token(token)
                 for token in self.__css_entity.parser.url_tokens]
        await asyncio.gather(*tasks)

    @abstract._task
    async def __update_import_tokens(self):
        tasks = [self.__updater.update_import_token(token)
                 for token in self.__css_entity.parser.import_tokens]
        await asyncio.gather(*tasks)


class CssFile(abstract.BaseEntity):
    def __init__(self, data, filepath, settings, recursion_limit=3):
        self._filepath = filepath

        parser = settings.css_parser(data.content_descriptor)
        parser.parse_tokens()
        resolver = settings.resolver(data.accessed_url)
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


class CSSContainer:
    def __init__(self, url, essential_location, res_location, settings):
        self._url = url
        self._res_location = res_location
        self._essential_location = essential_location
        self._settings = settings

    @property
    def css_file(self):
        return di_providers.Factory(CssFile, settings=self._settings)

    @property
    def css_inline(self):
        return di_providers.Factory(CSSStyle, url=self._url,
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
        self._settings = settings

        client = settings.http_client()

        self.__external_updater = UpdateElementAttributeSource(index_file.resolver)
        self.__data_updater = UpdateElement()

        self._css_file_handler = ExternalMigrationCSSFileHandler(
            client, index_file.path_gen, settings, index_file.recursion_limit)

        self._css_container = CSSContainer(index_file.resolver.base,
                                           index_file.essential_location,
                                           index_file.resource_location,
                                           settings)

        self._html_filter = container.HTMLFilter(index_file.parser)
        self._src_register = SrcRegister()

    def migrate_html_elements_sources(self):
        tasks = [self.__external_updater.update_entity(element, attr=attr)
                 for element, attr in self._html_filter.elements]

        return tasks

    def migrate_css_file(self):
        tasks = [self.__external_updater.update_entity(self._css_file_handler, element, attr=attr)
                 for element, attr in self._html_filter.stylesheet_link]

        return tasks

    def migrate_css_style(self):
        tasks = [self.__data_updater.update_entity(element)
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
        tasks = [self.__external_updater.update_entity(element, attr=attr)
                 for element, attr in self._html_filter.js_style]

        return tasks

    def migrate_frames(self):
        tasks = [self.__external_updater.update_recursive_entity(
            self.__migrate_frames, element, attr=attr)
            for element, attr in self._html_filter.frames]

        return tasks

    async def __migrate_frames(self, url):
        self.__external_updater.register_path_for(url)
        response = await self._client.get_request(url)
        path = self._src_register.get(url).abspath
        html_file = IndexFile(response, path, self._index_file.resource_location,
                              self._settings, self._index_file.recuriosn_limit-1)
        await html_file.migrate()
        html_file.export()


class HTMLMigrationWithExecutedJs(HTMLMigration):
    def __init__(self, index_file, setting):
        super().__init__(index_file, setting)
        self.__http_js_pool = setting.http_js_pool()


class IndexFile(abstract.BaseEntity):
    def __init__(self, response, filepath, res_location, settings, recursion_limit=3):
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._filepath = filepath
        self._settings = settings

        essential_location = pathlib.Path(filepath).parent
        self.__parser = settings.html_parser(response.content_descriptor)
        resolver = self.__init_resolver(response.accessed_url)
        path_gen = settings.path_gen(res_location, essential_location)

        super().__init__(self.__parser, resolver, path_gen,
                         essential_location, res_location, recursion_limit)

        self._html_migration = HTMLMigration(self, settings)
        del self.parser.base

    def __init_resolver(self, url):
        try:
            resolver = self._settings.resolver(url)
            resolver.base = resolver.resolve(self.__parser.base["href"])
        except Exception as e:
            self._logger.info(f"{e}")
            self._logger.info(f"Base url was {url}")
            self._logger.info(f"Base tag is {self.__parser.base}")
        finally:
            return resolver

    async def migrate_external_sources(self):
        #tasks = self._html_migration.migrate_css_declaration()
        #tasks += self._html_migration.migrate_css_style()
        #tasks = self._html_migration.migrate_html_elements_sources()
        tasks = self._html_migration.migrate_css_file()
        #tasks += self._html_migration.migrate_frames()
        #tasks += self._html_migration.migrate_javascript()

        await asyncio.gather(*tasks)

    def export(self):
        with open(self._filepath, "wb") as fd:
            fd.write(self.parser.export())
