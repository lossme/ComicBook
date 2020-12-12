import re
import logging
from urllib.parse import urljoin

from ..crawlerbase import CrawlerBase
from ..worker import concurrent_run

logger = logging.getLogger(__name__)


class NvshensCrawler(CrawlerBase):

    SITE = "nvshens"
    SITE_INDEX = 'https://www.nvshens.org/'
    SOURCE_NAME = "宅男女神"
    LOGIN_URL = SITE_INDEX
    R18 = True

    DEFAULT_COMICID = '34491'
    DEFAULT_SEARCH_NAME = ''
    DEFAULT_TAG = "toutiao"
    SITE_ENCODEING = 'utf-8'

    def __init__(self, comicid=None):
        super().__init__()
        self.comicid = comicid

    @property
    def source_url(self):
        return urljoin(self.SITE_INDEX, "/g/%s" % self.comicid)

    def get_comicbook_item(self):
        soup = self.get_soup(self.source_url)
        name = soup.h1.text
        author = ''
        desc = soup.find('div', {'id': 'ddesc'}).text.strip()
        page1_image_urls = self.get_book_image_urls(soup)
        book = self.new_comicbook_item(name=name,
                                       desc=desc,
                                       cover_image_url=page1_image_urls[0],
                                       author=author,
                                       source_url=self.source_url)
        max_page = self.get_book_max_page(soup)
        book.add_chapter(chapter_number=1, source_url=self.source_url, title=name,
                         page1_image_urls=page1_image_urls, max_page=max_page)
        return book

    def get_book_max_page(self, soup):
        max_page = 1
        for a in soup.find('div', {'id': 'pages'}).find_all('a'):
            try:
                page = int(a.text.strip())
            except ValueError:
                continue
            if page > max_page:
                max_page = page
        return max_page

    def get_book_image_urls(self, soup):
        return [img.get('src') for img in
                soup.find('ul', {'id': 'hgallery'}).find_all('img')]

    def get_chapter_item(self, citem):
        added_pages = set()
        max_page = citem.max_page
        image_urls = [i for i in citem.page1_image_urls]

        def _func(page):
            url = citem.source_url + '/%s.html' % page
            soup = self.get_soup(url)
            mpage = self.get_book_max_page(soup)
            urls = self.get_book_image_urls(soup)
            return [(mpage, urls)]

        while True:
            if added_pages:
                if max(added_pages) == max_page:
                    break
            zip_args = []
            for page in range(2, max_page):
                if page in added_pages:
                    continue
                zip_args.append((_func, dict(page=page)))
                added_pages.add(page)
            result = concurrent_run(zip_args=zip_args)
            if not result:
                break
            for (mpage, urls) in result:
                if mpage > max_page:
                    max_page = mpage
                image_urls.extend(urls)
        return self.new_chapter_item(chapter_number=citem.chapter_number,
                                     title=citem.title,
                                     image_urls=image_urls,
                                     source_url=citem.source_url)

    def get_comicid_by_url(self, url):
        return re.search(r'/g/(\d+)/?', url).group(1)

    def parse_book_list(self, soup):
        result = self.new_search_result_item()
        for li in soup.find_all('li', {'class': 'galleryli'}):
            href = li.a.get('href')
            source_url = urljoin(self.SITE_INDEX, href)
            comicid = self.get_comicid_by_url(href)
            name = li.a.img.get('alt')
            cover_image_url = li.a.img.get('data-original')
            result.add_result(comicid=comicid,
                              name=name,
                              cover_image_url=cover_image_url,
                              source_url=source_url)
        return result

    def get_tags(self):
        url = urljoin(self.SITE_INDEX, '/gallery/')
        soup = self.get_soup(url)
        tags = self.new_tags_item()

        for idx, div in enumerate(soup.find_all('div', {'class': 'tag_div'}), start=1):
            category = '分类%s' % idx
            for a in div.find_all('a'):
                name = a.text
                href = a.get('href')
                r = re.search(r'/gallery/(.*?)/', href)
                if not r:
                    continue
                tag_id = r.group(1)
                tags.add_tag(category=category, name=name, tag=tag_id)
        return tags

    def get_tag_result(self, tag, page):
        if not tag:
            url = urljoin(self.SITE_INDEX, "/gallery/")
        else:
            url = urljoin(self.SITE_INDEX, "/gallery/%s/" % tag)
        if page > 1:
            url += "%s.html" % page
        soup = self.get_soup(url)
        return self.parse_book_list(soup)

    def latest(self, page=1):
        return self.get_tag_result(tag=None, page=page)
