import os

import jinja2
from dependency_injector import providers


class MetaInfoTable:
    def __init__(self, filepath, template_location):
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_location))
        self._template = env.get_template('metatable.html')
        self._context = {
            'title': "",
            'metainfo': dict()
        }
        self._filepath = filepath

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.save()

    @property
    def title(self):
        return self._context.get('title')

    @title.setter
    def title(self, title):
        self._context['title'] = title

    def add_record(self, key, *args):
        self._context['metainfo'].update({key: args})

    def save(self):
        with open(self._filepath, "w") as fd:
            fd.write(self._template.render(self._context))


class MetaInfoContainer:
    def __init__(self):
        abs_dir_path = os.path.abspath(os.path.dirname(__file__))
        self._template_path = os.path.join(abs_dir_path, "template")

    @property
    def meta_tab(self):
        return providers.Factory(MetaInfoTable,
                                 template_location=self._template_path)
