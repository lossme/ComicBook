import re
import logging
from urllib.parse import urljoin
import json

from ..crawlerbase import CrawlerBase
from ..worker import concurrent_run

logger = logging.getLogger(__name__)


class C36mhCrawler(CrawlerBase):

    SITE = "177pic"
    SITE_INDEX = 'http://www.177pic.info/'
    SOURCE_NAME = "177漫画"
    LOGIN_URL = SITE_INDEX
    R18 = True

    DEFAULT_COMICID = '2020-12-3995736'
    DEFAULT_SEARCH_NAME = '中文'
    DEFAULT_TAG = "tt"

    def __init__(self, comicid=None):
        super().__init__()
        if comicid:
            self.comicid = self.get_comicid_by_url(comicid)
        else:
            self.comicid = comicid

    def get_comicid_by_url(self, url):
        comicid = re.search(r'(\d{4}[\/\-]\d{2}[\/\-]\d+)(?:\.html)?', url).group(1)
        return comicid.replace('/', '-')

    @property
    def source_url(self):
        return self.get_source_url(self.comicid.replace('-', '/'))

    def get_source_url(self, comicid):
        return urljoin(self.SITE_INDEX, 'html/%s.html' % comicid)

    def get_comicbook_item(self):
        soup = self.get_soup(self.source_url)
        name = soup.find('h1', {'class': 'entry-title'}).text.strip()
        author = ''
        desc = ''
        image_urls = self.get_image_urls_from_page(soup)
        book = self.new_comicbook_item(name=name,
                                       desc=desc,
                                       cover_image_url=image_urls[0],
                                       author=author,
                                       source_url=self.source_url)
        total_page = 1
        for a in soup.find('div', {'class': 'page-links'}).find_all('a', recursive=False):
            href = a.get('href')
            r = re.search(r'/html/.*?\.html/(\d+)/', href)
            if r:
                page = int(r.group(1))
                if page > total_page:
                    total_page = page
        book.add_chapter(chapter_number=1, source_url=self.source_url, title=name,
                         page1_image_urls=image_urls, total_page=total_page)
        return book

    def get_image_urls_from_page(self, soup):
        image_urls = []
        for p in soup.find('div', {'div', 'single-content'}).find_all('p', recursive=False):
            image_urls.append(p.img.get('data-lazy-src'))
        return image_urls

    def get_chapter_item(self, citem):
        image_urls = [i for i in citem.page1_image_urls]

        def _get_page_images(page):
            url = '%s/%s/' % (citem.source_url, page)
            soup = self.get_soup(url)
            return self.get_image_urls_from_page(soup=soup)
        zip_args = []
        for page in range(2, citem.total_page + 1):
            zip_args.append((_get_page_images, dict(page=page)))
        ret = concurrent_run(zip_args)
        image_urls.extend(ret)
        return self.new_chapter_item(chapter_number=citem.chapter_number,
                                     title=citem.title,
                                     image_urls=image_urls,
                                     source_url=citem.source_url)

    def paesr_book_list(self, url):
        soup = self.get_soup(url)
        result = self.new_search_result_item()
        for li in soup.find('main', {'id': 'main'}).find_all('article'):
            href = li.a.get('href')
            comicid = self.get_comicid_by_url(href)
            source_url = urljoin(self.SITE_INDEX, href)
            name = li.h2.a.text.strip()
            cover_image_url = li.img.get('src')
            result.add_result(comicid=comicid,
                              name=name,
                              cover_image_url=cover_image_url,
                              source_url=source_url)
        return result

    def latest(self, page=1):
        if page > 2:
            url = urljoin(self.SITE_INDEX, '/page/%s/' % page)
        else:
            url = self.SITE_INDEX
        return self.paesr_book_list(url)

    def get_tags(self):
        soup = self.get_soup(self.SITE_INDEX)
        tags = self.new_tags_item()
        category = '分类'
        for tag_id, tag_name in [
            ('tt', '中文H漫畫(Chinese)'),
            ('jj', '日本H漫画(Japanese)'),
            ('cg', '全彩CG(Full Color CG)'),
            ('cg/cg-cn', '全彩CG(中文全彩)'),
            ('cg/cg-jp', '全彩CG(日文全彩)'),
            ('cg/cg-no', '全彩CG(全彩CG(純圖無字)'),
        ]:
            tags.add_tag(category=category, name=tag_name, tag=tag_id)
        return tags

    def get_tag_result(self, tag, page=1):
        if not tag:
            return self.latest(page=page)
        if page > 1:
            url = urljoin(self.SITE_INDEX, "/html/category/%s/%s" % (tag, page))
        else:
            url = urljoin(self.SITE_INDEX, "/html/category/%s/" % tag)
        return self.paesr_book_list(url)

    def search(self, name, page, size=None):
        if page > 1:
            url = 'http://www.177pic.info/page/%s/?s=%s&cat=0' % (page, name)
        else:
            url = 'http://www.177pic.info/?s=%s&cat=0' % name
        return self.paesr_book_list(url)
