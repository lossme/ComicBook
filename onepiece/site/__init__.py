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


HEADERS = {
    'User-Agent': ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
                   'Chrome/65.0.3325.146 Safari/537.36')
}


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


class ComicBookCrawlerBase():

    HEADERS = HEADERS
    TIMEOUT = 30

    source_name = "未知"
    site = ""

    def __init__(self, **kwargs):
        self.session = requests.session()
        # {int_chapter_number: Chapter}
        self._chapter_item_db = {}
        self._comicbook_item = None

    def set_session(self, session):
        self.session = session

    def send_request(self, url, **kwargs):
        kwargs.setdefault('headers', self.HEADERS)
        kwargs.setdefault('timeout', self.TIMEOUT)
        try:
            return self.session.get(url, **kwargs)
        except Exception as e:
            msg = "URL链接访问异常！ url={}".format(url)
            raise URLException(msg) from e

    def get_html(self, url):
        response = self.send_request(url)
        return response.text

    @staticmethod
    def _get_html(url):
        response = requests.get(url, headers=HEADERS)
        return response.text

    def get_json(self, url):
        response = self.send_request(url)
        return response.json()

    @property
    def comicbook_item(self):
        if self._comicbook_item is None:
            self._comicbook_item = self.get_comicbook_item()
        return self._comicbook_item

    def ChapterItem(self, chapter_number):
        if chapter_number not in self._chapter_item_db:
            chapter_item = self.get_chapter_item(chapter_number)
        self._chapter_item_db[chapter_number] = chapter_item
        return chapter_item

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

    def login(self):
        pass
