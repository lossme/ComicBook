import requests
from ..exceptions import URLException


class ComicBookItem():
    FIELDS = ["name", "desc", "tag", "max_chapter_number", "cover_image_url", "author", "source_url", "source_name"]

    def __init__(self, name=None, desc=None, tag=None, max_chapter_number=None,
                 cover_image_url=None, author=None, source_url=None, source_name=None):
        self.name = name or ""
        self.desc = desc or ""
        self.tag = tag or ""
        self.max_chapter_number = max_chapter_number or 0
        self.cover_image_url = cover_image_url or ""
        self.author = author or ""
        self.source_url = source_url or ""
        self.source_name = source_name or ""

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
    FIELDS = ["site", "comicid", "name", "cover_image_url"]

    def __init__(self, site=None, comicid=None, name=None, cover_image_url=None):
        self.site = site
        self.comicid = comicid
        self.name = name
        self.cover_image_url = cover_image_url

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

    def __init__(self, **kwargs):
        self._session = requests.session()

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
