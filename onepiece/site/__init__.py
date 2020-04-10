import requests
import datetime
import pickle
import time

from ..exceptions import URLException
from ..logs import logger


class ComicBookItem():
    FIELDS = ["name", "desc", "tag", "cover_image_url", "author",
              "source_url", "source_name", "crawl_time", "chapters"]

    def __init__(self, name=None, desc=None, tag=None, cover_image_url=None,
                 author=None, source_url=None, source_name=None,
                 crawl_time=None, chapters=None):
        self.name = name or ""
        self.desc = desc or ""
        self.tag = tag or ""
        self.cover_image_url = cover_image_url or ""
        self.author = author or ""
        self.source_url = source_url or ""
        self.source_name = source_name or ""
        self.crawl_time = crawl_time or datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # [{"chapter_number": 1, "title": "xx"}, ]
        self.chapters = sorted(chapters, key=lambda x: x["chapter_number"]) if chapters else []

    @classmethod
    def create_chapter(cls, chapter_number, title):
        return {"chapter_number": chapter_number, "title": title}

    def create_chapters(cls, param_list):
        return [cls.create_chapter(**param) for param in param_list]

    def to_dict(self):
        return {field: getattr(self, field) for field in self.FIELDS}


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


class ComicBookCrawlerBase():

    TIMEOUT = 30
    DEFAULT_HEADERS = {
        'User-Agent': ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/65.0.3325.146 Safari/537.36')
    }

    SOURCE_NAME = "未知"
    SITE = ""

    _session = None

    DRIVER_PATH = None
    DRIVER_TYPE = None
    DEFAULT_DRIVER_TYPE = "Chrome"
    SUPPORT_DRIVER_TYPE = frozenset(["Firefox", "Chrome", "Opera", "Ie", "Edge"])

    @classmethod
    def set_session(cls, session):
        cls._session = session

    @classmethod
    def get_session(cls):
        if cls._session is None:
            session = requests.session()
            session.headers.update(cls.DEFAULT_HEADERS)
            cls._session = session
        return cls._session

    @classmethod
    def export_session(cls, path):
        session = cls.get_session()
        with open(path, "wb") as f:
            pickle.dump(session, f)

    @classmethod
    def load_session(cls, path):
        with open(path, "rb") as f:
            session = pickle.load(f)
            cls.set_session(session)

    @classmethod
    def send_request(cls, method, url, **kwargs):
        kwargs.setdefault('headers', cls.DEFAULT_HEADERS)
        kwargs.setdefault('timeout', cls.TIMEOUT)
        session = cls.get_session()
        try:
            return session.request(method=method, url=url, **kwargs)
        except Exception as e:
            msg = "URL链接访问异常！ url={}".format(url)
            raise URLException(msg) from e

    @classmethod
    def get_html(cls, url):
        response = cls.send_request("GET", url)
        return response.text

    @classmethod
    def get_json(cls, url):
        response = cls.send_request("GET", url)
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

    @classmethod
    def search(cls, name):
        """
        :return SearchResultItem list:
        """
        return []

    @classmethod
    def login(cls):
        pass

    @classmethod
    def selenium_login(cls, login_url, check_login_status_func):
        if check_login_status_func():
            logger.info("已登录")
            return

        driver = cls.create_driver()
        driver.get(login_url)

        while True:
            logger.info("等待登录")
            for cookie in driver.get_cookies():
                cls.get_session().cookies.set(name=cookie["name"],
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

    @classmethod
    def create_driver(cls):
        assert cls.DRIVER_PATH, "必须设置 DRIVER_PATH"

        driver_type = cls.DRIVER_TYPE or cls.DEFAULT_DRIVER_TYPE

        assert driver_type in cls.SUPPORT_DRIVER_TYPE, "DRIVER_TYPE 必须为: {}"\
            .format(",".join(cls.SUPPORT_DRIVER_TYPE))

        from selenium import webdriver
        driver_cls = getattr(webdriver, driver_type)
        return driver_cls(cls.DRIVER_PATH)
