import datetime
import time
import logging

import execjs
from bs4 import BeautifulSoup

from .exceptions import URLException
from .session import (
    Session,
    default_session
)

logger = logging.getLogger(__name__)


class ComicBookItem():
    FIELDS = ["name", "desc", "tag", "cover_image_url", "author",
              "source_url", "source_name", "crawl_time", "chapters", "ext_chapters", "volumes"]

    def __init__(self, name=None, desc=None, tag=None, cover_image_url=None,
                 author=None, source_url=None, source_name=None,
                 crawl_time=None):
        self.name = name or ""
        self.desc = desc or ""
        self.tag = tag or ""
        self.cover_image_url = cover_image_url or ""
        self.author = author or ""
        self.source_url = source_url or ""
        self.source_name = source_name or ""
        self.crawl_time = crawl_time or datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # {1: Citem(chapter_number=1, title="xx", cid="xxx"}
        self.citems = {}
        self.ext_citems = {}
        self.volume_citems = {}

    def to_dict(self):
        return {field: getattr(self, field) for field in self.FIELDS}

    def add_chapter(self, chapter_number, title, source_url, **kwargs):
        self.citems[chapter_number] = Citem(
            chapter_number=chapter_number, title=title, source_url=source_url, **kwargs)

    def add_ext_chapter(self, chapter_number, title, source_url, **kwargs):
        self.ext_citems[chapter_number] = Citem(
            chapter_number=chapter_number, title=title, source_url=source_url, **kwargs)

    def add_volume(self, chapter_number, title, source_url, **kwargs):
        self.volume_citems[chapter_number] = Citem(
            chapter_number=chapter_number, title=title, source_url=source_url, **kwargs)

    def citems_to_list(self, citems):
        rv = []
        for citem in sorted(citems.values(), key=lambda x: x.chapter_number):
            rv.append(
                {
                    "title": citem.title,
                    "chapter_number": citem.chapter_number,
                    "source_url": citem.source_url,
                }
            )
        return rv

    @property
    def chapters(self):
        return self.citems_to_list(self.citems)

    @property
    def ext_chapters(self):
        return self.citems_to_list(self.ext_citems)

    @property
    def volumes(self):
        return self.citems_to_list(self.volume_citems)


class Citem():

    def __init__(self, **kwargs):
        self._kwargs = kwargs
        for k, v in kwargs.items():
            setattr(self, k, v)

    def to_dict(self):
        return self._kwargs


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

    def __init__(self, site=None):
        self.site = site or ""
        self._result = []

    def add_result(self, comicid, name, cover_image_url, source_url, site=None):
        if site is None:
            site = self.site
        item = Citem(site=self.site, comicid=comicid, name=name,
                     cover_image_url=cover_image_url, source_url=source_url)
        self._result.append(item)

    def __iter__(self):
        return iter(self._result)

    def to_dict(self):
        return [i.to_dict() for i in self._result]


class CrawlerBase():

    SOURCE_NAME = "未知"
    SITE = ""
    SITE_INDEX = ""

    DEFAULT_COMICID = None
    DEFAULT_SEARCH_NAME = ''

    DRIVER_PATH = None
    DRIVER_TYPE = None
    DEFAULT_DRIVER_TYPE = "Chrome"
    SUPPORT_DRIVER_TYPE = frozenset(["Firefox", "Chrome", "Opera", "Ie", "Edge"])
    REQUIRE_JAVASCRIPT = False

    def __init__(self):
        self._session = None
        if self.REQUIRE_JAVASCRIPT:
            try:
                execjs.get()
            except Exception:
                raise RuntimeError('请先安装nodejs。 https://nodejs.org/zh-cn/')

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
        kwargs.setdefault('headers', {'Referer': self.SITE_INDEX})
        kwargs.setdefault('timeout', session.TIMEOUT)
        try:
            return session.request(method=method, url=url, **kwargs)
        except Exception as e:
            msg = "URL链接访问异常！ url={}".format(url)
            raise URLException(msg) from e

    def get_html(self, url):
        response = self.send_request("GET", url)
        return response.text

    def get_soup(self, url):
        html = self.get_html(url)
        return BeautifulSoup(html, 'html.parser')

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

    def search(self, name, page=1, size=None):
        """
        :return SearchResultItem:
        """
        raise NotImplementedError

    def latest(self, page=1):
        """
        :return SearchResultItem:
        """
        raise NotImplementedError

    def login(self):
        pass

    def selenium_login(self, login_url, check_login_status_func):
        if check_login_status_func():
            logger.info("已登录")
            return

        logger.info("请在浏览器上完成登录")
        driver = self.create_driver()
        driver.get(login_url)
        while True:
            logger.info("等待登录")
            time.sleep(3)
            try:
                cookies = driver.get_cookies()
            except Exception:
                logger.exception('unknow error. driver quit.')
                driver.quit()
                return
            for cookie in cookies:
                self.get_session().cookies.set(name=cookie["name"],
                                               value=cookie["value"],
                                               path=cookie["path"],
                                               domain=cookie["domain"],
                                               secure=cookie["secure"])
            if check_login_status_func():
                logger.info("登录成功")
                driver.quit()
                break

    def create_driver(self):
        assert self.DRIVER_PATH, "必须设置 DRIVER_PATH"

        driver_type = self.DRIVER_TYPE or self.DEFAULT_DRIVER_TYPE
        assert driver_type in self.SUPPORT_DRIVER_TYPE, "DRIVER_TYPE 必须为: {}"\
            .format(",".join(self.SUPPORT_DRIVER_TYPE))

        from selenium import webdriver
        driver_cls = getattr(webdriver, driver_type)
        return driver_cls(self.DRIVER_PATH)
