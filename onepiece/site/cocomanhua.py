import logging
import re
from urllib.parse import urljoin

from ..crawlerbase import CrawlerBase

logger = logging.getLogger(__name__)


class CocomanhuaCrawler(CrawlerBase):

    SITE = "cocomanhua"
    SITE_INDEX = 'https://www.cocomanhua.com/'
    SOURCE_NAME = "COCO漫画"
    LOGIN_URL = SITE_INDEX

    DEFAULT_COMICID = '12187'
    DEFAULT_SEARCH_NAME = '全职法师'
    DEFAULT_TAG = ""
    COMICID_PATTERN = re.compile(r'/(\d+)/?')

    def __init__(self, comicid=None):
        self.comicid = comicid
        super().__init__()

    @property
    def source_url(self):
        return self.get_source_url(self.comicid)

    def get_source_url(self, comicid):
        return urljoin(self.SITE_INDEX, "{}".format(comicid))

    def get_comicbook_item(self):
        soup = self.get_soup(self.source_url)
        name = soup.h1.text.strip()
        status = soup.find('span', text='状态').parent.a.text
        author = soup.find('span', text='作者').parent.a.text
        desc = soup.find('span', text='简介').parent.text.replace('简介', '', 1).strip()
        cover_image_url = soup.find('a', {'class': 'fed-list-pics fed-lazy fed-part-2by3'}).get('data-original')
        book = self.new_comicbook_item(name=name,
                                       desc=desc,
                                       cover_image_url=cover_image_url,
                                       author=author,
                                       status=status,
                                       source_url=self.source_url)
        li_list = soup.find('div', {'class': 'all_data_list'}).find_all('li')
        for chapter_number, li in enumerate(reversed(li_list), start=1):
            href = li.a.get('href')
            url = urljoin(self.SITE_INDEX, href)
            title = li.a.get('title')
            book.add_chapter(chapter_number=chapter_number,
                             source_url=url,
                             title=title)
        return book

    def get_chapter_item(self, citem):
        driver = self.create_driver()
        driver.get(citem.source_url)
        total_image = 0
        try:
            total_image = driver.execute_script(
                "return __cdecrypt('fw12558899ertyui', CryptoJS.enc.Base64.parse(mh_info.enc_code1).toString(CryptoJS.enc.Utf8));")
        except Exception:
            total_image = driver.execute_script(
                "return __cdecrypt('JRUIFMVJDIWE569j', CryptoJS.enc.Base64.parse(mh_info.enc_code1).toString(CryptoJS.enc.Utf8));")

        image_urls = []
        for index in range(int(total_image)):
            url = driver.execute_script("return __cr.getPicUrl(%s + 1);" % index)
            url = 'https:' + url
            image_urls.append(url)
        return self.new_chapter_item(chapter_number=citem.chapter_number,
                                     title=citem.title,
                                     image_urls=image_urls,
                                     source_url=citem.source_url)

    def latest(self, page=1):
        url = "https://www.cocomanhua.com/show?orderBy=update&page=%s" % page
        soup = self.get_soup(url)
        result = self.new_search_result_item()
        for li in soup.find('ul', {'class': 'fed-list-info fed-part-rows'}).find_all('li'):
            href = li.a.get('href')
            comicid = href.strip('/')
            source_url = urljoin(self.SITE_INDEX, href)
            name = li.find_all('a')[-1].text
            cover_image_url = li.a.get('data-original')
            result.add_result(comicid=comicid,
                              name=name,
                              cover_image_url=cover_image_url,
                              source_url=source_url)
        return result

    def search(self, name, page, size=None):
        url = "https://www.cocomanhua.com/search?searchString=%s&page=%s" % (name, page)
        soup = self.get_soup(url)
        result = self.new_search_result_item()
        for dl in soup.find_all('dl'):
            href = dl.dt.a.get('href')
            comicid = href.strip('/')
            name = dl.h1.text
            cover_image_url = dl.dt.a.get('data-original')
            source_url = self.get_source_url(comicid)
            result.add_result(comicid=comicid,
                              name=name,
                              cover_image_url=cover_image_url,
                              source_url=source_url)
        return result
