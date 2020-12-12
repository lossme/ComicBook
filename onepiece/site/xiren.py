import re
import logging
from urllib.parse import urljoin

from ..crawlerbase import CrawlerBase

logger = logging.getLogger(__name__)


class NvshensCrawler(CrawlerBase):

    SITE = "xiuren"
    SITE_INDEX = 'http://www.xiuren.org/'
    SOURCE_NAME = "秀人网"
    LOGIN_URL = SITE_INDEX
    R18 = True

    DEFAULT_COMICID = 'tuigirl-special-lilisha-double'
    DEFAULT_SEARCH_NAME = ''
    DEFAULT_TAG = "TuiGirl"
    SITE_ENCODEING = 'utf-8'

    def __init__(self, comicid=None):
        super().__init__()
        self.comicid = comicid

    @property
    def source_url(self):
        return urljoin(self.SITE_INDEX, "/%s.html" % self.comicid)

    def get_comicbook_item(self):
        soup = self.get_soup(self.source_url)
        name = soup.h1.text
        author = ''
        desc = ''
        image_urls = []
        for a in soup.find('div', {'class': 'post'}).find_all('a'):
            url = a.get('href')
            if url == 'http://www.xiuren.org/tuigirl-special-lilisha-double-download.html':
                continue
            image_urls.append(url)

        book = self.new_comicbook_item(name=name,
                                       desc=desc,
                                       cover_image_url=image_urls[0],
                                       author=author,
                                       source_url=self.source_url)
        book.add_chapter(chapter_number=1, source_url=self.source_url, title=name,
                         image_urls=image_urls)
        for a in soup.find('div', {'class': 'date'}).find_all('a'):
            href = a.get('href')
            if re.search(r'/tag/(.*?)\.html', href):
                name = a.text
                book.add_tag(name=name, tag='tag-%s' % name)
        return book

    def get_chapter_item(self, citem):
        return self.new_chapter_item(chapter_number=citem.chapter_number,
                                     title=citem.title,
                                     image_urls=citem.image_urls,
                                     source_url=citem.source_url)

    def parse_book_list(self, soup):
        result = self.new_search_result_item()
        for div in soup.find_all('div', {'class': 'loop'}):
            href = div.a.get('href')
            source_url = urljoin(self.SITE_INDEX, href)
            comicid = href.split('/')[-1].split('.')[0]
            name = div.a.get('title')
            cover_image_url = div.img.get('src')
            result.add_result(comicid=comicid,
                              name=name,
                              cover_image_url=cover_image_url,
                              source_url=source_url)
        return result

    def get_tags(self):
        soup = self.get_soup(self.SITE_INDEX)
        tags = self.new_tags_item()
        category = '分类'
        for li in soup.find('ul', {'class': 'in'}).find_all('li'):
            name = li.a.text
            href = li.a.get('href')
            r = re.search(r'/category/(.*?).html', href)
            if not r:
                continue
            tag_id = r.group(1)
            tags.add_tag(category=category, name=name, tag=tag_id)
        category = "热门标签"
        for li in soup.find('div', {'class': 'tag'}).find_all('li'):
            name = li.a.text
            if name == '套图下载':
                continue
            tags.add_tag(category=category, name=name, tag='tag-%s' % name)
        return tags

    def get_tag_result(self, tag, page):
        if not tag:
            url = urljoin(self.SITE_INDEX, "/")
            if page > 1:
                url += "page-%s.html" % page
        elif tag.startswith('tag-'):
            tag = tag.replace('tag-', '', 1)
            url = urljoin(self.SITE_INDEX, '/tag/%s.html' % tag)
            if page > 1:
                url = urljoin(self.SITE_INDEX, '/tag/%s-%s.html' % (tag, page))
        else:
            url = urljoin(self.SITE_INDEX, "/category/%s.html" % tag)
            if page > 1:
                url = urljoin(self.SITE_INDEX, "/category/%s-%s.html" % (tag, page))

        soup = self.get_soup(url)
        return self.parse_book_list(soup)

    def latest(self, page=1):
        return self.get_tag_result(tag=None, page=page)
