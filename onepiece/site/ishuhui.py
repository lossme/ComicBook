import re
import difflib
import collections
from . import ComicBookCrawlerBase, ChapterItem, ComicBookItem, SearchResultItem
from ..exceptions import ComicbookNotFound, ChapterNotFound


class ComicBookCrawler(ComicBookCrawlerBase):

    SOURCE_NAME = '鼠绘漫画'
    SITE = "ishuhui"
    CHAPTER_INTERVAL_PATTERN = re.compile(r"^(?P<start_chapter_number>\d+)\-(?P<end_chapter_number>\d+)")

    COMIC_API_VER = None

    # source= qq/ishuhui
    CItem = collections.namedtuple("CItem", ["title", "url", "source", "source_url"])

    def __init__(self, comicid):
        super().__init__()
        self.comicid = comicid
        self.api_data = None

        # {int_chapter_number: CItem, }
        self.chapter_db = {}
        self.source_url = "https://www.ishuhui.com/comics/anime/{}".format(comicid)

    @property
    def api_url(self):
        # https://prod-api.ishuhui.com/ver/8a175090/anime/detail?id=1&type=comics&.json
        return "https://prod-api.ishuhui.com/ver/{ver}/anime/detail?id={comicid}&type=comics&.json"\
            .format(ver=self.get_comics_api_ver(), comicid=self.comicid)

    @classmethod
    def get_comics_api_ver(cls):
        if cls.COMIC_API_VER is None:
            url = "https://prod-u.ishuhui.com/ver"
            data = cls.get_json(url)
            cls.COMIC_API_VER = data["data"]["comics"]
        return cls.COMIC_API_VER

    def get_api_data(self):
        if self.api_data is None:
            self.api_data = self.get_json(url=self.api_url)
        if not self.api_data.get("data"):
            msg = "资源未找到！ site={} comicid={}".format(self.SITE, self.comicid)
            raise ComicbookNotFound(msg)
        return self.api_data

    def get_comicbook_item(self):
        api_data = self.get_api_data()
        name = api_data['data']['name']
        desc = api_data['data']['desc'] or ""
        desc = desc.replace("<p>", "")
        desc = desc.replace("</p>", "")
        tag = api_data['data']['tag']
        last_chapter_number = int(api_data['data']['comicsIndexes']['1']['maxNum'])

        chapter_db = self.get_chapter_db()
        last_chapter_title = chapter_db[max(chapter_db.keys())].title

        cover_image_url = api_data['data']['thumbComics']
        author = api_data['data']['authorName']
        return ComicBookItem(name=name,
                             desc=desc,
                             tag=tag,
                             last_chapter_number=last_chapter_number,
                             last_chapter_title=last_chapter_title,
                             cover_image_url=cover_image_url,
                             author=author,
                             source_url=self.source_url,
                             source_name=self.SOURCE_NAME)

    def get_chapter_item(self, chapter_number):
        chapter_db = self.get_chapter_db()
        if chapter_number not in chapter_db:
            msg = "资源未找到！ site={} comicid={} chapter_number={}".format(self.SITE, self.comicid, chapter_number)
            raise ChapterNotFound(msg)

        item = chapter_db[chapter_number]
        if item.source == "qq":
            html = self.get_html(item.url)
            chapter_item = self.parser_qq_source(html, source_url=item.source_url)
            return chapter_item

        if item.source == "ishuhui":
            chapter_api_data = self.get_json(item.url)
            chapter_item = self.parser_ishuihui_source(chapter_api_data,
                                                       source_url=item.source_url)
            return chapter_item

    def get_chapter_db(self):
        if self.chapter_db:
            return self.chapter_db

        api_data = self.get_api_data()
        for interval, items in api_data['data']['comicsIndexes']['1']['nums'].items():
            for str_chapter_number, chapter_data_sources in items.items():
                # str_chapter_number = "1-8"
                # str_chapter_number = "9-17"
                r = self.CHAPTER_INTERVAL_PATTERN.search(str_chapter_number)
                if r:
                    chapter_number = int(r.group("start_chapter_number"))
                else:
                    chapter_number = int(str_chapter_number)

                # {source_id : {}}
                chapter_source = {}
                for chapter_data in chapter_data_sources:
                    source_id = chapter_data['sourceID']
                    chapter_source[source_id] = chapter_data

                if 2 in chapter_source:
                    chapter_data = chapter_source[2]
                    # http://ac.qq.com/ComicView/index/id/505430/cid/1
                    qq_source_url = chapter_data['url']
                    qq_source_url = qq_source_url.replace("http://", "https://", 1)

                    self.chapter_db[chapter_number] = self.CItem(title=chapter_data['title'],
                                                                 url=qq_source_url,
                                                                 source_url=qq_source_url,
                                                                 source="qq")
                    continue

                if 1 in chapter_source or 7 in chapter_source:
                    chapter_data = chapter_source[1] or chapter_source[7]
                    cid = chapter_data['id']
                    # https://www.ishuhui.com/comics/detail/11196
                    # https://prod-api.ishuhui.com/comics/detail?id=11196
                    url = "https://prod-api.ishuhui.com/comics/detail?id={}".format(cid)
                    source_url = "https://www.ishuhui.com/comics/detail/11370".format(cid)
                    self.chapter_db[chapter_number] = self.CItem(title=chapter_data['title'],
                                                                 url=url,
                                                                 source="ishuhui",
                                                                 source_url=source_url)
                    continue

                if chapter_data['sourceID'] == 6:
                    # 百度网盘
                    pass
        return self.chapter_db

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

    @classmethod
    def search(cls, name):
        url = "https://prod-api.ishuhui.com/ver/{}/comics/list?page=1&pageSize=100&toView=true&.json"\
            .format(cls.get_comics_api_ver())
        data = cls.get_json(url)
        rv = []
        for item in data["data"]["data"]:
            comicid = item["animeID"]
            name = item["title"]
            cover_image_url = item["thumb"]
            source_url = "https://www.ishuhui.com/comics/anime/{}".format(comicid)
            search_result_item = SearchResultItem(site=cls.SITE,
                                                  name=name,
                                                  comicid=comicid,
                                                  cover_image_url=cover_image_url,
                                                  source_url=source_url)
            rv.append(search_result_item)
        return sorted(rv, key=lambda x: difflib.SequenceMatcher(None, name, x.name).ratio(), reverse=True)
