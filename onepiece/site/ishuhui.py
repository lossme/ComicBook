import re
from . import ComicBookCrawlerBase, ChapterItem, ComicBookItem, ComicbookNotFound, ChapterSourceNotFound


class ComicBookCrawler(ComicBookCrawlerBase):

    source_name = '鼠绘漫画'
    site = "ishuhui"
    CHAPTER_INTERVAL_PATTERN = re.compile(r"^(?P<start_chapter_number>\d+)\-(?P<end_chapter_number>\d+)")

    def __init__(self, comicid):
        super().__init__()
        self.comicid = comicid
        self.api_data = None
        self._comics_api_ver = None

    @property
    def source_url(self):
        # https://prod-api.ishuhui.com/ver/8a175090/anime/detail?id=1&type=comics&.json
        return "https://prod-api.ishuhui.com/ver/{ver}/anime/detail?id={comicid}&type=comics&.json"\
            .format(ver=self.comics_api_ver, comicid=self.comicid)

    @property
    def comics_api_ver(self):
        if self._comics_api_ver is None:
            url = "https://prod-u.ishuhui.com/ver"
            data = self.get_json(url)
            self._comics_api_ver = data["data"]["comics"]
        return self._comics_api_ver

    def get_api_data(self):
        if self.api_data is None:
            self.api_data = self.get_json(url=self.source_url)
        if not self.api_data.get("data"):
            msg = "资源未找到！ site={} comicid={}".format(self.site, self.comicid)
            raise ComicbookNotFound(msg)
        return self.api_data

    def get_comicbook_item(self):
        api_data = self.get_api_data()
        comicbook_item = self.parser_api_data(api_data, source_url=self.source_url)
        return comicbook_item

    def get_chapter_item(self, chapter_number):
        api_data = self.get_api_data()
        for interval, items in api_data['data']['comicsIndexes']['1']['nums'].items():
            for str_chapter_number, chapter_data_sources in items.items():
                # str_chapter_number = "1-8"
                # str_chapter_number = "9-17"
                r = self.CHAPTER_INTERVAL_PATTERN.search(str_chapter_number)
                if r:
                    _chapter_number = int(r.group("start_chapter_number"))
                else:
                    _chapter_number = int(str_chapter_number)
                if chapter_number != _chapter_number:
                    continue

                qq_source_url = None
                ishuhui_source_url = None
                for chapter_data in chapter_data_sources:
                    source_id = chapter_data['sourceID']
                    if chapter_data['sourceID'] == 2:
                        # http://ac.qq.com/ComicView/index/id/505430/cid/1
                        qq_source_url = chapter_data['url']
                        qq_source_url = qq_source_url.replace("http://", "https://", 1)
                    if source_id in [1, 7]:
                        # https://prod-api.ishuhui.com/comics/detail?id=11196
                        ishuhui_source_url = "https://prod-api.ishuhui.com/comics/detail?id={}"\
                            .format(chapter_data['id'])
                    if chapter_data['sourceID'] == 6:
                        # 百度网盘
                        pass

                if qq_source_url:
                    html = self.get_html(qq_source_url)
                    chapter_item = self.parser_qq_source(html, source_url=qq_source_url)
                    return chapter_item
                if ishuhui_source_url:
                    chapter_api_data = self.get_json(ishuhui_source_url)
                    chapter_item = self.parser_ishuihui_source(chapter_api_data,
                                                               source_url=ishuhui_source_url)
                    return chapter_item

        msg = "资源未找到！ site={} comicid={} chapter_number={}".format(self.site, self.comicid, chapter_number)
        raise ChapterSourceNotFound(msg)

    @classmethod
    def parser_api_data(cls, api_data, source_url=None):
        name = api_data['data']['name']
        desc = api_data['data']['desc'] or ""
        desc = desc.replace("<p>", "")
        desc = desc.replace("</p>", "")
        tag = api_data['data']['tag']
        max_chapter_number = int(api_data['data']['comicsIndexes']['1']['maxNum'])
        cover_image_url = api_data['data']['thumbComics']
        author = api_data['data']['authorName']
        return ComicBookItem(name=name,
                             desc=desc,
                             tag=tag,
                             max_chapter_number=max_chapter_number,
                             cover_image_url=cover_image_url,
                             author=author,
                             source_url=source_url,
                             source_name=cls.source_name)

    @classmethod
    def parser_ishuihui_source(cls, chapter_api_data, source_url=None):
        # https://prod-api.ishuhui.com/comics/detail?id=11196
        image_urls = [item['url'] for item in chapter_api_data['data']['contentImg']]
        chapter_title = chapter_api_data['data']['title']
        chapter_number = chapter_api_data['data']['numberStart']
        return ChapterItem(chapter_number=chapter_number,
                           title=chapter_title,
                           image_urls=image_urls,
                           source_url=source_url)

    @classmethod
    def parser_qq_source(self, chapter_page_html, source_url=None):
        # https://ac.qq.com/ComicView/index/id/505430/cid/1
        from .qq import ComicBookCrawler as QQComicBookCrawler
        return QQComicBookCrawler.parser_chapter_page(chapter_page_html, source_url=source_url)
