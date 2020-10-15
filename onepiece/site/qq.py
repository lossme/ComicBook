import re
import base64
import json
from urllib.parse import urljoin

from ..crawlerbase import (
    CrawlerBase,
    ChapterItem,
    ComicBookItem,
    SearchResultItem
)
from ..exceptions import ComicbookNotFound


class QQCrawler(CrawlerBase):

    SITE = "qq"
    SITE_INDEX = 'https://ac.qq.com/'
    LOGIN_URL = SITE_INDEX

    SOURCE_NAME = '腾讯漫画'

    CHAPTER_JSON_STR_PATTERN = re.compile(r'("chapter":{.*)')
    DEFAULT_COMICID = 505430
    DEFAULT_SEARCH_NAME = '海贼王'

    def __init__(self, comicid=None):
        super().__init__()
        self.comicid = comicid

    @property
    def source_url(self):
        return self.get_source_url(self.comicid)

    def get_source_url(self, comicid):
        return 'https://ac.qq.com/Comic/ComicInfo/id/{}'.format(comicid)

    def get_index_page(self):
        if self.index_page is None:
            index_page = self.get_html(self.source_url)
            self.index_page = index_page
        return self.index_page

    def get_comicbook_item(self):
        # https://ac.qq.com/Comic/ComicInfo/id/505430
        soup = self.get_soup(self.source_url)
        name = soup.h2.text.strip()
        desc = soup.find('p', {'class': 'works-intro-short ui-text-gray9'}).text.strip()
        description = soup.find('meta', {'name': 'Description'}).get('content').strip()
        tag = re.search(r"的标签：(.*?)", description, re.S).group(1).strip()
        cover_image_url = soup.find('div', {'class': 'works-cover ui-left'}).img.get('src')
        author = soup.find('span', {'class': 'first'}).em.text.strip()
        book = ComicBookItem(name=name,
                             desc=desc,
                             tag=tag,
                             cover_image_url=cover_image_url,
                             author=author,
                             source_url=self.source_url,
                             source_name=self.SOURCE_NAME)
        ol = soup.find('ol', {'class': 'works-chapter-list'})
        for idx, a in enumerate(ol.find_all('a'), start=1):
            title = a.get('title')
            url = a.get('href')
            chapter_number = idx
            chapter_page_url = urljoin(self.SITE_INDEX, url)
            book.add_chapter(chapter_number=chapter_number, title=title, source_url=chapter_page_url)
        return book

    def get_chapter_item(self, citem):
        chapter_page_html = self.get_html(citem.source_url)
        chapter_item = self.parser_chapter_page(chapter_page_html, source_url=citem.source_url)
        return chapter_item

    @classmethod
    def parser_chapter_page(cls, chapter_page_html, source_url=None):
        # 该方法只能解出部分数据，会缺失前面的一部分json字符串
        bs64_data = re.search(r"var DATA\s*=\s*'(.*?)'", chapter_page_html).group(1)
        for i in range(len(bs64_data)):
            try:
                json_str_part = base64.b64decode(bs64_data[i:]).decode('utf-8')
                break
            except Exception:
                pass
        else:
            raise

        json_str = "{" + cls.CHAPTER_JSON_STR_PATTERN.search(json_str_part).group(1)
        data = json.loads(json_str)
        title = data["chapter"]["cTitle"]
        chapter_number = data["chapter"]["cSeq"]
        image_urls = [item['url'] for item in data["picture"]]
        return ChapterItem(chapter_number=chapter_number,
                           title=title,
                           image_urls=image_urls,
                           source_url=source_url)

    def search(self, name, page=1, size=None):
        url = "https://ac.qq.com/Comic/searchList/search/{}/page/{}".format(name, page)
        soup = self.get_soup(url)
        result = SearchResultItem(site=self.SITE)
        ul = soup.find('ul', {'class': 'mod_book_list mod_all_works_list mod_of'})
        for li in ul.find_all('li'):
            href = li.a.get('href')
            comicid = href.strip('/').split('/')[-1]
            name = li.a.get('title')
            cover_image_url = li.img.get("data-original")
            source_url = self.get_source_url(comicid)
            result.add_result(comicid=comicid,
                              name=name,
                              cover_image_url=cover_image_url,
                              source_url=source_url)
        return result

    def latest(self, page=1):
        url = 'https://ac.qq.com/Comic/all/search/time/page/%s' % page
        soup = self.get_soup(url)
        result = SearchResultItem(site=self.SITE)
        for li in soup.find_all('li', {'class': 'ret-search-item clearfix'}):
            href = li.a.get('href')
            comicid = href.strip('/').split('/')[-1]
            name = li.a.get('title')
            cover_image_url = li.a.img.get('data-original')
            source_url = self.get_source_url(comicid)
            result.add_result(comicid=comicid,
                              name=name,
                              cover_image_url=cover_image_url,
                              source_url=source_url)
        return result

    def login(self):
        self.selenium_login(
            login_url=self.LOGIN_URL,
            check_login_status_func=self.check_login_status)

    def check_login_status(self):
        session = self.get_session()
        if session.cookies.get("nav_userinfo_cookie", domain="ac.qq.com"):
            return True
