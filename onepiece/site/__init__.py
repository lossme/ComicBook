import requests
from ..exceptions import ChapterSourceNotFound, URLException


HEADERS = {
    'User-Agent': ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
                   'Chrome/65.0.3325.146 Safari/537.36')
}


class ComicBookItem():

    def __init__(self, name=None, desc=None, tag=None, max_chapter_number=None,
                 cover_image_url=None, author=None, source_url=None):
        self.name = name or ""
        self.desc = desc or ""
        self.tag = tag or ""
        self.max_chapter_number = max_chapter_number or 0
        self.cover_image_url = cover_image_url or ""
        self.author = author or ""
        self.source_url = source_url or ""


class ChapterItem():

    def __init__(self, title, image_urls, source_url=None):
        self.title = title or ""
        self.image_urls = image_urls or []
        self.source_url = source_url or ""


class ComicBookCrawlerBase():

    HEADERS = HEADERS
    TIMEOUT = 30
    source_name = "未知"

    def __init__(self):
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
        except Exception:
            msg = "URL链接访问异常: {}".format(url)
            raise URLException(msg)

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
            try:
                self._chapter_item_db[chapter_number] = self.get_chapter_item(chapter_number)
            except ChapterSourceNotFound:
                msg = "没找到资源 {} {} {}".format(self.source_name, self.comicbook_item.name, chapter_number)
                raise ChapterSourceNotFound(msg)
        return self._chapter_item_db[chapter_number]

    def get_comicbook_item(self):
        """
        :return ComicBook instance:
        """
        raise NotImplementedError

    def get_chapter_item(self, chapter_number):
        """
        :return Chapter instance:
        """
        raise NotImplementedError

    def login(self):
        pass
