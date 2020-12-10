import re
import logging
from urllib.parse import urljoin
import base64
import json

from ..crawlerbase import CrawlerBase

logger = logging.getLogger(__name__)


class ManhuadbCrawler(CrawlerBase):

    SITE = "manhuadb"
    SITE_INDEX = 'https://www.manhuadb.com/'
    SOURCE_NAME = "漫画DB"
    LOGIN_URL = SITE_INDEX

    DEFAULT_COMICID = '160'
    DEFAULT_SEARCH_NAME = '海贼'
    DEFAULT_TAG = "c-46"
    DEFAULT_EXT_NAME = "连载"

    def __init__(self, comicid=None):
        self.comicid = comicid
        super().__init__()

    @property
    def source_url(self):
        return self.get_source_url(self.comicid)

    def get_source_url(self, comicid):
        return urljoin(self.SITE_INDEX, "/manhua/{}".format(comicid))

    def get_comicbook_item(self):
        soup = self.get_soup(self.source_url)
        name = soup.h1.text.strip()
        author = soup.find('ul', {'class': 'creators'}).a.text
        desc = soup.find('p', {'class': 'comic_story'}).text.strip()

        cover_image_url = ''
        cover_tag = soup.find('div', {'class': 'cover'})
        if cover_tag and cover_tag.img:
            cover_image_url = cover_tag.img.get('src')
        if not cover_image_url:
            cover_tag = soup.find('td', {'class': 'comic-cover'})
            if cover_tag and cover_tag.img:
                cover_image_url = cover_tag.img.get('src')

        status_tag = soup.find('a', {'class': 'comic-pub-state'})
        status = status_tag.text if status_tag else ''

        book = self.new_comicbook_item(name=name,
                                       desc=desc,
                                       status=status,
                                       cover_image_url=cover_image_url,
                                       author=author,
                                       source_url=self.source_url)
        for li in soup.find('ul', {'class': 'tags'}).find_all('li'):
            tag_name = li.text.strip()
            book.add_tag(name=tag_name, tag=tag_name)
        tablist = soup.find('ul', {'id': 'myTab'}).find_all('li', {'class': 'nav-item'})
        ext_names = [li.a.span.text for li in tablist]
        ol_list = soup.find_all('ol', {'class': 'links-of-books num_div'})
        for ext_name, ol in zip(ext_names, ol_list):
            for chapter_number, li in enumerate(ol.find_all('li'), start=1):
                href = li.a.get('href')
                url = urljoin(self.SITE_INDEX, href)
                title = li.a.text.strip()
                book.add_chapter(chapter_number=chapter_number,
                                 source_url=url,
                                 title=title,
                                 ext_name=ext_name)

        return book

    def get_chapter_item(self, citem):
        html = self.get_html(citem.source_url)
        s = re.search(r"<script>var img_data = '(.*?)';</script>", html).group(1)
        data = json.loads(base64.b64decode(s.encode()).decode())
        url_part = citem.source_url.split('/')[-1].split('.')[0].replace('_', '/')
        image_urls = []
        prefix = 'https://i1.manhuadb.com/ccbaike'
        for item in data:
            uri = item.get('img_webp') or item.get('img')
            image_url = '%s/%s/%s' % (prefix, url_part, uri)
            image_urls.append(image_url)
        return self.new_chapter_item(chapter_number=citem.chapter_number,
                                     title=citem.title,
                                     image_urls=image_urls,
                                     source_url=citem.source_url)

    def latest(self, page=1):
        if page == 1:
            url = 'https://www.manhuadb.com/update.html'
        else:
            url = "https://www.manhuadb.com/update_%s.html" % page
        soup = self.get_soup(url)
        result = self.new_search_result_item()
        for div in soup.find_all('div', {'class': 'comicbook-index'}):
            href = div.a.get('href')
            comicid = self.get_comicid_by_url(href)
            source_url = urljoin(self.SITE_INDEX, href)
            name = div.a.get('title')
            cover_image_url = div.a.img.get('data-original')
            result.add_result(comicid=comicid,
                              name=name,
                              cover_image_url=cover_image_url,
                              source_url=source_url)
        return result

    def get_tags(self):
        url = "https://www.manhuadb.com/manhua/list.html"
        soup = self.get_soup(url)
        tags = self.new_tags_item()
        category = '分类'
        for h5 in soup.find_all('h5', {'class': 'mb-2'}):
            category = h5.span.text
            for a in h5.parent.find_all('a'):
                name = a.text
                href = a.get('href')
                tag_id = re.search(r'/manhua/list-(.*?)\.html', href).group(1)
                tags.add_tag(category=category, name=name, tag=tag_id)
        return tags

    def get_tag_result(self, tag, page=1):
        tag_id = self.get_tag_id_by_name(tag)
        if tag_id:
            tag = tag_id
        tag = tag.replace(',', '-')
        if page == 1:
            url = "https://www.manhuadb.com/manhua/list-%s.html" % (tag)
        else:
            url = "https://www.manhuadb.com/manhua/list-%s-page-%s.html" % (tag, page)
        soup = self.get_soup(url)
        result = self.new_search_result_item()
        for div in soup.find_all('div', {'class': 'media comic-book-unit'}):
            href = div.a.get('href')
            comicid = self.get_comicid_by_url(href)
            name = div.h2.text.strip()
            cover_image_url = div.a.img.get('data-original')
            source_url = self.get_source_url(comicid)
            result.add_result(comicid=comicid,
                              name=name,
                              cover_image_url=cover_image_url,
                              source_url=source_url)
        return result

    def get_comicid_by_url(self, url):
        return re.search(r'/manhua/(\d+)', url).group(1)

    def search(self, name, page, size=None):
        url = "https://www.manhuadb.com/search?q=%s&p=%s" % (name, page)
        soup = self.get_soup(url)
        result = self.new_search_result_item()
        for div in soup.find_all('div', {'class': 'comicbook-index'}):
            href = div.a.get('href')
            comicid = self.get_comicid_by_url(href)
            name = div.h2.text.strip()
            cover_image_url = div.a.img.get('data-original')
            source_url = self.get_source_url(comicid)
            result.add_result(comicid=comicid,
                              name=name,
                              cover_image_url=cover_image_url,
                              source_url=source_url)
        return result
