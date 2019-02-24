import requests


class ComicbookCrawlerException(Exception):
    pass


class NotFoundError(ComicbookCrawlerException):
    pass


class ComicbookNotFound(NotFoundError):
    pass


class ChapterSourceNotFound(NotFoundError):
    pass


class URLException(ComicbookCrawlerException):
    pass


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

    def __init__(self, **kwargs):
        self.session = requests.session()

    def set_session(self, session):
        self.session = session

    def send_request(self, url, **kwargs):
        kwargs.setdefault('headers', self.DEFAULT_HEADERS)
        kwargs.setdefault('timeout', self.TIMEOUT)
        try:
            return self.session.get(url, **kwargs)
        except Exception as e:
            msg = "URL链接访问异常！ url={}".format(url)
            raise URLException(msg) from e

    def get_html(self, url):
        response = self.send_request(url)
        return response.text

    @classmethod
    def _get_html(cls, url, **kwargs):
        kwargs.setdefault('headers', cls.DEFAULT_HEADERS)
        response = cls.DEAFULT_SESSION.get(url, **kwargs)
        return response.text

    def get_json(self, url):
        response = self.send_request(url)
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
    def search(self, name):
        """
        :return SearchResultItem list:
        """
        return []

    def login(self):
        pass
