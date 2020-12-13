import re
import logging
from urllib.parse import urljoin
import base64

from ..crawlerbase import CrawlerBase

logger = logging.getLogger(__name__)


class Mh160Crawler(CrawlerBase):

    SITE = "mh160"
    SITE_INDEX = 'https://www.mh160.xyz/'
    SOURCE_NAME = "漫画160"
    LOGIN_URL = SITE_INDEX

    DEFAULT_COMICID = '11106'
    DEFAULT_SEARCH_NAME = '和'
    DEFAULT_TAG = "rexue"
    SITE_ENCODEING = 'utf-8'
    COMICID_PATTERN = re.compile(r'/kanmanhua/([_a-zA-Z0-9\-]*)/?')

    def __init__(self, comicid=None):
        self.comicid = comicid
        super().__init__()

    @property
    def source_url(self):
        return self.get_source_url(self.comicid)

    def get_source_url(self, comicid):
        return urljoin(self.SITE_INDEX, "/kanmanhua/{}/".format(comicid))

    def get_comicbook_item(self):
        soup = self.get_soup(self.source_url)
        name = soup.find('div', {'class': 'mh-date-info-name'}).h4.text.strip()
        author_tag = soup.find('span', {'class': 'one'})
        author = author_tag.a.text if author_tag else ''
        desc = soup.find('div', {'id': 'workint'}).p.text.strip()
        cover_image_url = soup.find('div', {'class': 'mh-date-bgpic'}).img.get('src')
        status = ''
        for p in soup.find_all('p', {'class': 'works-info-tc'}):
            for span in p.find_all('span'):
                text = span.text
                if '状态：' in text:
                    status = span.em.text
        book = self.new_comicbook_item(name=name,
                                       desc=desc,
                                       status=status,
                                       cover_image_url=cover_image_url,
                                       author=author,
                                       source_url=self.source_url)

        li_list = soup.find('ul', {'id': 'mh-chapter-list-ol-0'}).find_all('li')
        for chapter_number, li in enumerate(reversed(li_list), start=1):
            href = li.a.get('href')
            url = urljoin(self.SITE_INDEX, href)
            title = li.a.text.strip()
            book.add_chapter(chapter_number=chapter_number,
                             source_url=url,
                             title=title)
        return book

    def get_pic_prefix(self, str_id):
        if int(str_id) > 884998:
            prefix = "https://mhpic88.miyeye.cn:20207"
        elif int(str_id) > 542724:
            prefix = "https://mhpic5.miyeye.cn:20208"
        else:
            prefix = "https://res.gezhengzhongyi.cn:20207"
        return prefix

    def get_chapter_item(self, citem):
        html = self.get_html(citem.source_url)
        str_id = re.search(r'qTcms_S_p_id="(.*?)"', html).group(1)
        prefix = self.get_pic_prefix(str_id)
        s = re.search(r'var qTcms_S_m_murl_e="(.*?)";', html).group(1)
        data = base64.b64decode(s.encode()).decode()
        image_urls = [prefix + url for url in data.replace('$qingtiandy$', '|').split('|')]
        return self.new_chapter_item(chapter_number=citem.chapter_number,
                                     title=citem.title,
                                     image_urls=image_urls,
                                     source_url=citem.source_url)

    def latest(self, page=1):
        if page > 1:
            self.new_search_result_item()
        url = urljoin(self.SITE_INDEX, '/kanmanhua/zaixian_recent.html')
        soup = self.get_soup(url)

        result = self.new_search_result_item()
        for li in soup.find('div', {'class': 'mh-search-result'}).find_all('li'):
            href = li.a.get('href')
            comicid = self.get_comicid_by_url(href)
            source_url = urljoin(self.SITE_INDEX, href)
            name = li.a.get('title')
            cover_image_url = li.a.img.get('src')
            status = li.find('p', {'class': 'mh-works-author'}).text
            result.add_result(comicid=comicid,
                              name=name,
                              status=status,
                              cover_image_url=cover_image_url,
                              source_url=source_url)
        return result

    def get_tags(self):
        url = urljoin(self.SITE_INDEX, "/kanmanhua/all/")
        soup = self.get_soup(url)
        tags = self.new_tags_item()
        for div in soup.find_all('div', {'class': 'mh-tags'}):
            category = div.h4.text
            for a in div.find_all('a'):
                name = a.text
                href = a.get('href')
                r = re.search(r'/kanmanhua/(.*?)/', href)
                if not r:
                    continue
                tag_id = r.group(1)
                tags.add_tag(category=category, name=name, tag=tag_id)
        return tags

    def get_tag_result(self, tag, page=1):
        if tag:
            url = urljoin(self.SITE_INDEX, "/kanmanhua/%s/" % tag)
        else:
            url = urljoin(self.SITE_INDEX, "/kanmanhua/all/")

        if page > 1:
            url += '%s.html' % page

        soup = self.get_soup(url)
        result = self.new_search_result_item()
        for li in soup.find('div', {'class': 'mh-search-result'}).ul.find_all('li'):
            href = li.a.get('href')
            comicid = self.get_comicid_by_url(href)
            source_url = urljoin(self.SITE_INDEX, href)
            name = li.a.get('title')
            cover_image_url = li.a.img.get('src')
            status = li.find('p', {'class': 'mh-works-author'}).text
            result.add_result(comicid=comicid,
                              name=name,
                              status=status,
                              cover_image_url=cover_image_url,
                              source_url=source_url)
        return result

    def search(self, name, page, size=None):
        url = "https://www.mh160.xyz/statics/search.aspx?key=%s&page=%s" % (name, page)
        soup = self.get_soup(url)
        result = self.new_search_result_item()
        for li in soup.find('div', {'class': 'mh-search-result'}).ul.find_all('li'):
            href = li.a.get('href')
            comicid = self.get_comicid_by_url(href)
            source_url = urljoin(self.SITE_INDEX, href)
            name = li.a.get('title')
            cover_image_url = li.a.img.get('src')
            status = li.find('p', {'class': 'mh-works-author'}).text
            result.add_result(comicid=comicid,
                              name=name,
                              status=status,
                              cover_image_url=cover_image_url,
                              source_url=source_url)
        return result
