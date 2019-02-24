import os
import warnings
import shutil
import re
import importlib

from concurrent.futures import ThreadPoolExecutor

import requests

from .utils import safe_filename
from .image_cache import ImageCache
from .exceptions import SiteNotSupport

HERE = os.path.abspath(os.path.dirname(__file__))


class ComicBook():
    SUPPORT_SITE = frozenset(
        map(
            lambda x: x.split(".py")[0],
            filter(
                lambda x: re.match(r"^[a-zA-Z].*?\.py$", x),
                os.listdir(os.path.join(HERE, "site"))
            )
        )
    )

    def __init__(self, comicbook_crawler):
        self.crawler = comicbook_crawler
        self.comicbook_item = self.crawler.get_comicbook_item()
        for field in self.comicbook_item.FIELDS:
            setattr(self, field, getattr(self.comicbook_item, field))

        # {chapter_number: Chapter}
        self.chapter_db = {}

    @classmethod
    def init(cls, worker=4):
        Chapter.init(worker=worker)

    @classmethod
    def create_comicbook(cls, site, comicid):
        if site not in cls.SUPPORT_SITE:
            raise SiteNotSupport("site={} 暂不支持".format(site))
        module = importlib.import_module(".site.{}".format(site), __package__)
        crawler = module.ComicBookCrawler(comicid)
        return cls(comicbook_crawler=crawler)

    @classmethod
    def search(cls, site, name):
        if site not in cls.SUPPORT_SITE:
            raise SiteNotSupport("site={} 暂不支持".format(site))
        module = importlib.import_module(".site.{}".format(site), __package__)
        return module.ComicBookCrawler.search(name)

    def to_dict(self):
        return self.comicbook_item.to_dict()

    def __repr__(self):
        return "<ComicBook>: {}".format(self.to_dict())

    def Chapter(self, chapter_number):
        if chapter_number not in self.chapter_db:
            chapter_item = self.crawler.get_chapter_item(chapter_number)
            chapter = Chapter(comicbook_item=self.comicbook_item, chapter_item=chapter_item)
            self.chapter_db[chapter_number] = chapter
        return self.chapter_db[chapter_number]


class Chapter():
    IMAGE_DOWNLOAD_POOL = None
    DEFAULT_POOL_SIZE = 4

    def __init__(self, comicbook_item, chapter_item):
        self.comicbook_item = comicbook_item
        self.chapter_item = chapter_item

        for field in self.chapter_item.FIELDS:
            setattr(self, field, getattr(self.chapter_item, field))

    @classmethod
    def init(cls, worker=None):
        worker = worker or cls.DEFAULT_POOL_SIZE
        cls.IMAGE_DOWNLOAD_POOL = ThreadPoolExecutor(max_workers=worker)

    @classmethod
    def get_pool(cls):
        if cls.IMAGE_DOWNLOAD_POOL is None:
            cls.IMAGE_DOWNLOAD_POOL = ThreadPoolExecutor(max_workers=4)
        return cls.IMAGE_DOWNLOAD_POOL

    def to_dict(self):
        return self.chapter_item.to_dict()

    def __repr__(self):
        return "<Chapter>: {}".format(self.to_dict())

    def get_chapter_image_dir(self, output_dir):
        first_dir = safe_filename(self.comicbook_item.source_name)
        second_dir = safe_filename(self.comicbook_item.name)
        third_dir = safe_filename("{} {}".format(self.chapter_item.chapter_number, self.chapter_item.title))
        chapter_dir = os.path.join(output_dir, first_dir, second_dir, third_dir)
        return chapter_dir

    def get_chapter_pdf_path(self, output_dir):
        first_dir = safe_filename(self.comicbook_item.source_name)
        second_dir = safe_filename(self.comicbook_item.name)
        file_name = safe_filename("{} {}.pdf".format(self.chapter_number, self.title))
        pdf_path = os.path.join(output_dir, first_dir, second_dir, file_name)
        return pdf_path

    def save(self, output_dir):
        chapter_dir = self.get_chapter_image_dir(output_dir)
        future_list = []
        for idx, image in enumerate(self.images, start=1):
            ext = ImageInfo.find_suffix(image.image_url)
            target_path = os.path.join(chapter_dir, "{}.{}".format(idx, ext))
            future = self.get_pool().submit(image.save, target_path=target_path)
            future_list.append(future)
        return chapter_dir, future_list

    @property
    def images(self):
        return [ImageInfo(image_url) for image_url in self.image_urls]

    def save_as_pdf(self, output_dir):
        from .utils.img2pdf import image_dir_to_pdf
        # 等全部图片下载完成
        chapter_dir, future_list = self.save(output_dir)
        for future in future_list:
            try:
                future.result()
            except Exception as e:
                warnings.warn(str(e))

        pdf_path = self.get_chapter_pdf_path(output_dir)
        image_dir_to_pdf(img_dir=chapter_dir,
                         target_path=pdf_path,
                         sort_by=lambda x: int(x.split('.')[0]))
        return pdf_path


class ImageInfo():
    session = requests.Session()
    TIMEOUT = 30
    IS_USE_CACHE = True

    def __init__(self, image_url):
        self.image_url = image_url

    def __repr__(self):
        return "<ImageInfo>: image_url={image_url}".format(image_url=self.image_url)

    @staticmethod
    def find_suffix(image_url, default='jpg', allow=frozenset(['jpg', 'png', 'jpeg', 'gif'])):
        """从图片url提取图片扩展名
        :param image_url: 图片链接
        :param default: 扩展名不在 allow 内，则返回默认扩展名
        :param allow: 允许的扩展名
        :return ext: 扩展名，不包含.
        """
        ext = image_url.rsplit('.', 1)[-1].lower()
        if ext not in allow:
            return default
        return ext

    def save(self, target_path):
        if self.IS_USE_CACHE:
            cache_file = ImageCache.get_cache_path(self.image_url)
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            shutil.copyfile(cache_file, target_path)
        else:
            ImageCache.download_image(image_url=self.image_url, target_path=target_path)
        return target_path
