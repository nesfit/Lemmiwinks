import os
import uuid


class Directory:
    def __init__(self, dirpath):
        self._dirpath = dirpath
        self._files = set()

    @property
    def dirpath(self):
        return self._dirpath

    @property
    def list_files(self):
        return os.listdir(self._dirpath)

    def get_unique_filepath(self, ext):
        filepath = self.__generate_unique_filepath(ext)
        self._files.add(filepath)
        return filepath

    def __generate_unique_filepath(self, ext):
        filepath = self.__generate_filepath(ext)

        while filepath in self._files or os.path.exists(filepath):
            filepath = self.__generate_filepath(ext)

        return filepath

    def __generate_filepath(self, ext):
        filename = f"{uuid.uuid4().hex}" if ext else f"{uuid.uuid4().hex}.{ext}"
        return os.path.join(self._dirpath, filename)

    def remove_file(self, filepath):
        os.remove(filepath)
        self._files.remove(filepath)
