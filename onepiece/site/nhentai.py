import logging
from urllib.parse import urljoin

from ..crawlerbase import CrawlerBase

logger = logging.getLogger(__name__)


class NhentaiCrawler(CrawlerBase):

    SITE = "nhentai"
    SITE_INDEX = 'https://nhentai.net/'
    SOURCE_NAME = "NHentai"
    LOGIN_URL = 'https://nhentai.net/login/?next=/'

    DEFAULT_COMICID = 331735
    DEFAULT_SEARCH_NAME = 'manga'
    DEFAULT_TAG = 'big-breasts'

    REQUIRE_JAVASCRIPT = True
    R18 = True

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
        cover_image_url = soup.find('div', {'id': 'cover'}).img.get('data-src')
        chapter_number = 1
        image_urls = []
        div_list = soup.find('div', {'id': 'thumbnail-container'}).find_all('div', {'class': 'thumb-container'})
        book = self.new_comicbook_item(name=name,
                                       desc=desc,
                                       cover_image_url=cover_image_url,
                                       author=author,
                                       source_url=self.source_url)
        for div in soup.find('section', {'id': 'tags'}).find_all('div', {'class': 'tag-container'}):
            for a in div.find('span', {'class': 'tags'}).find_all('a'):
                href = a.get('href', '')
                if href.startswith('/search'):
                    continue
                name, tag = href.strip('/').split('/')
                book.add_tag(name=tag, tag='%s_%s' % (name, tag))

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
        return self.new_chapter_item(chapter_number=citem.chapter_number,
                                     title=citem.title,
                                     image_urls=citem.image_urls,
                                     source_url=citem.source_url)

    def search(self, name, page=1, size=None):
        url = urljoin(
            self.SITE_INDEX,
            '/search/?q=%s&page=%s' % (name, page)
        )
        soup = self.get_soup(url)
        result = self.new_search_result_item()
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
        result = self.new_search_result_item()
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

    def get_tag_result(self, tag, page=1):
        if not tag:
            return self.latest(page=page)
        elif '_' in tag:
            name, tag = tag.split('_', 1)
            url = 'https://nhentai.net/%s/%s/popular' % (name, tag)
        else:
            url = 'https://nhentai.net/tag/%s/popular' % tag

        params = {'page': page}
        soup = self.get_soup(url, params=params)
        result = self.new_search_result_item()
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
