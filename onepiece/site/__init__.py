import collections
import requests
from ..exceptions import ChapterSourceNotFound


ComicBook = collections.namedtuple("ComicBook", ["name", "desc", "tag", "max_chapter_number"])
Chapter = collections.namedtuple("Chapter", ["title", "image_urls"])


class ComicBookCrawlerBase():

    HEADERS = {
        'User-Agent': ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/65.0.3325.146 Safari/537.36')
    }
    TIMEOUT = 30

    def __init__(self):
        self.session = requests.session()
        # {int_chapter_number: Chapter}
        self._chapter_db = {}
        self._comicbook = None

    def set_session(self, session):
        self.session = session

    def send_request(self, url, **kwargs):
        kwargs.setdefault('headers', self.HEADERS)
        kwargs.setdefault('timeout', self.TIMEOUT)
        return self.session.get(url, **kwargs)

    def get_html(self, url):
        response = self.send_request(url)
        return response.text

    def get_json(self, url):
        response = self.send_request(url)
        return response.json()

    @property
    def comicbook(self):
        if self._comicbook is None:
            self._comicbook = self.get_comicbook()
        return self._comicbook

    def Chapter(self, chapter_number):
        if chapter_number not in self._chapter_db:
            try:
                self._chapter_db[chapter_number] = self.get_chapter(chapter_number)
            except ChapterSourceNotFound:
                raise ChapterSourceNotFound("没找到资源 {} {}".format(self.comicbook.name, chapter_number))
        return self._chapter_db[chapter_number]

    def get_comicbook(self):
        """
        :return ComicBook instance:
        """
        raise NotImplementedError

    def get_chapter(self, chapter_number):
        """
        :return Chapter instance:
        """
        raise NotImplementedError
