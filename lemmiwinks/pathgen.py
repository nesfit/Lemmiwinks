import pathlib
import uuid
import logging
import urllib.parse
import mimetypes

import magic


class DirectoryWrapper:
    def __init__(self, location: str):
        self._dirpath = pathlib.Path(location).resolve()
        self._files = set()

        if not self._dirpath.exists() or not self._dirpath.is_dir():
            raise NotADirectoryError(
                f"Path '{location}' doesn't exist or it is not a directory.")

    def get_filepath_with(self, extension: str) -> pathlib.Path:
        filepath = self.__generate_unique_filepath_with(extension)
        self._files.add(filepath)
        return filepath

    def __generate_unique_filepath_with(self, extension: str) -> pathlib.Path:
        filepath = self.__generate_filepath_with(extension)

        while filepath in self._files or filepath.exists():
            filepath = self.__generate_filepath_with(extension)

        return filepath

    def __generate_filepath_with(self, extension: str) -> pathlib.Path:
        filename = f"{uuid.uuid4().hex}{extension}"
        return self._dirpath.joinpath(filename)


class FilePathGenerator:
    def __init__(self, directory: object, path_prefix: str):
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._directory = directory
        self._path_prefix = path_prefix

    def generate_filepath_with(self, extension: str) -> str:
        abs_path = self.__generate_abs_filepath_with(extension)
        return str(abs_path)

    def get_relpath_from(self, abs_path: str) -> str:
        try:
            relpath = str(pathlib.Path(abs_path).relative_to(self._path_prefix))
        except Exception as e:
            self._logger.exception(e)
            self._logger.error(f"absolute path: {abs_path}")
            return abs_path
        else:
            return relpath


    def __generate_abs_filepath_with(self, extension: str) -> pathlib.Path:
        return self._directory.get_filepath_with(extension)


class FilePathProvider:
    @classmethod
    def filepath_generator(cls, location, path_prefix):
        directory = DirectoryWrapper(location)
        return FilePathGenerator(directory, path_prefix)


class MimeFileExtension:
    def __init__(self, filepath, url):
        self.__filepath = filepath
        self.__url = url

    def add_extension_to(self, name):
        ext = self.__get_extension_from_url()
        mime_type = self.__get_mime_type_from_filepath()

        if not self.__is_extension_valid_to_mime_type(ext, mime_type):
            ext = self.__get_extension_from(mime_type)

        return f"{name}{ext}"

    def __get_extension_from_url(self):
        url_path = urllib.parse.urlparse(self.__url).path
        ext = pathlib.Path(url_path).suffix
        return ext

    def __get_mime_type_from_filepath(self):
        mime_type = magic.from_file(self.__filepath, mime=True)
        return mime_type

    @staticmethod
    def __is_extension_valid_to_mime_type(ext, mime_type):
        return ext in mimetypes.guess_all_extensions(mime_type)

    @staticmethod
    def __get_extension_from(mime_type):
        return mimetypes.guess_extension(mime_type)