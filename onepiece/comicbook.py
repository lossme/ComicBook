import os
import re
import importlib

from .utils import safe_filename
from .image_cache import ImageCache
from .exceptions import SiteNotSupport

HERE = os.path.abspath(os.path.dirname(__file__))


def find_support_site():
    sites = set(
        map(
            lambda x: x.split(".py")[0],
            filter(
                lambda x: re.match(r"^[a-zA-Z].*?\.py$", x),
                os.listdir(os.path.join(HERE, "site"))
            )
        )
    )
    sites.remove('ishuhui')   # 蜡烛
    sites.remove('wangyi')    # 被b站收购了
    return frozenset(sites)


class ComicBook():
    SUPPORT_SITE = find_support_site()

    def __init__(self, comicbook_crawler):
        self.crawler = comicbook_crawler
        self.comicbook_item = self.crawler.get_comicbook_item()
        for field in self.comicbook_item.FIELDS:
            setattr(self, field, getattr(self.comicbook_item, field))

        # {chapter_number: Chapter}
        self.chapter_db = {}

        if len(self.comicbook_item.chapters) > 0:
            self.last_chapter_number = self.comicbook_item.chapters[-1]["chapter_number"]
            self.last_chapter_title = self.comicbook_item.chapters[-1]["title"]
        else:
            self.last_chapter_number = 0
            self.last_chapter_title = ""

    @classmethod
    def create_comicbook(cls, site, comicid):
        if site not in cls.SUPPORT_SITE:
            raise SiteNotSupport("site={} 暂不支持".format(site))
        module = importlib.import_module(".site.{}".format(site), __package__)
        crawler = module.ComicBookCrawler(comicid)
        return cls(comicbook_crawler=crawler)

    @classmethod
    def search(cls, site, name, limit=None):
        if site not in cls.SUPPORT_SITE:
            raise SiteNotSupport("site={} 暂不支持".format(site))
        module = importlib.import_module(".site.{}".format(site), __package__)
        return module.ComicBookCrawler.search(name)[:limit]

    def to_dict(self):
        return self.comicbook_item.to_dict()

    def __repr__(self):
        return "<ComicBook>: {}".format(self.to_dict())

    def Chapter(self, chapter_number):
        if chapter_number < 0:
            chapter_number = self.last_chapter_number + chapter_number + 1
        if chapter_number not in self.chapter_db:
            chapter_item = self.crawler.get_chapter_item(chapter_number)
            chapter = Chapter(comicbook_item=self.comicbook_item, chapter_item=chapter_item)
            self.chapter_db[chapter_number] = chapter
        return self.chapter_db[chapter_number]


class Chapter():

    def __init__(self, comicbook_item, chapter_item):
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
        ImageCache.download_images(image_urls=self.image_urls, output_dir=chapter_dir)
        return chapter_dir

    def save_as_pdf(self, output_dir):
        from .utils.img2pdf import image_dir_to_pdf
        chapter_dir = self.save(output_dir)
        pdf_path = self.get_chapter_pdf_path(output_dir)
        image_dir_to_pdf(img_dir=chapter_dir,
                         target_path=pdf_path,
                         sort_by=lambda x: int(x.split('.')[0]))
        return pdf_path
