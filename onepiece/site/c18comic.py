import re
import logging
from urllib.parse import urljoin

import execjs
from bs4 import BeautifulSoup

from ..crawlerbase import (
    CrawlerBase,
    ChapterItem,
    ComicBookItem,
    Citem,
    SearchResultItem)
from ..exceptions import ChapterNotFound, ComicbookNotFound

logger = logging.getLogger(__name__)


class C18comicCrawler(CrawlerBase):

    SITE = "18comic"
    SITE_INDEX = 'https://18comic.org/'
    SOURCE_NAME = "禁漫天堂"
    LOGIN_URL = SITE_INDEX

    DEFAULT_COMICID = 201118
    DEFAULT_COMIC_NAME = '騎馬的女孩好想被她騎!'

    def __init__(self, comicid=None):
        self.comicid = comicid
        super().__init__()

    @property
    def source_url(self):
        return self.get_source_url(self.comicid)

    def get_source_url(self, comicid):
        return urljoin(self.SITE_INDEX, "/album/{}/".format(comicid))

    def get_comicbook_item(self):
        html = self.get_html(self.source_url)
        soup = BeautifulSoup(html, 'html.parser')
        name = soup.find('div', {'itemprop': 'name'}).text.strip()
        author = ''
        desc = ''
        for i in soup.find_all('div', {'class': 'p-t-5 p-b-5'}):
            if '敘述：' in i.text:
                desc = i.text.strip().replace('\n', '').replace('敘述：', '', 1)
        for i in soup.find_all('div', {'class': 'tag-block'}):
            if '作者：' in i.text:
                author = i.text.strip().replace('\n', '').replace('作者：', '', 1)
        tag = ",".join([i.text for i in soup.find('span', {'itemprop': 'genre'}).find_all('a')])
        cover_image_url = soup.find('img', {'itemprop': 'image'}).get('src')
        citem_dict = {}
        res = soup.find('div', {'class': 'episode'})
        if not res:
            chapter_number = 1
            url = urljoin(self.SITE_INDEX, '/photo/{}/'.format(self.comicid))
            citem_dict[chapter_number] = Citem(
                chapter_number=chapter_number,
                source_url=url,
                title=str(chapter_number))
        else:
            a_list = res.find_all('a')
            for idx, a_soup in enumerate(a_list, start=1):
                chapter_number = idx
                for i in a_soup.find_all('span'):
                    i.decompose()
                title = a_soup.text.strip().replace('\n', ' ')
                url = a_soup.get('href')
                full_url = urljoin(self.SITE_INDEX, url)
                citem_dict[chapter_number] = Citem(
                    chapter_number=chapter_number,
                    source_url=full_url,
                    title=title)

        return ComicBookItem(name=name,
                             desc=desc,
                             tag=tag,
                             cover_image_url=cover_image_url,
                             author=author,
                             source_url=self.source_url,
                             source_name=self.SOURCE_NAME,
                             citem_dict=citem_dict)

    def get_chapter_item(self, citem):
        html = self.get_html(citem.source_url)
        soup = BeautifulSoup(html, 'html.parser')
        img_list = soup.find('div', 'row thumb-overlay-albums')\
            .find_all('img', {'id': re.compile(r'album_photo_\d+')})
        image_urls = []
        for img_soup in img_list:
            url = img_soup.get('data-original')
            if not url:
                url = img_soup.get('src')
            image_urls.append(url)
        return ChapterItem(chapter_number=citem.chapter_number,
                           title=citem.title,
                           image_urls=image_urls,
                           source_url=citem.source_url)

    def search(self, name, page=1, size=None):
        url = urljoin(
            self.SITE_INDEX,
            '/search/photos?search_query={}&page={}'.format(name, page)
        )
        html = self.get_html(url)
        soup = BeautifulSoup(html, 'html.parser')
        rv = []
        for div in soup.find_all('div', {'class': 'thumb-overlay'}):
            comicid = div.a.get('id').split('_')[-1]
            name = div.img.get('alt')
            cover_image_url = div.img.get('data-original')
            source_url = self.get_source_url(comicid)
            search_result_item = SearchResultItem(site=self.SITE,
                                                  comicid=comicid,
                                                  name=name,
                                                  cover_image_url=cover_image_url,
                                                  source_url=source_url)
            rv.append(search_result_item)
        return rv

    def login(self):
        self.selenium_login(login_url=self.LOGIN_URL,
                            check_login_status_func=self.check_login_status)

    def check_login_status(self):
        session = self.get_session()
        if session.cookies.get("remember", domain=".18comic.org"):
            return True
