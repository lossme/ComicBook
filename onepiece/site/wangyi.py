import re

from . import ComicBookCrawlerBase, Chapter, ComicBook


class ComicBookCrawler(ComicBookCrawlerBase):

    COMIC_HOST = 'https://manhua.163.com/source/4458002705630123103'

    source_name = '网易漫画'
    COMIC_NAME_PATTERN = re.compile(r'<h1 class="f-toe sr-detail__heading">(.*?)</h1>')
    IMAGE_PATTERN = re.compile(r'url: window.IS_SUPPORT_WEBP \? ".*?" : "(.*?AccessKeyId=\w{32})')
    CHAPTER_TITLE_PATTERN = re.compile('fullTitle: "(.*?)"')

    def __init__(self, comicid):
        super().__init__()
        self.comicid = comicid

        self.api_data = None
        self.index_page = None

    def get_index_page(self):
        if self.index_page is None:
            # https://manhua.163.com/source/4458002705630123103
            url = "https://manhua.163.com/source/{comicid}".format(comicid=self.comicid)
            self.index_page = self.get_html(url)
        return self.index_page

    def get_api_data(self):
        if self.api_data:
            return self.api_data
        # https://manhua.163.com/book/catalog/4458002705630123103.json
        url = "https://manhua.163.com/book/catalog/{comicid}.json".format(comicid=self.comicid)
        self.api_data = self.get_json(url=url)
        return self.api_data

    def get_comicbook(self):
        name = self.COMIC_NAME_PATTERN.search(self.get_index_page()).group(1)

        api_data = self.get_api_data()
        desc = ""
        tag = ""
        max_chapter_number = len(api_data['catalog']['sections'][0]['sections'])
        return ComicBook(name=name, desc=desc, tag=tag, max_chapter_number=max_chapter_number)

    def get_chapter(self, chapter_number):
        api_data = self.get_api_data()
        chapter_data = api_data['catalog']['sections'][0]['sections'][chapter_number - 1]
        url = "https://manhua.163.com/reader/{}/{}".format(chapter_data['bookId'],
                                                           chapter_data['sectionId'])
        html = self.get_html(url)
        image_urls = self.IMAGE_PATTERN.findall(html)
        title = self.CHAPTER_TITLE_PATTERN.search(html).group(1)
        return Chapter(title=title, image_urls=image_urls)
