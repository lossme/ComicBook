import re
import logging
from urllib.parse import urljoin

from ..crawlerbase import CrawlerBase
from ..worker import concurrent_run

logger = logging.getLogger(__name__)


class C2animxCrawler(CrawlerBase):

    SITE = "2animx"
    SITE_INDEX = 'https://www.2animx.com/'
    SOURCE_NAME = "二次元动漫"
    LOGIN_URL = SITE_INDEX

    DEFAULT_COMICID = '24755'
    DEFAULT_SEARCH_NAME = '和'
    DEFAULT_TAG = ""
    COMICID_PATTERN = re.compile(r'-id-(\d+)')

    def __init__(self, comicid=None):
        self.comicid = comicid
        super().__init__()

    @property
    def source_url(self):
        return self.get_source_url(self.comicid)

    def get_source_url(self, comicid):
        return urljoin(self.SITE_INDEX, "/index-comic-id-{}/".format(comicid))

    def get_comicbook_item(self):
        soup = self.get_soup(self.source_url)
        mh_info = soup.find('dl', {'class': 'mh-detail'})
        name = soup.find('div', {'class': 'box-hd'}).h1.text.strip()
        author = ''
        tags = []
        for p in mh_info.dd.find_all('p'):
            if not p.span:
                continue
            text = p.span.text
            if '漫畫作者：' in text:
                author = p.a.text
            elif '漫畫狀態：' in text:
                status = p.a.text
            elif '漫畫類型：' in text:
                href = p.a.get('href') or ''
                r = re.search(r'(typeid-\d+)', href)
                if not r:
                    continue
                tag_id = r.group(1)
                tag_name = p.a.text
                tags.append((tag_id, tag_name))

        desc = soup.find('div', {'class': 'mh-introduce'}).text.strip()
        cover_image_url = urljoin(self.SITE_INDEX, mh_info.dt.img.get('src'))

        book = self.new_comicbook_item(name=name,
                                       desc=desc,
                                       cover_image_url=cover_image_url,
                                       author=author,
                                       status=status,
                                       source_url=self.source_url)
        for tag_id, tag_name in tags:
            book.add_tag(name=tag_name, tag=tag_id)

        li_list = soup.find('ul', {'class': 'b1'}).find_all('li')
        for chapter_number, li in enumerate(li_list, start=1):
            href = li.a.get('href')
            url = urljoin(self.SITE_INDEX, href)
            title = li.a.text.strip()
            book.add_chapter(chapter_number=chapter_number,
                             source_url=url,
                             title=title)
        return book

    def get_chapter_max_page(self, soup):
        max_page = 1
        for i in soup.find('select', {'name': 'select1'}).find_all('option'):
            page = int(i.get('value'))
            if page > max_page:
                max_page = page
        return max_page

    def get_image_url_from_page(self, soup):
        return soup.find('img', {'id': 'ComicPic'}).get('src')

    def get_chapter_item(self, citem):
        soup = self.get_soup(citem.source_url)
        max_page = self.get_chapter_max_page(soup)
        image_urls = [self.get_image_url_from_page(soup)]

        def _get_page_image(page):
            url = citem.source_url + "-p-%s" % page
            soup = self.get_soup(url)
            return self.get_image_url_from_page(soup=soup)

        zip_args = []
        for page in range(2, max_page + 1):
            zip_args.append((_get_page_image, dict(page=page)))
        result_list = concurrent_run(zip_args)
        for result in result_list:
            image_urls.append(result)
        return self.new_chapter_item(chapter_number=citem.chapter_number,
                                     title=citem.title,
                                     image_urls=image_urls,
                                     source_url=citem.source_url)

    def latest(self, page=1):
        if page > 1:
            return self.new_search_result_item()
        url = urljoin(self.SITE_INDEX, "/index-update")
        soup = self.get_soup(url)
        return self.parse_book_list(soup)

    def parse_book_list(self, soup):
        result = self.new_search_result_item()
        for ul in soup.find_all('ul', {'class': 'liemh htmls indliemh'}):
            for li in ul.find_all('li'):
                href = li.a.get('href')
                comicid = self.get_comicid_by_url(href)
                source_url = urljoin(self.SITE_INDEX, href)
                name = li.a.div.text
                cover_image_url = li.a.img.get('src')
                result.add_result(comicid=comicid,
                                  name=name,
                                  cover_image_url=cover_image_url,
                                  source_url=source_url)
        return result

    def get_tags(self):
        url = urljoin(self.SITE_INDEX, '/index-html')
        soup = self.get_soup(url)
        tags = self.new_tags_item()
        for dl in soup.find_all('dl', {'class': 'sort-area'}):
            category = dl.dt.text
            for a in dl.dd.find_all('a'):
                name = a.text
                href = a.get('href')
                if category == '按狀態':
                    r = re.search(r'status-(\d+)', href)
                    if not r:
                        continue
                    tag = 'status-%s' % r.group(1)
                elif category == '按分類':
                    r = re.search(r'typeid-(\d+)', href)
                    if not r:
                        continue
                    tag = 'typeid-%s' % r.group(1)
                tags.add_tag(category=category, name=name, tag=tag)
        return tags

    def get_tag_result(self, tag, page=1):
        if not tag:
            if page > 1:
                url = 'https://www.2animx.com/index.php?s=%2Findex-html&page={}'.format(page)
            else:
                url = 'https://www.2animx.com/index-html'
        else:
            status = '0'
            typeid = '0'
            for t in tag.split(','):
                if t.startswith('status-'):
                    status = t.replace('status-', '')
                else:
                    typeid = t.replace('typeid-', '')
            if page > 1:
                url = "https://www.2animx.com/index.php?s=%2Findex-html-status-{}-typeid-{}-sort-&page={}"\
                    .format(status, typeid, page)
            else:
                url = "https://www.2animx.com/index-html-status-{}-typeid-{}-sort-"\
                    .format(status, typeid)
        soup = self.get_soup(url)
        return self.parse_book_list(soup)

    def search(self, name, page=1, size=None):
        if page > 1:
            url = 'https://www.2animx.com/index.php?s=%2Fsearch-index&searchType=1&q={}&page={}'\
                .format(name, page)
        else:
            url = "https://www.2animx.com/search-index?searchType=1&q={}".format(name)
        soup = self.get_soup(url)
        return self.parse_book_list(soup)
