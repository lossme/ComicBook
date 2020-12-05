import re
import logging
from urllib.parse import urljoin

from ..crawlerbase import CrawlerBase

logger = logging.getLogger(__name__)


class Mh1234Crawler(CrawlerBase):

    SITE = "dm5"
    SITE_INDEX = 'https://www.dm5.com/'
    SOURCE_NAME = "DM5"
    LOGIN_URL = SITE_INDEX

    DEFAULT_COMICID = 'douluodalu'
    DEFAULT_SEARCH_NAME = '斗罗大陆'
    DEFAULT_TAG = "31"

    def __init__(self, comicid=None):
        self.comicid = comicid
        super().__init__()

    @property
    def source_url(self):
        return self.get_source_url(self.comicid)

    def get_source_url(self, comicid):
        return urljoin(self.SITE_INDEX, "/manhua-{}".format(comicid))

    def get_comicbook_item(self):
        html, soup = self.get_html_and_soup(self.source_url)
        soup = self.get_soup(self.source_url)
        div = soup.find('div', {'class': 'info'})
        name = re.search(r'var DM5_COMIC_MNAME="(.*?)";', html).group(1)

        desc = div.find('p', {'class': 'content'}).text.strip()
        author = div.find('p', {'class': 'subtitle'}).text.strip().replace('作者：', '')
        status = ''
        for span in div.find('p', {'class': 'tip'}).find_all('span'):
            if '状态：' in span.text:
                status = span.text.replace('状态：', '')
        cover_image_url = soup.find('div', {'class': 'cover'}).img.get('src')
        book = self.new_comicbook_item(name=name,
                                       desc=desc,
                                       status=status,
                                       cover_image_url=cover_image_url,
                                       author=author,
                                       source_url=self.source_url)
        li_list = soup.find('ul', {'id': 'detail-list-select-1'}).find_all('li')
        for chapter_number, li in enumerate(li_list, start=1):
            href = li.a.get('href')
            url = urljoin(self.SITE_INDEX, href)
            title = li.a.get('title')
            book.add_chapter(chapter_number=chapter_number,
                             source_url=url,
                             title=title)
        return book

    def get_chapter_item(self, citem):
        soup = self.get_soup(citem.source_url)
        image_urls = []
        div = soup.find('div', {'id': 'barChapter'})
        if div:
            image_urls = [img.get('data-src') for img in div.find_all('img', recursive=False)]
        return self.new_chapter_item(chapter_number=citem.chapter_number,
                                     title=citem.title,
                                     image_urls=image_urls,
                                     source_url=citem.source_url)

    def latest(self, page=1):
        url = 'https://www.dm5.com/manhua-new/'
        soup = self.get_soup(url)
        result = self.new_search_result_item()
        for li in soup.find('ul', {'class': 'mh-list col7'}).find_all('li'):
            href = li.h2.a.get('href')
            comicid = self.get_comicid_by_url(href)
            source_url = urljoin(self.SITE_INDEX, href)
            name = li.h2.a.text

            style = li.p.get('style')
            cover_image_url = re.search(r'background-image: url\((.*?)\)', style).group(1)
            result.add_result(comicid=comicid,
                              name=name,
                              cover_image_url=cover_image_url,
                              source_url=source_url)
        return result

    def get_tags(self):
        url = 'https://www.dm5.com/manhua-list/'
        soup = self.get_soup(url)
        tags = self.new_tags_item()
        category = '题材'
        for dd in soup.find('dl', {'id': 'tags'}).find_all('dd'):
            name = dd.a.text.strip()
            tag_id = dd.a.get('data-id')
            if tag_id:
                tags.add_tag(category=category, name=name, tag=tag_id)
        return tags

    def get_tag_result(self, tag, page=1):
        url = "https://www.dm5.com/manhua-list-tag%s-p%s/" % (tag, page)
        soup = self.get_soup(url)
        result = self.new_search_result_item()
        for li in soup.find('ul', {'class': 'mh-list col7'}).find_all('li'):
            href = li.h2.a.get('href')
            comicid = self.get_comicid_by_url(href)
            source_url = urljoin(self.SITE_INDEX, href)
            name = li.h2.a.text
            style = li.p.get('style')
            cover_image_url = re.search(r'background-image: url\((.*?)\)', style).group(1)
            result.add_result(comicid=comicid,
                              name=name,
                              cover_image_url=cover_image_url,
                              source_url=source_url)
        return result

    def get_comicid_by_url(self, url):
        return re.search(r'/manhua-(.*?)/', url).group(1)

    def search(self, name, page, size=None):
        url = "https://www.dm5.com/search?title=%s&page=%s" % (name, page)
        soup = self.get_soup(url)
        result = self.new_search_result_item()
        for li in soup.find('ul', {'class': 'mh-list col7'}).find_all('li'):
            href = li.h2.a.get('href')
            comicid = self.get_comicid_by_url(href)
            source_url = urljoin(self.SITE_INDEX, href)
            name = li.h2.a.text
            style = li.p.get('style')
            cover_image_url = re.search(r'background-image: url\((.*?)\)', style).group(1)
            result.add_result(comicid=comicid,
                              name=name,
                              cover_image_url=cover_image_url,
                              source_url=source_url)
        return result
