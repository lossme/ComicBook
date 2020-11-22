import re
import logging
from urllib.parse import urljoin
import jsbeautifier

from ..crawlerbase import CrawlerBase

logger = logging.getLogger(__name__)


class Mh1234Crawler(CrawlerBase):

    SITE = "77mh"
    SITE_INDEX = 'https://www.77mh.cc/'
    SOURCE_NAME = "新新漫画"
    LOGIN_URL = SITE_INDEX

    DEFAULT_COMICID = '78824'
    DEFAULT_SEARCH_NAME = '海贼王'
    DEFAULT_TAG = "chunqing"

    def __init__(self, comicid=None):
        self.comicid = comicid
        super().__init__()

    @property
    def source_url(self):
        return self.get_source_url(self.comicid)

    def get_source_url(self, comicid):
        return urljoin(self.SITE_INDEX, "/colist_{}.html".format(comicid))

    def get_comicbook_item(self):
        soup = self.get_soup(self.source_url)
        name = soup.h1.text.strip()
        author = ''
        for li in soup.find('ul', {'class': 'ar_list_coc'}).find_all('li'):
            if '作者' in li.text:
                author = li.a.text.strip()

        desc = soup.find('i', {'class': 'd_sam'}).text.strip()
        cover_image_url = soup.find('div', {'class': 'ar_list_coc'}).dt.img.get('src')
        book = self.new_comicbook_item(name=name,
                                       desc=desc,
                                       cover_image_url=cover_image_url,
                                       author=author,
                                       source_url=self.source_url)
        li_list = soup.find('ul', {'class': 'ar_rlos_bor ar_list_col'}).find_all('li')
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
        coid = citem.source_url.split('/')[-1].split('.')[0]
        s = re.search(r'<script type="text/javascript">(.*?)</script>', html, re.S).group(1).strip()
        js_str = jsbeautifier.beautify(s)
        msg = re.search(r"var msg = '(.*?)';", js_str).group(1)
        atsvr = re.search(r'var atsvr = "(.*?)";', js_str).group(1)
        img_s = re.search(r"var img_s = (\d+);", js_str).group(1)
        image_urls = []
        url_params = {'z': atsvr, 's': img_s, 'cid': self.comicid, 'coid': coid}
        image_prefix, end = self.get_image_prefix(url_params)
        image_urls = []
        for url in msg.split('|'):
            image_url = image_prefix + url + end
            image_urls.append(image_url)
        return self.new_chapter_item(chapter_number=citem.chapter_number,
                                     title=citem.title,
                                     image_urls=image_urls,
                                     source_url=citem.source_url)

    def get_image_prefix(self, params):
        url = 'https://css.gdbyhtl.net/img_v1/cn_svr.aspx'
        html = self.get_html(url, params=params)
        prefix = re.search(
            r'(http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)',
            html).group(1)
        end = '.webp' if re.search(r'var webpshow = 1;', html) else ''
        return prefix, end

    def latest(self, page=1):
        url = "https://www.77mh.cc/new_coc.html"
        soup = self.get_soup(url)
        result = self.new_search_result_item()
        for li in soup.find('div', {'class': 'ar_list_co'}).find_all('li'):
            href = li.a.get('href')
            comicid = self.get_comicid_by_url(href)
            source_url = urljoin(self.SITE_INDEX, href)
            name = li.span.a.text
            cover_image_url = li.img.get('src')
            result.add_result(comicid=comicid,
                              name=name,
                              cover_image_url=cover_image_url,
                              source_url=source_url)
        return result

    def get_tags(self):
        soup = self.get_soup(self.SITE_INDEX)
        tags = self.new_tags_item()
        category = '分类'
        for li in soup.find('div', {'id': 'nav'}).find_all('li')[1:]:
            href = li.a.get('href')
            name = li.a.text.strip()
            tag_id = href.strip('/').split('/')[0]
            tags.add_tag(category=category, name=name, tag=tag_id)
        return tags

    def get_tag_result(self, tag, page=1):
        if page == 1:
            url = "https://www.77mh.cc/%s/index.html" % tag
        else:
            url = "https://www.77mh.cc/%s/index_%s.html" % (tag, page - 1)

        soup = self.get_soup(url)
        result = self.new_search_result_item()
        for li in soup.find('div', {'class': 'ar_list_co'}).find_all('dl'):
            href = li.a.get('href')
            comicid = self.get_comicid_by_url(href)
            name = li.h1.text.strip()
            cover_image_url = li.img.get('src')
            source_url = self.get_source_url(comicid)
            result.add_result(comicid=comicid,
                              name=name,
                              cover_image_url=cover_image_url,
                              source_url=source_url)
        return result

    def get_comicid_by_url(self, url):
        return re.search(r'colist_(\d+).html', url).group(1)

    def search(self, name, page, size=None):
        url = "https://so.77mh.cc/k.php?k=%s&p=%s" % (name, page)
        soup = self.get_soup(url)
        result = self.new_search_result_item()
        for li in soup.find('div', {'class': 'ar_list_co'}).find_all('dl'):
            href = li.a.get('href')
            comicid = self.get_comicid_by_url(href)
            name = li.h1.text.strip()
            cover_image_url = li.img.get('src')
            source_url = self.get_source_url(comicid)
            result.add_result(comicid=comicid,
                              name=name,
                              cover_image_url=cover_image_url,
                              source_url=source_url)
        return result
