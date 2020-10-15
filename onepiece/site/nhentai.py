import logging
from urllib.parse import urljoin

from ..crawlerbase import (
    CrawlerBase,
    ChapterItem,
    ComicBookItem,
    SearchResultItem)

logger = logging.getLogger(__name__)


class NhentaiCrawler(CrawlerBase):

    SITE = "nhentai"
    SITE_INDEX = 'https://nhentai.net/'
    SOURCE_NAME = "NHentai"
    LOGIN_URL = 'https://nhentai.net/login/?next=/'

    DEFAULT_COMICID = 331735
    DEFAULT_SEARCH_NAME = 'manga'
    REQUIRE_JAVASCRIPT = True

    def __init__(self, comicid=None):
        self.comicid = comicid
        super().__init__()

    @property
    def source_url(self):
        return self.get_source_url(self.comicid)

    def get_source_url(self, comicid):
        return urljoin(self.SITE_INDEX, "/g/{}/".format(comicid))

    def get_comicbook_item(self):
        soup = self.get_soup(self.source_url)
        name = soup.h2.text.strip()
        author = ''
        desc = soup.h2.text.strip()
        tag = ''
        cover_image_url = soup.find('div', {'id': 'cover'}).img.get('data-src')
        chapter_number = 1
        image_urls = []
        div_list = soup.find('div', {'id': 'thumbnail-container'}).find_all('div', {'class': 'thumb-container'})
        book = ComicBookItem(name=name,
                             desc=desc,
                             tag=tag,
                             cover_image_url=cover_image_url,
                             author=author,
                             source_url=self.source_url,
                             source_name=self.SOURCE_NAME)
        for div in div_list:
            url = div.img.get('data-src').replace('t.nhentai', 'i.nhentai')
            url_split = url.rsplit('.', 1)
            url_split[-2] = url_split[-2].rstrip('t')
            image_urls.append('.'.join(url_split))
            book.add_chapter(chapter_number=chapter_number,
                             cid=self.comicid,
                             source_url=self.source_url,
                             image_urls=image_urls,
                             title=str(chapter_number))
        return book

    def get_chapter_item(self, citem):
        return ChapterItem(chapter_number=citem.chapter_number,
                           title=citem.title,
                           image_urls=citem.image_urls,
                           source_url=citem.source_url)

    def search(self, name, page=1, size=None):
        url = urljoin(
            self.SITE_INDEX,
            '/search/?q=%s&page=%s' % (name, page)
        )
        soup = self.get_soup(url)
        result = SearchResultItem(site=self.SITE)
        for div in soup.find_all('div', {'class': 'gallery'}):
            href = div.a.get('href')
            name = div.find('div', {'class': 'caption'}).text
            comicid = href.strip('/').split('/')[-1]
            cover_image_url = div.img.get('data-src')
            source_url = self.get_source_url(comicid)
            result.add_result(comicid=comicid,
                              name=name,
                              cover_image_url=cover_image_url,
                              source_url=source_url)
        return result

    def latest(self, page=1):
        url = urljoin(self.SITE_INDEX, '/?page=%s' % (page))
        soup = self.get_soup(url)
        result = SearchResultItem(site=self.SITE)
        for div in soup.find_all('div', {'class': 'gallery'}):
            href = div.a.get('href')
            name = div.find('div', {'class': 'caption'}).text
            comicid = href.strip('/').split('/')[-1]
            cover_image_url = div.img.get('data-src')
            source_url = self.get_source_url(comicid)
            result.add_result(comicid=comicid,
                              name=name,
                              cover_image_url=cover_image_url,
                              source_url=source_url)
        return result

    def login(self):
        self.selenium_login(login_url=self.LOGIN_URL,
                            check_login_status_func=self.check_login_status)

    def check_login_status(self):
        session = self.get_session()
        if session.cookies.get("sessionid", domain="nhentai.net"):
            return True
