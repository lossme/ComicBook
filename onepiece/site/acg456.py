import re
import logging
import time
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from ..crawlerbase import CrawlerBase

logger = logging.getLogger(__name__)


class Acg456Crawler(CrawlerBase):

    SITE = "acg456"
    SITE_INDEX = 'http://www.acg456.com/'
    SOURCE_NAME = "ACG肆伍陆"
    LOGIN_URL = SITE_INDEX

    DEFAULT_COMICID = 'OnePiece'
    DEFAULT_SEARCH_NAME = '海贼王'
    DEFAULT_TAG = "1"

    def __init__(self, comicid=None):
        self.comicid = comicid
        super().__init__()

    @property
    def source_url(self):
        return self.get_source_url(self.comicid)

    def get_source_url(self, comicid):
        return urljoin(self.SITE_INDEX, "/HTML/{}".format(comicid))

    def get_comicbook_item(self):
        soup = self.get_soup(self.source_url)

        name = soup.h1.b.text.strip()
        author = ''
        desc = ''
        tag_list = []
        for li in soup.find('ul', {'class':'Height_px22'}).find_all('li'):
            if '作　　者：' in li.text:
                author = li.a.text.replace('作　　者：', '')
            elif '故事简介：' in li.text:
                desc = li.text.strip().replace('故事简介：', '')
            elif '漫画类型：' in li.text:
                for a in li.find_all('a'):
                    tag_list.append(li.a)

        cover_image_url = soup.find('td', {'class': 'comic_cover'}).img.get('src')
        book = self.new_comicbook_item(name=name,
                                       desc=desc,
                                       cover_image_url=cover_image_url,
                                       author=author,
                                       source_url=self.source_url)
        li_list = soup.find('ul', {'class': 'serialise_list Blue_link2'}).find_all('li')
        for chapter_number, li in enumerate(reversed(li_list), start=1):
            href = li.a.get('href')
            cid = href.strip('/').split('/')[-1]
            title = li.a.text.strip()
            url = urljoin(self.SITE_INDEX, href)
            book.add_chapter(chapter_number=chapter_number, 
                             source_url=url,
                             title=title,
                             cid=cid)
        for a in tag_list:
            href = a.get('href')
            tag_id = href.split('=')[-1]
            tag_name = a.text.strip()
            book.add_tag(name=tag_name, tag=tag_id)
        return book

    def get_chapter_item(self, citem):
        html = self.get_html(citem.source_url)
        cid = re.search(r'var c = (\d+);', html).group(1)
        api_url = 'http://www.acg456.com/ajax/Common.ashx'
        params = dict(op='getPics', cid=cid, path=citem.cid, _=int(time.time()))
        data = self.get_json(api_url, params=params)
        image_urls = data['data']
        return self.new_chapter_item(chapter_number=citem.chapter_number,
                                     title=citem.title,
                                     image_urls=image_urls,
                                     source_url=citem.source_url)

    def get_index_soup(self):
        response = self.send_request('get', self.SITE_INDEX)
        html = response.content.decode('utf-8')
        soup = BeautifulSoup(html, 'html.parser')
        return soup

    def latest(self, page=1):
        soup = self.get_index_soup()
        result = self.new_search_result_item()
        table = soup.find('div', {'id': 'TopList_1'}).find_all('table', recursive=False)[1]
        for td in table.find_all('table'):
            href = td.a.get('href')
            comicid = href.strip('/').split('/')[-1]
            source_url = urljoin(self.SITE_INDEX, href)
            name = td.img.get('alt')
            cover_image_url = td.img.get('src')
            result.add_result(comicid=comicid,
                              name=name,
                              cover_image_url=cover_image_url,
                              source_url=source_url)
        return result

    def get_tags(self):
        soup = self.get_index_soup()
        tags = self.new_tags_item()
        category = '分类列表'
        for a in soup.find('tr', {'class': 'typelist'}).td.find_all('a'):
            href = a.get('href')
            name = a.text.strip()
            tag_id = href.split('=')[-1]
            tags.add_tag(category=category, name=name, tag=tag_id)
        return tags

    def get_tag_result(self, tag, page=1):
        url = 'http://www.acg456.com/Catalog/?tid=%s&PageIndex=%s' % (tag, page)
        soup = self.get_soup(url)
        result = self.new_search_result_item()
        for ul in soup.find_all('ul', {'class': 'Comic_Pic_List'}):
            li = ul.li
            href = li.a.get('href')
            comicid = href.strip('/').split('/')[-1]
            name = li.img.get('alt')
            cover_image_url = li.img.get('src')
            source_url = self.get_source_url(comicid)
            result.add_result(comicid=comicid,
                              name=name,
                              cover_image_url=cover_image_url,
                              source_url=source_url)
        return result
