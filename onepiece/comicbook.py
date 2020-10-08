import os
import re
import importlib
import datetime
import logging

from .utils import safe_filename
from .exceptions import (
    SiteNotSupport,
    ChapterNotFound
)
from .crawlerbase import CrawlerBase
from .image_cache import image_cache
HERE = os.path.abspath(os.path.dirname(__file__))

logger = logging.getLogger(__name__)


def find_all_crawler():
    for file in os.listdir(os.path.join(HERE, "site")):
        if re.match(r"^[a-zA-Z].*?\.py$", file):
            importlib.import_module(".site.{}".format(file.split(".")[0]), __package__)
    return CrawlerBase.__subclasses__()


class ComicBook():
    CRAWLER_CLS_MAP = {crawler.SITE: crawler for crawler in find_all_crawler()}

    def __init__(self, comicbook_crawler):
        self.crawler = comicbook_crawler

        # {chapter_number: Chapter}
        self.chapter_cache = {}
        self.crawler_time = None
        self.comicbook_item = None

    def start_crawler(self):
        self.comicbook_item = self.crawler.get_comicbook_item()
        self.crawler_time = datetime.datetime.now()
        for field in self.comicbook_item.FIELDS:
            setattr(self, field, getattr(self.comicbook_item, field))

        if self.comicbook_item.citem_dict:
            last_chapter = max(self.comicbook_item.citem_dict.values(),
                               key=lambda x: x.chapter_number)
            self.last_chapter_number = last_chapter.chapter_number
            self.last_chapter_title = last_chapter.title
        else:
            self.last_chapter_number = 0
            self.last_chapter_title = ""

    @classmethod
    def create_comicbook(cls, site, comicid):
        if site not in cls.CRAWLER_CLS_MAP:
            raise SiteNotSupport("site={} 暂不支持".format(site))
        crawler_cls = cls.CRAWLER_CLS_MAP[site]
        if comicid is None:
            comicid = crawler_cls.DEFAULT_COMICID
        crawler = crawler_cls(comicid)
        comicbook = cls(comicbook_crawler=crawler)
        return comicbook

    def search(self, name=None, page=1, limit=None):
        return self.crawler.search(name, page=page, size=limit)

    def latest(self, page=1):
        return self.crawler.latest(page=page)

    def to_dict(self):
        return self.comicbook_item.to_dict()

    def __repr__(self):
        return "<ComicBook>: {}".format(self.to_dict())

    def Chapter(self, chapter_number, force_refresh=False):
        if chapter_number < 0:
            chapter_number = self.last_chapter_number + chapter_number + 1

        if chapter_number not in self.comicbook_item.citem_dict:
            msg = ChapterNotFound.TEMPLATE.format(site=self.crawler.SITE,
                                                  comicid=self.crawler.comicid,
                                                  chapter_number=chapter_number,
                                                  source_url=self.crawler.source_url)
            raise ChapterNotFound(msg)

        if force_refresh or chapter_number not in self.chapter_cache:
            citem = self.comicbook_item.citem_dict[chapter_number]
            chapter_item = self.crawler.get_chapter_item(citem)
            self.chapter_cache[chapter_number] = Chapter(
                crawler=self.crawler,
                comicbook_item=self.comicbook_item,
                chapter_item=chapter_item)
        return self.chapter_cache[chapter_number]


class Chapter():

    def __init__(self, crawler, comicbook_item, chapter_item):
        self.crawler = crawler
        self.comicbook_item = comicbook_item
        self.chapter_item = chapter_item

        for field in self.chapter_item.FIELDS:
            setattr(self, field, getattr(self.chapter_item, field))

    def to_dict(self):
        return self.chapter_item.to_dict()

    def __repr__(self):
        return "<Chapter>: {}".format(self.to_dict())

    def get_chapter_image_dir(self, output_dir):
        first_dir = safe_filename(self.comicbook_item.source_name)
        second_dir = safe_filename(self.comicbook_item.name)
        third_dir = safe_filename("{:>03} {}".format(self.chapter_item.chapter_number, self.chapter_item.title))
        chapter_dir = os.path.join(output_dir, first_dir, second_dir, third_dir)
        return chapter_dir

    def get_chapter_pdf_path(self, output_dir):
        first_dir = safe_filename(self.comicbook_item.source_name)
        second_dir = safe_filename(self.comicbook_item.name)
        filename = safe_filename("{:>03} {}".format(self.chapter_number, self.title)) + ".pdf"
        pdf_path = os.path.join(output_dir, first_dir, second_dir, filename)
        return pdf_path

    def save(self, output_dir):
        chapter_dir = self.get_chapter_image_dir(output_dir)
        headers = {'Referer': self.chapter_item.source_url}
        image_cache.download_images(
            image_urls=self.image_urls, output_dir=chapter_dir, headers=headers)
        return chapter_dir

    def save_as_pdf(self, output_dir):
        from .utils.img2pdf import image_dir_to_pdf
        chapter_dir = self.save(output_dir)
        pdf_path = self.get_chapter_pdf_path(output_dir)
        image_dir_to_pdf(img_dir=chapter_dir,
                         target_path=pdf_path,
                         sort_by=lambda x: int(x.split('.')[0]))
        return pdf_path
