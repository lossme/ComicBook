import requests
import datetime

from ..exceptions import URLException


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
        self.chapters = sorted(chapters, key=lambda x: x["chapter_number"]) or []

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

    DEAFULT_SESSION = requests.session()
    _session = None

    @classmethod
    def set_session(cls, session):
        cls._session = session

    @classmethod
    def get_session(cls):
        return cls._session or cls.DEAFULT_SESSION

    @classmethod
    def send_request(cls, url, **kwargs):
        kwargs.setdefault('headers', cls.DEFAULT_HEADERS)
        kwargs.setdefault('timeout', cls.TIMEOUT)
        session = cls.get_session()
        try:
            return session.get(url, **kwargs)
        except Exception as e:
            msg = "URL链接访问异常！ url={}".format(url)
            raise URLException(msg) from e

    @classmethod
    def get_html(cls, url):
        response = cls.send_request(url)
        return response.text

    @classmethod
    def get_json(cls, url):
        response = cls.send_request(url)
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

    def login(self):
        pass
