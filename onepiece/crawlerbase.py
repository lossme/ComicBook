import datetime
import time
import logging

from .exceptions import URLException
from .session import (
    Session,
    default_session
)


logger = logging.getLogger(__name__)


class ComicBookItem():
    FIELDS = ["name", "desc", "tag", "cover_image_url", "author",
              "source_url", "source_name", "crawl_time", "chapters"]

    def __init__(self, name=None, desc=None, tag=None, cover_image_url=None,
                 author=None, source_url=None, source_name=None,
                 crawl_time=None, citem_dict=None):
        self.name = name or ""
        self.desc = desc or ""
        self.tag = tag or ""
        self.cover_image_url = cover_image_url or ""
        self.author = author or ""
        self.source_url = source_url or ""
        self.source_name = source_name or ""
        self.crawl_time = crawl_time or datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # {1: Citem(chapter_number=1, title="xx", cid="xxx"}
        self.citem_dict = citem_dict or {}
        self.chapters = []
        for citem in sorted(citem_dict.values(), key=lambda x: x.chapter_number):
            self.chapters.append(
                {"title": citem.title, "chapter_number": citem.chapter_number}
            )

    def to_dict(self):
        return {field: getattr(self, field) for field in self.FIELDS}


class Citem():

    def __init__(self, chapter_number, title, **kwargs):
        self.chapter_number = chapter_number
        self.title = title
        for k, v in kwargs.items():
            setattr(self, k, v)


class ChapterItem():
    FIELDS = ["chapter_number", "title", "image_urls", "source_url"]

    def __init__(self, chapter_number, title, image_urls, source_url=None):
        self.chapter_number = chapter_number
        self.title = title or ""
        self.image_urls = image_urls or []
        self.source_url = source_url or ""

    def to_dict(self):
        return {field: getattr(self, field) for field in self.FIELDS}


class SearchResultItem():
    FIELDS = ["site", "comicid", "name", "cover_image_url", "source_url"]

    def __init__(self, site=None, comicid=None, name=None, cover_image_url=None, source_url=None):
        self.site = site or ""
        self.comicid = comicid or ""
        self.name = name or ""
        self.cover_image_url = cover_image_url or ""
        self.source_url = source_url or ""

    def to_dict(self):
        return {field: getattr(self, field) for field in self.FIELDS}


class CrawlerBase():

    SOURCE_NAME = "未知"
    SITE = ""

    DRIVER_PATH = None
    DRIVER_TYPE = None
    DEFAULT_DRIVER_TYPE = "Chrome"
    SUPPORT_DRIVER_TYPE = frozenset(["Firefox", "Chrome", "Opera", "Ie", "Edge"])
    _session = None

    def set_session(self, session):
        self._session = session

    def get_session(self):
        if self._session is None:
            self._session = default_session
        return self._session

    def export_session(self, path):
        session = self.get_session()
        session.export(path)

    def load_session(self, path):
        session = Session.load(path)
        self.set_session(session)

    def send_request(self, method, url, **kwargs):
        session = self.get_session()
        kwargs.setdefault('headers', session.DEFAULT_HEADERS)
        kwargs.setdefault('timeout', session.TIMEOUT)
        try:
            return session.request(method=method, url=url, **kwargs)
        except Exception as e:
            msg = "URL链接访问异常！ url={}".format(url)
            raise URLException(msg) from e

    def get_html(self, url):
        response = self.send_request("GET", url)
        return response.text

    def get_json(self, url):
        response = self.send_request("GET", url)
        return response.json()

    def get_comicbook_item(self):
        """
        :return ComicBookItem instance:
        """
        raise NotImplementedError

    def get_chapter_item(self, chapter_number):
        """
        :return ChapterItem instance:
        """
        raise NotImplementedError

    def search(self, name):
        """
        :return SearchResultItem list:
        """
        return []

    def login(self):
        pass

    def selenium_login(self, login_url, check_login_status_func):
        if check_login_status_func():
            logger.info("已登录")
            return

        driver = self.create_driver()
        driver.get(login_url)

        while True:
            logger.info("等待登录")
            for cookie in driver.get_cookies():
                self.get_session().cookies.set(name=cookie["name"],
                                               value=cookie["value"],
                                               path=cookie["path"],
                                               domain=cookie["domain"],
                                               secure=cookie["secure"])
            if check_login_status_func():
                logger.info("登录成功")
                break
            time.sleep(2)

        logger.info("关闭 driver")
        driver.close()

    def create_driver(self):
        assert self.DRIVER_PATH, "必须设置 DRIVER_PATH"

        driver_type = self.DRIVER_TYPE or self.DEFAULT_DRIVER_TYPE
        assert driver_type in self.SUPPORT_DRIVER_TYPE, "DRIVER_TYPE 必须为: {}"\
            .format(",".join(self.SUPPORT_DRIVER_TYPE))

        from selenium import webdriver
        driver_cls = getattr(webdriver, driver_type)
        return driver_cls(self.DRIVER_PATH)
