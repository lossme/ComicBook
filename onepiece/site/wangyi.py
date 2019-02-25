import re
import time

from . import ComicBookCrawlerBase, ChapterItem, ComicBookItem, SearchResultItem
from ..exceptions import ComicbookNotFound, ChapterNotFound


class ComicBookCrawler(ComicBookCrawlerBase):

    SOURCE_NAME = '网易漫画'
    SITE = "wangyi"

    COMIC_NAME_PATTERN = re.compile(r'<h1 class="f-toe sr-detail__heading">(.*?)</h1>')
    IMAGE_PATTERN = re.compile(r'url: window.IS_SUPPORT_WEBP \? ".*?" : "(.*?AccessKeyId=\w{32})')
    CHAPTER_TITLE_PATTERN = re.compile('fullTitle: "(.*?)"')
    CSRF_TOKEN_PATTERN = re.compile(r'csrfToken: "(.*?)"')
    DESC_PATTERN = re.compile(r'<dl class="sr-dl multi-lines j-desc-inner">.*?<dd>(.*?)</dd>', re.S)
    COVER_IMAGE_URL_PATTERN = re.compile(r'<img class="sr-bcover" src="(.*?)"/>')
    TAG_HTML_PATTERN = re.compile(r'<dl class="sr-dl">(.*?)</dl>', re.S)
    TAG_PATTERN = re.compile(r'<a title="(.*?)".*?</a>', re.S)
    AUTHOR_PATTERN = re.compile(
        r'<a class="sr-detail__author".*?<img src=".*?" alt="(.*?)" class="sr-detail__avatar f-fl" />', re.S)

    SEARCH_DATA_PATTERN = re.compile(r"""<div class="img-block">\s*<a href="/source/(.*?)" title="(.*?)" target="_blank">\s*\
<img alt="(.*?)" src="(.*?)".*?</a>\s*</div>""", re.S)

    def __init__(self, comicid):
        super().__init__()
        self.comicid = comicid

        self.api_data = None
        self.index_page = None

        # https://manhua.163.com/source/4458002705630123103
        self.source_url = "https://manhua.163.com/source/{comicid}".format(comicid=self.comicid)

    def get_index_page(self):
        if self.index_page is None:
            self.index_page = self.get_html(self.source_url)
        return self.index_page

    def get_api_data(self):
        if self.api_data:
            return self.api_data
        # https://manhua.163.com/book/catalog/4458002705630123103.json
        url = "https://manhua.163.com/book/catalog/{comicid}.json".format(comicid=self.comicid)
        self.api_data = self.get_json(url=url)
        return self.api_data

    def get_comicbook_item(self):
        html = self.get_index_page()

        r = self.COMIC_NAME_PATTERN.search(html)
        if not r:
            msg = "资源未找到！ site={} comicid={}".format(self.SITE, self.comicid)
            raise ComicbookNotFound(msg)
        name = r.group(1)
        api_data = self.get_api_data()
        desc = self.DESC_PATTERN.search(html).group(1)
        tag_html = self.TAG_HTML_PATTERN.search(html).group(1)
        tag = ','.join(self.TAG_PATTERN.findall(tag_html))
        author = self.AUTHOR_PATTERN.search(html).group(1)
        cover_image_url = self.COVER_IMAGE_URL_PATTERN.search(html).group(1)
        last_chapter_number = len(api_data['catalog']['sections'][0]['sections'])
        last_chapter_title = api_data['catalog']['sections'][0]['sections'][-1]["title"]

        return ComicBookItem(name=name,
                             desc=desc,
                             tag=tag,
                             last_chapter_number=last_chapter_number,
                             last_chapter_title=last_chapter_title,
                             author=author,
                             source_url=self.source_url,
                             source_name=self.SOURCE_NAME,
                             cover_image_url=cover_image_url)

    def get_chapter_item(self, chapter_number):
        api_data = self.get_api_data()
        try:
            chapter_data = api_data['catalog']['sections'][0]['sections'][chapter_number - 1]
        except IndexError:
            msg = "资源未找到！ site={} comicid={} chapter_number={}".format(self.SITE, self.comicid, chapter_number)
            raise ChapterNotFound(msg)
        url = "https://manhua.163.com/reader/{}/{}".format(chapter_data['bookId'],
                                                           chapter_data['sectionId'])
        html = self.get_html(url)
        image_urls = self.IMAGE_PATTERN.findall(html)
        title = self.CHAPTER_TITLE_PATTERN.search(html).group(1)

        return ChapterItem(chapter_number=chapter_number, title=title, image_urls=image_urls, source_url=url)

    def login(self):
        import webbrowser
        html = self.get_index_page()
        csrf_token = self.CSRF_TOKEN_PATTERN.search(html).group(1)
        timestamp = int(time.time())
        login_url = 'https://manhua.163.com/login/qrCodeLoginImage.json?csrfToken={csrf_token}&_={timestamp}'\
            .format(csrf_token=csrf_token, timestamp=timestamp)

        data = self.get_json(login_url)
        token = data["token"]
        qrcode_url = "https://manhua.163.com" + data["url"]
        webbrowser.open(qrcode_url)
        check_url = ("https://manhua.163.com/login/qrCodeCheck.json"
                     "?token={token}&status=0&csrfToken={csrf_token}&_={timestamp}")\
            .format(token=token, csrf_token=csrf_token, timestamp=timestamp)
        while True:
            print("请扫描二维码")
            check_data = self.get_json(check_url)
            status = check_data['status']
            if status == 2:
                print("登录成功")
                break
            time.sleep(2)
        return

    @classmethod
    def search(cls, name):
        url = "https://manhua.163.com/search/book/key.do?key={}".format(name)
        html = cls.get_html(url)
        rv = []
        for item in cls.SEARCH_DATA_PATTERN.findall(html):
            comicid, name1, name2, cover_image_url = item
            search_result_item = SearchResultItem(site=cls.SITE,
                                                  comicid=comicid,
                                                  name=name1,
                                                  cover_image_url=cover_image_url)
            rv.append(search_result_item)
        return rv
