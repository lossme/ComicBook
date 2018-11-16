import collections
import requests


class ComicBookCrawlerBase():
    ComicBook = collections.namedtuple("ComicBook", ["name", "desc", "tag", "max_chapter_number"])
    Chapter = collections.namedtuple("Chapter", ["chapter_title", "image_urls"])

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

    def chapter(self, chapter_number):
        if chapter_number not in self._chapter_db:
            self._chapter_db[chapter_number] = self.get_chapter(chapter_number)
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

    def get_comicbook_name(self):
        """
        :return str comicbook_name:
        """
        return self.get_comicbook().name

    def get_comicbook_desc(self):
        return self.get_comicbook().name

    def get_comicbook_tag(self):
        return self.get_comicbook().tag

    def get_max_chapter_number(self):
        return self.get_comicbook().max_chapter_number

    def get_chapter_title(self, chapter_number):
        return self.get_chapter(chapter_number).chapter_title

    def get_chapter_image_urls(self, chapter_number):
        return self.get_chapter(chapter_number).image_urls
