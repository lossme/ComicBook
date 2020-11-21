import re
import logging
import time
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from ..crawlerbase import CrawlerBase

logger = logging.getLogger(__name__)


class Mh1234Crawler(CrawlerBase):

    SITE = "mh1234"
    SITE_INDEX = 'https://www.mh1234.com/'
    SOURCE_NAME = "漫画1234"
    LOGIN_URL = SITE_INDEX

    DEFAULT_COMICID = '9683'
    DEFAULT_SEARCH_NAME = '斗罗大陆'
    DEFAULT_TAG = "1"

    def __init__(self, comicid=None):
        self.comicid = comicid
        super().__init__()

    @property
    def source_url(self):
        return self.get_source_url(self.comicid)

    def get_source_url(self, comicid):
        return urljoin(self.SITE_INDEX, "/comic/{}.html".format(comicid))

    def get_comicbook_item(self):
        soup = self.get_soup(self.source_url)

        name = soup.h1.text.strip()
        author = ''
        for p in soup.find('div', {'class':'info'}).find_all('p'):
            if '原著作者：' in p.text:
                author = p.text.replace('原著作者：', '').strip()
        desc = soup.find('div', {'class': 'introduction'}).p.text
        cover_image_url = soup.find('p', {'class': 'cover'}).img.get('src')
        book = self.new_comicbook_item(name=name,
                                       desc=desc,
                                       cover_image_url=cover_image_url,
                                       author=author,
                                       source_url=self.source_url)
        li_list = soup.find('ul', {'id': 'chapter-list-1'}).find_all('li')
        for chapter_number, li in enumerate(reversed(li_list), start=1):
            href = li.a.get('href')
            url = urljoin(self.SITE_INDEX, href)
            title = li.a.text.strip()
            book.add_chapter(chapter_number=chapter_number, 
                             source_url=url,
                             title=title)
        return book

    def get_chapter_item(self, citem):
        html = self.get_html(citem.source_url)
        chapterImages = re.search(r'var chapterImages = \[(.*?)\];', html).group(1)
        chapterPath = re.search(r'var chapterPath = "(.*?)";', html).group(1)
        image_urls = []
        for url in chapterImages.split(','):
            image_url = urljoin("https://img.wszwhg.net", chapterPath + url.strip('"'))
            image_urls.append(image_url)
        return self.new_chapter_item(chapter_number=citem.chapter_number,
                                     title=citem.title,
                                     image_urls=image_urls,
                                     source_url=citem.source_url)

    def latest(self, page=1):
        url = "https://www.mh1234.com/comic/one/page_recent.html"
        soup = self.get_soup(url)
        result = self.new_search_result_item()
        for li in soup.find('ul', {'id': 'w0'}).find_all('li'):
            href = li.a.get('href')
            comicid = self.get_comicid_url(href)
            source_url = urljoin(self.SITE_INDEX, href)
            name = li.a.text
            cover_image_url = li.a.get('i')
            result.add_result(comicid=comicid,
                              name=name,
                              cover_image_url=cover_image_url,
                              source_url=source_url)
        return result

    def get_comicid_url(self, url):
        return re.search(r'/comic/(\d+).html', url).group(1)

    def search(self, name, page, size=None):
        url = 'https://www.mh1234.com/search/?keywords=%s&page=%s' % (name, page)
        soup = self.get_soup(url)
        result = self.new_search_result_item()
        for li in soup.find('div', {'id': 'dmList'}).find_all('li'):
            href = li.a.get('href')
            comicid = self.get_comicid_url(href)
            name = li.img.get('alt')
            cover_image_url = li.img.get('original')
            source_url = self.get_source_url(comicid)
            result.add_result(comicid=comicid,
                              name=name,
                              cover_image_url=cover_image_url,
                              source_url=source_url)
        return result


    def get_tags(self):
        soup = self.get_soup(self.SITE_INDEX)
        tags = self.new_tags_item()
        category = '分类'
        for li in soup.find('ul', {'class': 'nav_menu'}).find_all('li')[1:]:
            href = li.a.get('href')
            name = li.a.text.strip()
            tag_id = href.strip('/').split('/')[-1]
            tags.add_tag(category=category, name=name, tag=tag_id)
        return tags

    def get_tag_result(self, tag, page=1):
        url = "https://www.mh1234.com/comic/list/%s/%s.html" % (tag, page)
        soup = self.get_soup(url)
        result = self.new_search_result_item()
        for li in soup.find('div', {'id': 'dmList'}).find_all('li'):
            href = li.a.get('href')
            comicid = self.get_comicid_url(href)
            name = li.img.get('alt')
            cover_image_url = li.img.get('original')
            source_url = self.get_source_url(comicid)
            result.add_result(comicid=comicid,
                              name=name,
                              cover_image_url=cover_image_url,
                              source_url=source_url)
        return result
