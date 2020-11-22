import re
import logging
import json
from urllib.parse import urljoin

import jsbeautifier
from ..crawlerbase import CrawlerBase

logger = logging.getLogger(__name__)


class DmzjCrawler(CrawlerBase):

    SITE = "dmzj"
    SITE_INDEX = 'https://www.dmzj.com/'
    SOURCE_NAME = "动漫之家"
    LOGIN_URL = SITE_INDEX

    DEFAULT_COMICID = 'sichunqijcdexienaijishangzhenpin'
    DEFAULT_SEARCH_NAME = '海贼'
    DEFAULT_TAG = "0-1-0-0-0-0"

    def __init__(self, comicid=None):
        self.comicid = comicid
        super().__init__()

    @property
    def source_url(self):
        return self.get_source_url(self.comicid)

    def get_source_url(self, comicid):
        return urljoin(self.SITE_INDEX, "/info/{}.html".format(comicid))

    def get_comicbook_item(self):
        soup = self.get_soup(self.source_url)
        name = soup.h1.text.strip()
        author = ''
        status = ''
        for li in soup.find('ul', {'class': 'comic_deCon_liO'}).find_all('li'):
            text = li.text.strip()
            if '作者：' in text:
                author = text.replace('作者：', '')
            if '状态：' in text:
                status = text.replace('状态：', '')

        desc = soup.find('p', {'class': 'comic_deCon_d'}).text.strip()
        cover_image_url = soup.find('div', {'class': 'comic_i_img'}).img.get('src')
        book = self.new_comicbook_item(name=name,
                                       desc=desc,
                                       cover_image_url=cover_image_url,
                                       author=author,
                                       status=status,
                                       source_url=self.source_url)
        li_list = soup.find('ul', {'class': 'list_con_li autoHeight'}).find_all('li')
        for chapter_number, li in enumerate(reversed(li_list), start=1):
            url = li.a.get('href')
            title = li.find('span', {'class': 'list_con_zj'}).text.strip()
            book.add_chapter(chapter_number=chapter_number,
                             source_url=url,
                             title=title)
        return book

    def get_chapter_item(self, citem):
        html = self.get_html(citem.source_url)
        s = re.search(r'(eval\(function.*)', html).group(1)
        js_str = jsbeautifier.beautify(s)
        json_str = re.search(r"var pages = '(.*?)';", js_str).group(1)
        data = json.loads(json_str)
        image_urls = []
        image_prefix = 'https://images.dmzj.com'
        for url in data['page_url'].split():
            image_url = urljoin(image_prefix, url)
            image_urls.append(image_url)
        return self.new_chapter_item(chapter_number=citem.chapter_number,
                                     title=citem.title,
                                     image_urls=image_urls,
                                     source_url=citem.source_url)

    def latest(self, page=1):
        if page == 1:
            url = "https://www.dmzj.com/update/"
        else:
            url = "https://www.dmzj.com/update/%s.html" % page
        soup = self.get_soup(url)
        result = self.new_search_result_item()
        for li in soup.find('ul', {'class': 'list_con_li'}).find_all('li'):
            href = li.a.get('href')
            comicid = self.get_comicid_by_url(href)
            source_url = urljoin(self.SITE_INDEX, href)
            name = li.a.get('title')
            cover_image_url = "https:" + li.img.get('src')
            status = ''
            for p in li.find('span', {'class': 'comic_list_det'}).find_all('p'):
                text = p.text.strip()
                if '状态：' in text:
                    status = text.replace('状态：', '')
            result.add_result(comicid=comicid,
                              name=name,
                              status=status,
                              cover_image_url=cover_image_url,
                              source_url=source_url)
        return result

    def get_tags(self):
        url = 'https://www.dmzj.com/category'
        soup = self.get_soup(url)
        tags = self.new_tags_item()
        for div in soup.find_all('div', {'class': 'public_com'}):
            category = div.find('span', {'class': 'statu_title'}).text
            for li in div.find_all('li'):
                href = li.a.get('href')
                name = li.a.text.strip()
                tag_id = href.split('/')[-1]
                tag_id = tag_id.replace('-1.html', '')
                tags.add_tag(category=category, name=name, tag=tag_id)
        return tags

    def get_tag_result(self, tag, page=1):
        url = 'https://www.dmzj.com/category/%s-%s.html' % (tag, page)
        soup = self.get_soup(url)
        result = self.new_search_result_item()
        for li in soup.find('ul', {'class': 'list_con_li'}).find_all('li'):
            href = li.a.get('href')
            comicid = self.get_comicid_by_url(href)
            name = li.h3.text.strip()
            for p in li.find_all('p'):
                text = p.text.strip()
                if '状态：' in text:
                    status = text.replace('状态：', '')
            cover_image_url = li.img.get('data-original')
            source_url = self.get_source_url(comicid)
            result.add_result(comicid=comicid,
                              name=name,
                              status=status,
                              cover_image_url=cover_image_url,
                              source_url=source_url)
        return result

    def get_comicid_by_url(self, url):
        try:
            return re.search(r'/info/(.*?).html', url).group(1)
        except Exception:
            return re.search(r'dmzj.com/([\w\d]*)$', url).group(1)

    def search(self, name, page, size=None):
        url = 'https://www.dmzj.com/dynamic/o_search/index/%s/%s' % (name, page)
        soup = self.get_soup(url)
        result = self.new_search_result_item()
        for li in soup.find('ul', {'class': 'update_con autoHeight'}).find_all('li'):
            href = li.a.get('href')
            comicid = self.get_comicid_by_url(href)
            name = li.a.get('title')
            cover_image_url = li.img.get('src')
            source_url = self.get_source_url(comicid)
            result.add_result(comicid=comicid,
                              name=name,
                              cover_image_url=cover_image_url,
                              source_url=source_url)
        return result
