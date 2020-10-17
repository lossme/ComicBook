import re
import base64
import json
import logging
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from ..crawlerbase import CrawlerBase

logger = logging.getLogger(__name__)


class QQCrawler(CrawlerBase):

    SITE = "qq"
    SITE_INDEX = 'https://ac.qq.com/'
    LOGIN_URL = SITE_INDEX

    SOURCE_NAME = '腾讯漫画'

    CHAPTER_JSON_STR_PATTERN = re.compile(r'("chapter":{.*)')
    DEFAULT_COMICID = 505430
    DEFAULT_SEARCH_NAME = '海贼王'
    DEFAULT_TAG = 'theme_105'

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
        book = self.new_comicbook_item(name=name,
                                       desc=desc,
                                       tag=tag,
                                       cover_image_url=cover_image_url,
                                       author=author,
                                       source_url=self.source_url)
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

    def parser_chapter_page(self, chapter_page_html, source_url=None):
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

        json_str = "{" + self.CHAPTER_JSON_STR_PATTERN.search(json_str_part).group(1)
        data = json.loads(json_str)
        title = data["chapter"]["cTitle"]
        chapter_number = data["chapter"]["cSeq"]
        image_urls = [item['url'] for item in data["picture"]]
        return self.new_chapter_item(chapter_number=chapter_number,
                                     title=title,
                                     image_urls=image_urls,
                                     source_url=source_url)

    def search(self, name, page=1, size=None):
        url = "https://ac.qq.com/Comic/searchList/search/{}/page/{}".format(name, page)
        soup = self.get_soup(url)
        result = self.new_search_result_item()
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
        result = self.new_search_result_item()
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

    def get_tags(self):
        tags = self.new_tags_item()
        url = 'https://ac.qq.com/Comic/all/search/hot/page/1'
        html = self.get_html(url)
        soup = BeautifulSoup(html, 'html.parser')
        for div in soup.find_all('div', {'class': 'ret-tags-type'}):
            category = div.h3.text
            if category == '标签':
                continue
            for a in div.find_all('a'):
                name = a.get('title')
                tag_id = a.get('id', '')
                tags.add_tag(category=category, name=name, tag=tag_id)
        tag_str = re.search(r'var tagList = "(.*?)"', html).group(1)
        for i in tag_str.split('|'):
            tag_id, name = i.split('#')
            tags.add_tag(category='标签', name=name, tag='theme_%s' % tag_id)
        return tags

    def get_tag_result(self, tag, page=1):
        if not tag:
            url = 'https://ac.qq.com/Comic/all/search/hot/page/%s' % page
        else:
            # url = "https://ac.qq.com/Comic/all/theme/%s/finish/%s/search/hot/vip/%s/page/%s"
            url = "https://ac.qq.com/Comic/all"
            params = {}
            for i in tag.split(','):
                key, tag_id = i.split('_', 1)
                params[key] = tag_id
            if 'theme' in params:
                url += "/theme/%s" % params['theme']
            if 'finish' in params:
                url += "/finish/%s" % params['finish']
            url += "/search/hot"
            if 'vip' in params:
                url += "/vip/%s" % params['vip']
            url += "/page/%s" % page
        soup = self.get_soup(url)
        result = self.new_search_result_item()
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
