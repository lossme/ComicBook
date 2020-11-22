import os
import re
import importlib
import datetime
import logging
import weakref

from .utils import safe_filename
from .utils import ensure_file_dir_exists
from .exceptions import (
    SiteNotSupport,
    ChapterNotFound
)
from .crawlerbase import CrawlerBase
from .image import ImageDownloader
HERE = os.path.abspath(os.path.dirname(__file__))

logger = logging.getLogger(__name__)


def find_all_crawler():
    for file in os.listdir(os.path.join(HERE, "site")):
        if re.match(r"^[a-zA-Z].*?\.py$", file):
            importlib.import_module(".site.{}".format(file.split(".")[0]), __package__)
    return CrawlerBase.__subclasses__()


class ComicBook():
    CRAWLER_CLS_MAP = {crawler.SITE: crawler for crawler in find_all_crawler()}

    def __init__(self, site, comicid=None):
        if site not in self.CRAWLER_CLS_MAP:
            raise SiteNotSupport(f"SiteNotSupport site={site}")
        crawler_cls = self.CRAWLER_CLS_MAP[site]
        comicid = comicid or crawler_cls.DEFAULT_COMICID
        self.crawler = crawler_cls(comicid)

        self.image_downloader = ImageDownloader(site=site)

        # {chapter_number: Chapter}
        self.chapter_cache = {}
        self.crawler_time = None
        self.comicbook_item = None
        self.tags = None
        self.last_chapter_number = 0
        self.last_chapter_title = ''

    def start_crawler(self):
        if self.crawler_time is None:
            self.refresh()

    def refresh(self):
        self.comicbook_item = self.crawler.get_comicbook_item()
        self.crawler_time = datetime.datetime.now()
        for field in self.comicbook_item.FIELDS:
            setattr(self, field, getattr(self.comicbook_item, field))

        if self.comicbook_item.citems:
            last_chapter = max(self.comicbook_item.citems.values(),
                               key=lambda x: x.chapter_number)
            self.last_chapter_number = last_chapter.chapter_number
            self.last_chapter_title = last_chapter.title
        else:
            self.last_chapter_number = 0
            self.last_chapter_title = ""

    def search(self, name=None, page=1, limit=None):
        return self.crawler.search(name, page=page, size=limit)

    def latest(self, page=1):
        return self.crawler.latest(page=page)

    def get_tags(self):
        if self.tags is None:
            self.tags = self.crawler.get_tags()
        return self.tags

    def get_tag_result(self, tag, page=1):
        return self.crawler.get_tag_result(tag=tag, page=page)

    def to_dict(self):
        if self.crawler_time is None:
            self.start_crawler()
        return self.comicbook_item.to_dict()

    def __repr__(self):
        return "<ComicBook>: {}".format(self.to_dict())

    def Chapter(self, chapter_number):
        if self.crawler_time is None:
            self.start_crawler()

        if chapter_number < 0:
            chapter_number = self.last_chapter_number + chapter_number + 1

        if chapter_number not in self.comicbook_item.citems:
            msg = ChapterNotFound.TEMPLATE.format(site=self.crawler.SITE,
                                                  comicid=self.crawler.comicid,
                                                  chapter_number=chapter_number,
                                                  source_url=self.crawler.source_url)
            raise ChapterNotFound(msg)

        if self.crawler.SITE == 'bilibili' or chapter_number not in self.chapter_cache:
            citem = self.comicbook_item.citems[chapter_number]
            chapter_item = self.crawler.get_chapter_item(citem)
            self.chapter_cache[chapter_number] = Chapter(
                comicbook_ref=weakref.ref(self),
                chapter_item=chapter_item)
        return self.chapter_cache[chapter_number]


class Chapter():

    def __init__(self, comicbook_ref, chapter_item):
        self.comicbook_ref = comicbook_ref
        self.chapter_item = chapter_item
        self._saved = False
        for field in self.chapter_item.FIELDS:
            setattr(self, field, getattr(self.chapter_item, field))

    @property
    def comicbook(self):
        return self.comicbook_ref()

    def to_dict(self):
        return self.chapter_item.to_dict()

    def __repr__(self):
        return "<Chapter>: {}".format(self.to_dict())

    def get_chapter_image_dir(self, output_dir):
        first_dir = safe_filename(self.comicbook.source_name)
        second_dir = safe_filename(self.comicbook.name)
        third_dir = safe_filename("{:>03} {}".format(self.chapter_item.chapter_number, self.chapter_item.title))
        chapter_dir = os.path.join(output_dir, first_dir, second_dir, third_dir)
        return chapter_dir

    def get_chapter_pdf_path(self, output_dir):
        first_dir = safe_filename(self.comicbook.source_name + ' pdf')
        second_dir = safe_filename(self.comicbook.name)
        filename = safe_filename("{:>03} {}".format(self.chapter_number, self.title)) + ".pdf"
        pdf_path = os.path.join(output_dir, first_dir, second_dir, filename)
        return pdf_path

    def get_single_image_path(self, output_dir):
        first_dir = safe_filename(self.comicbook.source_name + ' 长图')
        second_dir = safe_filename(self.comicbook.name)
        filename = safe_filename("{:>03} {}".format(self.chapter_number, self.title)) + ".jpg"
        img_path = os.path.join(output_dir, first_dir, second_dir, filename)
        return img_path

    def get_zipfile_path(self, output_dir):
        first_dir = safe_filename(self.comicbook.source_name + ' zip')
        second_dir = safe_filename(self.comicbook.name)
        filename = safe_filename("{:>03} {}".format(self.chapter_number, self.title)) + ".zip"
        zipfile_path = os.path.join(output_dir, first_dir, second_dir, filename)
        return zipfile_path

    def save(self, output_dir):
        chapter_dir = self.get_chapter_image_dir(output_dir)
        if self._saved is True:
            return chapter_dir
        headers = {'Referer': self.chapter_item.source_url}
        self.comicbook.image_downloader.download_images(
            image_urls=self.image_urls,
            output_dir=chapter_dir,
            headers=headers,
            image_pipelines=self.chapter_item.image_pipelines)
        self._saved = True
        return chapter_dir

    def save_as_pdf(self, output_dir):
        from .utils._img2pdf import image_dir_to_pdf
        chapter_dir = self.save(output_dir)
        pdf_path = self.get_chapter_pdf_path(output_dir)
        ensure_file_dir_exists(pdf_path)
        image_dir_to_pdf(img_dir=chapter_dir,
                         target_path=pdf_path,
                         sort_by=lambda x: int(x.split('.')[0]))
        return pdf_path

    def save_as_single_image(self, output_dir, quality=95):
        from .utils import image_dir_to_single_image
        chapter_dir = self.save(output_dir)
        img_path = self.get_single_image_path(output_dir)
        ensure_file_dir_exists(img_path)
        img_path = image_dir_to_single_image(img_dir=chapter_dir,
                                             target_path=img_path,
                                             sort_by=lambda x: int(x.split('.')[0]),
                                             quality=quality)
        return img_path

    def save_as_zip(self, output_dir):
        from .utils import image_dir_to_zipfile
        chapter_dir = self.save(output_dir)
        zipfile_path = self.get_zipfile_path(output_dir)
        ensure_file_dir_exists(zipfile_path)
        return image_dir_to_zipfile(chapter_dir, zipfile_path)
