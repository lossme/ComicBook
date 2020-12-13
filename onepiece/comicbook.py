import os
import re
import importlib
import datetime
import logging
import weakref
from collections import defaultdict

from .utils import safe_filename
from .utils import (
    ensure_file_dir_exists,
    find_all_image
)
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
    CHAPTER_NOT_CACHE_SITE = frozenset(['bilibili'])

    def __init__(self, site=None, comicid=None):
        if not site:
            site = self.get_site_by_url(comicid)
        if site not in self.CRAWLER_CLS_MAP:
            raise SiteNotSupport(f"SiteNotSupport site={site}")
        crawler_cls = self.CRAWLER_CLS_MAP[site]

        url = comicid or crawler_cls.DEFAULT_COMICID
        comicid = self.get_comicid_by_url(site=site, url=url)
        self.crawler = crawler_cls(comicid)
        self.image_downloader = ImageDownloader(site=site)

        # {ext_name: {chapter_number: Chapter}}
        self.chapter_cache = defaultdict(dict)
        self.chapter_desc = defaultdict(dict)

        self.crawler_time = None
        self.comicbook_item = None

    @classmethod
    def get_site_by_url(cls, url):
        if not url:
            return
        uri = re.sub('https?://', '', url)
        for crawler_cls in cls.CRAWLER_CLS_MAP.values():
            crawler_uri = re.sub('https?://', '', crawler_cls.SITE_INDEX)
            if uri.startswith(crawler_uri):
                return crawler_cls.SITE

    @classmethod
    def get_comicid_by_url(cls, site, url):
        if site not in cls.CRAWLER_CLS_MAP:
            return None
        crawler_cls = cls.CRAWLER_CLS_MAP[site]
        return crawler_cls.get_comicid_by_url(url)

    def start_crawler(self):
        if self.crawler_time is None:
            self.refresh()

    def refresh(self):
        self.comicbook_item = self.crawler.get_comicbook_item()
        self.crawler_time = datetime.datetime.now()
        for field in self.comicbook_item.FIELDS:
            setattr(self, field, getattr(self.comicbook_item, field))

        for ext_name in self.comicbook_item.citems:
            citems = self.comicbook_item.citems[ext_name]
            if not citems:
                self.chapter_desc[ext_name] = {
                    'last_chapter_number': 0,
                    'last_chapter_title': ''
                }
            else:
                last_chapter = max(citems.values(),
                                   key=lambda x: x.chapter_number)
                self.chapter_desc[ext_name] = {
                    'last_chapter_number': last_chapter.chapter_number,
                    'last_chapter_title': last_chapter.title
                }

    def get_last_chapter_number(self, ext_name=None):
        ext_name = ext_name or self.crawler.DEFAULT_EXT_NAME
        return self.chapter_desc.get(ext_name, {}).get('last_chapter_number', 0)

    def get_last_chapter_title(self, ext_name=None):
        ext_name = ext_name or self.crawler.DEFAULT_EXT_NAME
        return self.chapter_desc.get(ext_name, {}).get('last_chapter_title', '')

    def search(self, name=None, page=1, limit=None):
        return self.crawler.search(name, page=page, size=limit)

    def latest(self, page=1):
        return self.crawler.latest(page=page)

    def get_tags(self):
        return self.crawler.get_tags_from_cache()

    def get_tag_result(self, tag, page=1):
        tag_id = self.crawler.get_tag_id_by_name(tag)
        if tag_id:
            return self.crawler.get_tag_result(tag=tag_id, page=page)
        return self.crawler.get_tag_result(tag=tag, page=page)

    def to_dict(self):
        if self.crawler_time is None:
            self.start_crawler()
        return self.comicbook_item.to_dict()

    def Chapter(self, chapter_number, ext_name=None):
        ext_name = ext_name or self.crawler.DEFAULT_EXT_NAME
        if self.crawler_time is None:
            self.start_crawler()

        if chapter_number < 0:
            chapter_number = self.last_chapter_number + chapter_number + 1

        citems = self.comicbook_item.citems.get(ext_name, {})
        if chapter_number not in citems:
            msg = ChapterNotFound.TEMPLATE.format(site=self.crawler.SITE,
                                                  comicid=self.crawler.comicid,
                                                  chapter_number=chapter_number,
                                                  source_url=self.crawler.source_url)
            raise ChapterNotFound(msg)
        if self.crawler.SITE in self.CHAPTER_NOT_CACHE_SITE \
                or chapter_number not in self.chapter_cache[ext_name]:
            citem = citems[chapter_number]
            chapter_item = self.crawler.get_chapter_item(citem)
            self.chapter_cache[ext_name][chapter_number] = Chapter(
                comicbook_ref=weakref.ref(self),
                chapter_item=chapter_item,
                ext_name=ext_name)

        return self.chapter_cache[ext_name][chapter_number]


class Chapter():

    def __init__(self, comicbook_ref, chapter_item, ext_name=None):
        self.ext_name = ext_name
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

    def get_comicbook_dir_name(self):
        if self.ext_name:
            name = safe_filename('{} 【{}】'.format(self.comicbook.name, self.ext_name))
        else:
            name = safe_filename(self.comicbook.name)
        return name

    def get_chapter_image_dir(self, output_dir):
        first_dir = safe_filename(self.comicbook.source_name)
        second_dir = self.get_comicbook_dir_name()
        third_dir = safe_filename("{:>03} {}".format(self.chapter_item.chapter_number, self.chapter_item.title))
        chapter_dir = os.path.join(output_dir, first_dir, second_dir, third_dir)
        return chapter_dir

    def get_chapter_pdf_path(self, output_dir):
        first_dir = safe_filename(self.comicbook.source_name + ' pdf')
        second_dir = self.get_comicbook_dir_name()
        filename = safe_filename("{:>03} {}".format(self.chapter_number, self.title)) + ".pdf"
        pdf_path = os.path.join(output_dir, first_dir, second_dir, filename)
        return pdf_path

    def get_single_image_dir(self, output_dir):
        first_dir = safe_filename(self.comicbook.source_name + ' 长图')
        second_dir = self.get_comicbook_dir_name()
        third_dir = safe_filename("{:>03} {}".format(self.chapter_item.chapter_number, self.chapter_item.title))
        image_dir = os.path.join(output_dir, first_dir, second_dir, third_dir)
        return image_dir

    def get_zipfile_path(self, output_dir):
        first_dir = safe_filename(self.comicbook.source_name + ' zip')
        second_dir = self.get_comicbook_dir_name()
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
        if os.path.exists(pdf_path) and not self.images_has_modify(chapter_dir):
            return pdf_path
        ensure_file_dir_exists(pdf_path)
        image_dir_to_pdf(img_dir=chapter_dir,
                         target_path=pdf_path,
                         sort_by=lambda x: int(x.split('.')[0]))
        return pdf_path

    def images_has_modify(self, image_dir):
        crawler_time = self.comicbook.crawler_time.timestamp()
        images_latest_mtime = self.get_images_latest_mtime(image_dir)
        return images_latest_mtime > crawler_time

    def get_images_latest_mtime(self, image_dir):
        files = find_all_image(image_dir)
        if not files:
            return 0
        return max([os.path.getmtime(f) for f in files])

    def save_as_single_image(self, output_dir, quality=None, max_height=None):
        from .utils import image_dir_to_single_image
        chapter_dir = self.save(output_dir)
        image_dir = self.get_single_image_dir(output_dir)
        ensure_file_dir_exists(dirpath=image_dir)
        image_dir = image_dir_to_single_image(img_dir=chapter_dir,
                                              output_dir=image_dir,
                                              sort_by=lambda x: int(x.split('.')[0]),
                                              quality=quality,
                                              max_height=max_height)
        return image_dir

    def save_as_zip(self, output_dir):
        from .utils import image_dir_to_zipfile
        chapter_dir = self.save(output_dir)
        zipfile_path = self.get_zipfile_path(output_dir)
        if os.path.exists(zipfile_path) and not self.images_has_modify(chapter_dir):
            return output_dir
        ensure_file_dir_exists(zipfile_path)
        return image_dir_to_zipfile(chapter_dir, zipfile_path)
