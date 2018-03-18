import abc
import logging

import lemmiwinks.taskwrapper as taskwrapper


class BaseMigration(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    async def migrate(self):
        raise NotImplemented()


class DataHandler(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    async def process(self, data):
        raise NotImplemented()


class UpdateEntity(metaclass=abc.ABCMeta):
    def __init__(self):
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @taskwrapper.task
    async def update_entity(self, handler, entity, **kwargs):
        try:
            data = self._get_data_from(entity, **kwargs)
            new_data = await handler.process(data)
            self._update_entity(new_data, entity, **kwargs)
        except Exception as e:
            self._logger.exception(e)
            self._logger.error(e)
            self._logger.error(f"entity: {entity}")
            self._logger.error(f"entity attributes: {kwargs}")

    @abc.abstractmethod
    def _get_data_from(self, entity, **kwargs):
        raise NotImplemented()

    @abc.abstractclassmethod
    def _update_entity(self, data, entity, **kwargs):
        raise NotImplemented()


class BaseProperty(metaclass=abc.ABCMeta):
    def __init__(self, parser, resolver, path_gen,
                 entity_location, resource_location, recursion_limit):
        self.__parser = parser
        self.__resolver = resolver
        self.__path_gen = path_gen
        self.__recursion_limit = recursion_limit
        self.__entity_location = entity_location
        self.__resource_location = resource_location

    @property
    def parser(self):
        return self.__parser

    @property
    def path_gen(self):
        return self.__path_gen

    @property
    def resolver(self):
        return self.__resolver

    @property
    def recursion_limit(self):
        return self.__recursion_limit

    @property
    def resource_location(self):
        return self.__resource_location

    @property
    def entity_location(self):
        return self.__entity_location


class BaseEntity(metaclass=abc.ABCMeta):
    def __init__(self, parser, resolver, path_gen,
                 entity_location, resource_location, recursion_limit):

        self.__property = BaseProperty(
            parser, resolver, path_gen, entity_location, resource_location, recursion_limit)

    def __getattr__(self, item):
        return getattr(self.__property, item)

    @abc.abstractmethod
    def migrate_external_sources(self):
        raise NotImplemented()

    @abc.abstractmethod
    def export(self):
        raise NotImplemented()


class MigrationSettings(metaclass=abc.ABCMeta):
    @property
    def html_parser(self):
        raise NotImplemented()

    @property
    def css_parser(self):
        raise NotImplemented()

    @property
    def path_gen(self):
        raise NotImplemented()

    @property
    def http_client(self):
        raise NotImplemented()

    @property
    def http_js_pool(self):
        raise NotImplemented()

    @property
    def resolver(self):
        raise NotImplemented()
