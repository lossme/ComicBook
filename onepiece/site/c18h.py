import re
import logging
from urllib.parse import urljoin
import json

from bs4 import BeautifulSoup
from ..crawlerbase import CrawlerBase

logger = logging.getLogger(__name__)


class C36mhCrawler(CrawlerBase):

    SITE = "18h"
    SITE_INDEX = 'http://18h.mm-cg.com/'
    SOURCE_NAME = "18H漫画区"
    LOGIN_URL = SITE_INDEX
    R18 = True

    DEFAULT_COMICID = '18H_6809'
    DEFAULT_SEARCH_NAME = '中文'
    DEFAULT_TAG = "100"

    def __init__(self, comicid=None):
        super().__init__()
        self.comicid = comicid

    @property
    def source_url(self):
        return urljoin(self.SITE_INDEX, '%s.html' % self.comicid)

    def get_comicbook_item(self):
        html, soup = self.get_html_and_soup(self.source_url)
        name = soup.find('h1').text.strip()
        author = ''
        desc = ''
        image_urls = re.findall(r'Large_cgurl\[\d+\] = "(.*?)";', html)
        book = self.new_comicbook_item(name=name,
                                       desc=desc,
                                       cover_image_url=image_urls[0],
                                       author=author,
                                       source_url=self.source_url)
        book.add_chapter(chapter_number=1, source_url=self.source_url, title=name,
                         image_urls=image_urls)
        return book

    def get_chapter_item(self, citem):
        return self.new_chapter_item(chapter_number=citem.chapter_number,
                                     title=citem.title,
                                     image_urls=citem.image_urls,
                                     source_url=citem.source_url)

    def paesr_book_list(self, html):
        r = re.search(
            r"""<script>document.write\("<br>"\);document.getElementById\('main'\).innerHTML = '(.*?)';</script>""",
            html, re.S)
        if r:
            soup = BeautifulSoup(r.group(1))
        else:
            soup = BeautifulSoup(html, 'html.parser')

        result = self.new_search_result_item()
        added = set()
        for a in soup.find_all('a', {'class': 'aRF'}):
            href = a.get('href')
            comicid = href.split('/')[-1].split('.')[0]
            if comicid in added:
                continue
            added.add(comicid)
            source_url = urljoin(self.SITE_INDEX, href)
            name = a.img.get('alt')
            cover_image_url = a.img.get('src')
            result.add_result(comicid=comicid,
                              name=name,
                              cover_image_url=cover_image_url,
                              source_url=source_url)
        return result

    def latest(self, page=1):
        if page > 1:
            return self.new_search_result_item()
        html = self.get_html(self.SITE_INDEX)
        return self.paesr_book_list(html)

    def get_tags(self):
        soup = self.get_soup(self.SITE_INDEX)
        tags = self.new_tags_item()
        category = '分类'
        for a in soup.find('span', {'class': 'altto'}).find_all('a'):
            tag_id = a.get('href').split('/')[-1].split('.')[0]
            tag_name = a.text
            tags.add_tag(category=category, name=tag_name, tag=tag_id)
        return tags

    def get_tag_result(self, tag, page=1):
        if page > 1:
            return self.new_search_result_item()

        url = urljoin(self.SITE_INDEX, "18h_category/%s.html" % tag)
        html = self.get_html(url)
        return self.paesr_book_list(html)

    def search(self, name, page, size=None):
        if page > 1:
            return self.new_search_result_item()
        url = urljoin(self.SITE_INDEX, "/serch/18av_serch.html")
        data = {
            'form_serch_category': 'form_serch_18h',
            'key_myform': name,
            'form_page': page,
            'se_id[]': '本站精选漫画分类'
        }
        response = self.send_request('POST', url, data=data)
        html = response.text
        return self.paesr_book_list(html)
