import pathlib
import uuid
import collections

Path = collections.namedtuple('Path', 'abspath relpath')


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
        self._directory = directory
        self.path_prefix = path_prefix

    def generate_filepath_with(self, extension: str) -> Path:
        try:
            abs_path = self.__generate_abs_filepath_with(extension)
            rel_path = abs_path.relative_to(self.path_prefix)
        except ValueError:
            rel_path = abs_path
        finally:
            return Path(abspath=str(abs_path), relpath=str(rel_path))

    def __generate_abs_filepath_with(self, extension: str) -> pathlib.Path:
        return self._directory.get_filepath_with(extension)


class FilePathProvider:
    @classmethod
    def filepath_generator(cls, location, path_prefix):
        directory = DirectoryWrapper(location)
        return FilePathGenerator(directory, path_prefix)
