import time
import uuid
import os.path
import mimetypes
import magic
from chardet.universaldetector import UniversalDetector
import urllib.parse

def unique(path: str):
    while True:
        name = str(time.time()) + "_" + str(uuid.uuid4())
        if not os.path.exists(path + '/' + name):
            break

    return name


def set_file_ext(filepath: str) -> str:
    _, ext = os.path.splitext(filepath)

    if ext:
        return filepath

    try:
        type = magic.from_file(filepath, mime=True)
        ext = mimetypes.guess_extension(type)
    except Exception:
        ext = ".unknown"
    new_name = unique_filename(filepath+ext)
    os.rename(filepath, new_name)

    return new_name


def unique_filename(filepath: str) -> str:
    if not os.path.exists(filepath):
        return filepath

    filename, ext = os.path.split(filepath)
    dirpath = os.path.dirname(filename)

    while True:
        namepath = str(uuid.uuid4()) + ext
        if not os.path.exists(dirpath + '/' + namepath + ext):
            break

    return namepath+ext


def get_file_encoding(filepath: str) -> str:
    with open(filepath, 'rb') as fd:
        detector = UniversalDetector()
        for line in fd:
            detector.feed(line)
            if detector.done:
                break
        detector.close()
    return detector.result


def ext_from_url(url: str) -> str:
    parts = urllib.parse.urlparse(url)
    # parts[2] is url path
    _, ext = os.path.splitext(parts[2])
    return ext
