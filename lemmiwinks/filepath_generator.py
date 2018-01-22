import os
import uuid
from typing import List


class Directory:
    def __init__(self, dirpath: str):
        self._dirpath = dirpath
        self._files = set()

    @property
    def dirpath(self) -> str:
        return self._dirpath

    @property
    def list_files(self) -> List[str]:
        return os.listdir(self._dirpath)

    def get_unique_filepath(self, ext: str) -> str:
        filepath = self.__generate_unique_filepath(ext)
        self._files.add(filepath)
        return filepath

    def __generate_unique_filepath(self, ext: str) -> str:
        filepath = self.__generate_filepath(ext)

        while filepath in self._files or os.path.exists(filepath):
            filepath = self.__generate_filepath(ext)

        return filepath

    def __generate_filepath(self, ext: str) -> str:
        filename = f"{uuid.uuid4().hex}{ext}"
        return os.path.join(self._dirpath, filename)

    def remove_file(self, filepath: str) -> None:
        # TODO: try block ?
        os.remove(filepath)
        self._files.remove(filepath)


class FilePathGenerator:
    def __init__(self, directory: object, rel_path_prefix: str):
        self._directory = directory
        self._rel_path_prefix = rel_path_prefix

    def generate_unique_filepath_from(self, filepath):
        _, ext = os.path.splitext(filepath)
        path = self._directory.get_unique_filepath(ext)
        return path

    def generate_relative_path_from(self, path):
        _, filename = os.path.split(path)
        rel_path = os.path.join(self._rel_path_prefix, filename)
        return rel_path


class FilePathGeneratorContainer:
    @staticmethod
    def filepath_generator(path, rel_path):
        directory = Directory(path)
        return FilePathGenerator(directory, rel_path)
