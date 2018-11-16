import os
import warnings
import shutil
import re
import importlib

from concurrent.futures import ThreadPoolExecutor

import requests
from .image_cache import ImageCache

HERE = os.path.abspath(os.path.dirname(__file__))


class ComicBook():
    SUPPORT_SITE = list(
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

    @classmethod
    def init(cls, worker=4):
        Chapter.init(worker=worker)

    @classmethod
    def create_comicbook(cls, site, comicid):
        if site not in cls.SUPPORT_SITE:
            raise Exception("site={} 暂不支持")
        module = importlib.import_module(".site.{}".format(site), __package__)
        crawler = module.ComicBookCrawler(comicid)
        return cls(comicbook_crawler=crawler)

    @property
    def name(self):
        return self.crawler.get_comicbook_name()

    @property
    def desc(self):
        return self.crawler.get_comicbook_desc()

    @property
    def source_name(self):
        return self.crawler.source_name

    @property
    def tag(self):
        return self.crawler.get_comicbook_tag()

    @property
    def max_chapter_number(self):
        self.crawler.get_max_chapter_number()

    def __repr__(self):
        return """<ComicBook>
name={name}
desc={desc}
tag={tag}
source_name={source_name}
</ComicBook>""".format(name=self.name, desc=self.desc, tag=self.tag, source_name=self.source_name)

    def get_chapter(self, chapter_number):
        return Chapter(chapter_number=chapter_number, comicbook_crawler=self.crawler)

    def get_max_chapter_number(self):
        return self.crawler.get_max_chapter_number()

    def get_comicbook_dir(self, output_dir):
        comicbook_dir = os.path.join(output_dir, self.source_name, self.name)
        if not os.path.exists(comicbook_dir):
            os.makedirs(comicbook_dir)
        return comicbook_dir

    def save(self, chapter_number, output_dir):
        comicbook_dir = self.get_comicbook_dir(output_dir)
        chapter = self.get_chapter(chapter_number)
        chapter_dir, _ = chapter.save(comicbook_dir)
        return chapter_dir

    def save_as_pdf(self, chapter_number, output_dir):
        comicbook_dir = self.get_comicbook_dir(output_dir)
        chapter = self.get_chapter(chapter_number)
        pdf_path = chapter.save_as_pdf(comicbook_dir)
        return pdf_path


class Chapter():
    image_download_pool = None

    def __init__(self, chapter_number, comicbook_crawler):
        self.crawler = comicbook_crawler
        self.chapter_number = chapter_number

    @classmethod
    def init(cls, worker=4):
        cls.image_download_pool = ThreadPoolExecutor(max_workers=worker)

    @classmethod
    def get_pool(cls):
        if cls.image_download_pool is None:
            cls.image_download_pool = ThreadPoolExecutor(max_workers=4)
        return cls.image_download_pool

    @property
    def title(self):
        return self.crawler.get_chapter_title(self.chapter_number)

    @property
    def image_urls(self):
        return self.crawler.get_chapter(self.chapter_number).image_urls

    def __repr__(self):
        return """<Chapter>
title={title}
chapter_number={chapter_number}
</Chapter>""".format(title=self.title, chapter_number=self.chapter_number)

    def get_chapter_images(self):
        image_urls = self.crawler.get_chapter_image_urls(self.chapter_number)
        return [ImageInfo(image_url) for image_url in image_urls]

    def save(self, output_dir):
        chapter_dir = os.path.join(output_dir, "{} {}".format(self.chapter_number, self.title))
        if not os.path.exists(chapter_dir):
            os.makedirs(chapter_dir)

        future_list = []
        for idx, image in enumerate(self.get_chapter_images(), start=1):
            ext = ImageInfo.find_suffix(image.image_url)
            target_path = os.path.join(chapter_dir, "{}.{}".format(idx, ext))
            future = self.get_pool().submit(image.save, target_path=target_path)
            future_list.append(future)
        return chapter_dir, future_list

    def save_as_pdf(self, output_dir):
        from .utils.img2pdf import image_dir_to_pdf
        # 等全部图片下载完成
        chapter_dir, future_list = self.save(output_dir)
        for future in future_list:
            try:
                future.result()
            except Exception as e:
                warnings.warn(str(e))

        pdf_path = os.path.join(output_dir, "{} {}.pdf".format(self.chapter_number, self.title))
        image_dir_to_pdf(img_dir=chapter_dir,
                         output=pdf_path,
                         sort_by=lambda x: int(x.split('.')[0]))
        return pdf_path


class ImageInfo():
    session = requests.Session()
    TIMEOUT = 30

    def __init__(self, image_url):
        self.image_url = image_url

    def __repr__(self):
        return """<ImageInfo>
image_url={image_url}
</ImageInfo>""".format(image_url=self.image_url)

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
        cache_file = ImageCache.get_cache_path(self.image_url)
        shutil.copyfile(cache_file, target_path)
