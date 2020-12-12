import re
import logging
from urllib.parse import urljoin
import json

from ..crawlerbase import CrawlerBase

logger = logging.getLogger(__name__)


class Tuhao456Crawler(CrawlerBase):

    SITE = "tuhao456"
    SITE_INDEX = 'https://www.tuhao456.com/'
    SOURCE_NAME = "土豪漫画网"
    LOGIN_URL = SITE_INDEX

    DEFAULT_COMICID = '1831'
    DEFAULT_SEARCH_NAME = '和'
    DEFAULT_TAG = "t1"

    def __init__(self, comicid=None):
        self.comicid = comicid
        super().__init__()

    @property
    def source_url(self):
        return self.get_source_url(self.comicid)

    def get_source_url(self, comicid):
        return urljoin(self.SITE_INDEX, "/manhua/{}/".format(comicid))

    def get_comicbook_item(self):
        soup = self.get_soup(self.source_url)
        name = soup.find('div', {'class': 'cy_title'}).h1.text.strip()
        author = ''
        tags = []
        status = ''
        for div in soup.find_all('div', {'class': 'cy_xinxi'}):
            for span in div.find_all('span'):
                text = span.text
                if '作者：' in text:
                    author = text.replace('作者：', '')
                elif '状态：' in text:
                    status = text.replace('状态：', '')
                elif '类别：' in text:
                    for a in span.find_all('a'):
                        tag_name = a.text
                        tag_id = re.search(r'/sort/(.*?)/', a.get('href')).group(1)
                        tags.append((tag_id, tag_name))

        desc = soup.find('p', {'id': 'comic-description'}).text.strip()
        cover_image_url = soup.find('div', {'class': 'cy_info_cover'}).img.get('src')
        book = self.new_comicbook_item(name=name,
                                       desc=desc,
                                       cover_image_url=cover_image_url,
                                       author=author,
                                       status=status,
                                       source_url=self.source_url)
        for tag_id, tag_name in tags:
            book.add_tag(name=tag_name, tag=tag_id)

        li_list = soup.find('ul', {'id': 'mh-chapter-list-ol-0'}).find_all('li')
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
        js_str = re.search(r'var pages = (\{.*?\});', html).group(1)
        data = json.loads(js_str)
        image_urls = [url for url in data['page_url'].split('|')]
        return self.new_chapter_item(chapter_number=citem.chapter_number,
                                     title=citem.title,
                                     image_urls=image_urls,
                                     source_url=citem.source_url)

    def latest(self, page=1):
        if page > 1:
            self.new_search_result_item()
        url = urljoin(self.SITE_INDEX, '/update.html')
        soup = self.get_soup(url)
        result = self.new_search_result_item()
        for li in soup.find('div', {'class': 'cy_new_list'}).find_all('li'):
            href = li.a.get('href')
            comicid = self.get_comicid_by_url(href)
            source_url = urljoin(self.SITE_INDEX, href)
            name = li.a.get('title')
            cover_image_url = ''
            result.add_result(comicid=comicid,
                              name=name,
                              cover_image_url=cover_image_url,
                              source_url=source_url)
        return result

    def get_tags(self):
        url = urljoin(self.SITE_INDEX, "/sort/")
        soup = self.get_soup(url)
        tags = self.new_tags_item()
        for div in soup.find_all('div', {'class': 'cy_tag'}):
            category = div.span.text
            for li in div.find_all('li'):
                name = li.a.text
                href = li.a.get('href')
                r = re.search(r'/sort/(.*?)/', href)
                if not r:
                    continue
                tag_id = r.group(1)
                tags.add_tag(category=category, name=name, tag=tag_id)
        return tags

    def get_tag_result(self, tag, page=1):
        if tag:
            url = urljoin(self.SITE_INDEX, "/sort/%s/%s.html" % (tag, page))
        else:
            url = urljoin(self.SITE_INDEX, "/sort/%s.html" % page)

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

    def search(self, name, page, size=None):
        url = "https://www.tuhao456.com/sort/?key=%s&button=搜索" % name
        soup = self.get_soup(url)
        result = self.new_search_result_item()
        for ul in soup.find('div', {'class': 'cy_list_mh'}).find_all('ul'):
            name = ul.find('li', {'class': 'title'}).a.text
            cover_image_url = ul.find('a', {'class': 'pic'}).img.get('src')
            href = ul.find('a', {'class': 'pic'}).get('href')
            comicid = self.get_comicid_by_url(href)
            source_url = self.get_source_url(comicid)
            status = ul.find('li', {'class': 'zuozhe'}).a.text
            result.add_result(comicid=comicid,
                              name=name,
                              status=status,
                              cover_image_url=cover_image_url,
                              source_url=source_url)
        return result
