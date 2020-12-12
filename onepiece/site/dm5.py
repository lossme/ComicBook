import re
import logging
import json
from urllib.parse import urljoin

import jsbeautifier

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
            if '题材：' in span.text:
                tag_name = span.a.text

        cover_image_url = soup.find('div', {'class': 'cover'}).img.get('src')
        book = self.new_comicbook_item(name=name,
                                       desc=desc,
                                       status=status,
                                       cover_image_url=cover_image_url,
                                       author=author,
                                       source_url=self.source_url)
        book.add_tag(name=tag_name, tag=tag_name)
        try:
            li_list = soup.find('ul', {'id': 'detail-list-select-1'}).find_all('li')
        except Exception:
            li_list = []
        for chapter_number, li in enumerate(li_list, start=1):
            href = li.a.get('href')
            cid = href.replace('/', '').replace('m', '')
            url = urljoin(self.SITE_INDEX, href)
            title = li.a.get('title')

            book.add_chapter(chapter_number=chapter_number,
                             source_url=url,
                             cid=cid,
                             title=title)

        return book

    def get_chapter_item(self, citem):
        html, soup = self.get_html_and_soup(citem.source_url)
        image_urls = []
        div = soup.find('div', {'id': 'barChapter'})
        if div:
            image_urls = [img.get('data-src') for img in div.find_all('img', recursive=False)]
        else:
            sign = re.search(r'var DM5_VIEWSIGN="(.*?)";', html).group(1)
            dt = re.search(r'var DM5_VIEWSIGN_DT="(.*?)";', html).group(1)
            mid = re.search(r'var COMIC_MID = (\d*);', html).group(1)
            is_end_page = False
            page = 1
            api_url = "https://www.dm5.com/m%s/chapterfun.ashx" % citem.cid
            added = set()
            while not is_end_page:
                params = {
                    'cid': citem.cid,
                    '_cid': citem.cid,
                    'page': page,
                    'key': '',
                    'language': '1',
                    'gtk': '6',
                    '_mid': mid,
                    '_dt': dt,
                    '_sign': sign
                }
                html = self.get_html(api_url, params=params)
                js_str = jsbeautifier.beautify(html)
                key = re.search(r"var key = '(.*?)';", js_str).group(1)
                pvalue = re.search(r'var pvalue = (\[.*?\]);', js_str).group(1)
                pix = re.search(r'var pix = "(.*?)";', js_str).group(1)
                data = json.loads(pvalue)
                if len(data) >= 2:
                    is_end_page = data[0] == data[1]
                else:
                    is_end_page = True
                page += 1
                for i in data:
                    if i in added:
                        continue
                    added.add(i)
                    image_url = '%s%s?cid=%s&key=%s' % (pix, i, citem.cid, key)
                    image_urls.append(image_url)
        return self.new_chapter_item(chapter_number=citem.chapter_number,
                                     title=citem.title,
                                     image_urls=image_urls,
                                     source_url=citem.source_url)

    def latest(self, page=1):
        if page > 1:
            return self.new_search_result_item()
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
        result = self.new_search_result_item()
        if not tag.isdigit():
            tag = self.get_tag_id_by_name(tag)
        if not tag:
            url = "https://www.dm5.com/manhua-list-p%s/" % page
        else:
            url = "https://www.dm5.com/manhua-list-tag%s-p%s/" % (tag, page)
        soup = self.get_soup(url)
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
