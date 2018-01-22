import archive.migrate as migrate
import os

from http_client import provider
from archive import maff
from .migrate import container
import filepath_generator
import parser.container

async def archive():
    with maff.MozillaArchiveFormat("./hovno") as maff_archive:
        dst = maff_archive.create_tab()
        os.makedirs(os.path.join(dst, "index_files"), exist_ok=True)
        fd = open("/home/viliam/PycharmProjects/lemmiwinks/html_example/index.html")
        na = container.WebPageMigration(dst=dst,
                                        file=fd,
                                        url="http://www.plocha.net/kdojeplocha.php",
                                        http_downloader=provider.HTTPClientDownloadProvider.aio_downloader(),
                                        filepath_gen=filepath_generator.FilePathGeneratorContainer.filepath_generator,
                                        html_parser=parser.container.HTMLParserContainer.bs_parser)
        await na.migrate_html_elements()
        await na.migrate_css()
        await na.migrate_js()
        na.save_index()