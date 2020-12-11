import re
import logging
from urllib.parse import urljoin
import json

from bs4 import BeautifulSoup
from ..crawlerbase import CrawlerBase

logger = logging.getLogger(__name__)


class C36mhCrawler(CrawlerBase):

    SITE = "36mh"
    SITE_INDEX = 'https://www.36mh.net/'
    SOURCE_NAME = "36漫画网"
    LOGIN_URL = SITE_INDEX

    DEFAULT_COMICID = 'quanzhifashi'
    DEFAULT_SEARCH_NAME = '全职法师'
    DEFAULT_TAG = "rexue"

    def __init__(self, comicid=None):
        self.comicid = comicid
        super().__init__()

    @property
    def source_url(self):
        return self.get_source_url(self.comicid)

    def get_source_url(self, comicid):
        return urljoin(self.SITE_INDEX, "/manhua/{}/".format(comicid))

    def get_soup(self, url):
        response = self.send_request('get', url)
        html = response.content.decode('utf-8')
        soup = BeautifulSoup(html, 'html.parser')
        return soup

    def get_comicbook_item(self):
        soup = self.get_soup(self.source_url)
        name = soup.find('div', {'class': 'book-title'}).h1.text.strip()
        author = ''
        tag_id = ''
        tag_name = ''
        status = ''
        for span in soup.find('ul', {'class': 'detail-list cf'}).find_all('span'):
            if not span.strong:
                continue
            text = span.strong.text
            if '漫画作者' in text:
                author = span.a.text.strip()
            elif '漫画剧情' in text:
                tag_id = re.search(r'/list/(.*?)/', span.a.get('href')).group(1)
                tag_name = span.a.text.strip()
            elif '漫画状态' in text:
                status = span.a.text.strip()

        desc = soup.find('div', {'id': 'intro-all'}).p.text.strip()
        cover_image_url = soup.find('p', {'class': 'cover'}).img.get('src')
        book = self.new_comicbook_item(name=name,
                                       desc=desc,
                                       cover_image_url=cover_image_url,
                                       author=author,
                                       status=status,
                                       source_url=self.source_url)
        if tag_id:
            book.add_tag(name=tag_name, tag=tag_id)

        li_list = soup.find('ul', {'id': 'chapter-list-4'}).find_all('li')
        for chapter_number, li in enumerate(li_list, start=1):
            href = li.a.get('href')
            url = urljoin(self.SITE_INDEX, href)
            title = li.a.text.strip()
            book.add_chapter(chapter_number=chapter_number,
                             source_url=url,
                             title=title)
        return book

    def get_chapter_item(self, citem):
        html = self.get_html(citem.source_url)
        chapterPath = re.search(r'var chapterPath = "(.*?)";', html).group(1)
        chapterImages = re.search(r'var chapterImages = (\[.*?\]);', html).group(1)
        prefix = 'https://res.xiaoqinre.com/'
        image_urls = []
        for i in json.loads(chapterImages):
            image_url = prefix + chapterPath + i
            image_urls.append(image_url)
        return self.new_chapter_item(chapter_number=citem.chapter_number,
                                     title=citem.title,
                                     image_urls=image_urls,
                                     source_url=citem.source_url)

    def latest(self, page=1):
        url = urljoin(self.SITE_INDEX, "/update/%s/" % page)
        soup = self.get_soup(url)
        result = self.new_search_result_item()
        for li in soup.find('ul', {'id': 'contList'}).find_all('li'):
            href = li.a.get('href')
            comicid = self.get_comicid_by_url(href)
            source_url = urljoin(self.SITE_INDEX, href)
            name = li.a.get('title')
            cover_image_url = li.a.img.get('src')
            result.add_result(comicid=comicid,
                              name=name,
                              cover_image_url=cover_image_url,
                              source_url=source_url)
        return result

    def get_tags(self):
        soup = self.get_soup(self.SITE_INDEX)
        tags = self.new_tags_item()
        for div in soup.find_all('div', {'class': 'filter-item clearfix'}):
            category = div.label.text
            for li in div.find_all('li'):
                name = li.a.text
                href = li.a.get('href')
                r = re.search(r'/list/(.*?)/', href)
                if not r:
                    continue
                tag_id = r.group(1)
                tags.add_tag(category=category, name=name, tag=tag_id)
        return tags

    def get_tag_result(self, tag, page=1):
        if tag:
            url = urljoin(self.SITE_INDEX, "/list/%s/%s" % (tag, page))
        else:
            url = urljoin(self.SITE_INDEX, "/list/")

        soup = self.get_soup(url)
        result = self.new_search_result_item()
        for li in soup.find('ul', {'id': 'contList'}).find_all('li'):
            href = li.a.get('href')
            comicid = self.get_comicid_by_url(href)
            source_url = urljoin(self.SITE_INDEX, href)
            name = li.a.get('title')
            cover_image_url = li.a.img.get('src')
            result.add_result(comicid=comicid,
                              name=name,
                              cover_image_url=cover_image_url,
                              source_url=source_url)
        return result

    def get_comicid_by_url(self, url):
        return re.search(r'/manhua/(.*?)/', url).group(1)
