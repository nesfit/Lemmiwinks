import os
import uuid


def get_extension_from(path):
    _, extension = os.path.splitext(path)
    return extension[1::]


def get_filename_from(path):
    _, filename = os.path.split(path)
    return filename


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
        filename = f"{uuid.uuid4().hex}.{ext}" if ext else f"{uuid.uuid4().hex}"
        return os.path.join(self._dirpath, filename)

    def remove_file(self, filepath):
        os.remove(filepath)
        self._files.remove(filepath)
