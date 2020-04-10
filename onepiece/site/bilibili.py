import tempfile
import collections
import io
import json
import os
import zipfile
import urllib.parse

from . import ComicBookCrawlerBase, ChapterItem, ComicBookItem, SearchResultItem
from ..exceptions import ChapterNotFound, ComicbookNotFound


class ComicBookCrawler(ComicBookCrawlerBase):

    SITE = "bilibili"
    SOURCE_NAME = "哔哩哔哩漫画"
    CItem = collections.namedtuple("CItem", ["chapter_number", "title", "cid"])

    DATA_HOST = "https://i0.hdslb.com"

    def __init__(self, comicid):
        super().__init__()
        self.comicid = comicid.lstrip("mc")
        self.source_url = "https://manga.bilibili.com/m/detail/mc{}".format(self.comicid)
        self.api_url = "https://manga.bilibili.com/twirp/comic.v1.Comic/ComicDetail?device=h5&platform=h5"
        self.api_data = None
        # {int_chapter_number: CItem, }
        self.chapter_db = {}

    @classmethod
    def unzip(cls, file, target_dir):
        obj = zipfile.ZipFile(file)
        obj.extractall(target_dir)

    @staticmethod
    def generateHashKey(seasonId, episodeId):
        n = [None for i in range(8)]
        e = int(seasonId)
        t = int(episodeId)
        n[0] = t
        n[1] = t >> 8
        n[2] = t >> 16
        n[3] = t >> 24
        n[4] = e
        n[5] = e >> 8
        n[6] = e >> 16
        n[7] = e >> 24
        for idx in range(8):
            n[idx] = n[idx] % 256
        return n

    @staticmethod
    def unhashContent(hashKey, indexData):
        for idx in range(len(indexData)):
            indexData[idx] ^= hashKey[idx % 8]
        return bytes(indexData)

    def get_chapter_api_data(self, cid):
        url = "https://manga.bilibili.com/twirp/comic.v1.Comic/Index?device=h5&platform=h5"
        response = self.send_request("POST", url, data={"ep_id": cid})

        data = self.DATA_HOST + response.json()["data"]
        url = urllib.parse.urljoin(self.DATA_HOST, data)
        response = self.send_request("GET", url)
        indexData = response.content
        hashKey = self.generateHashKey(seasonId=self.comicid, episodeId=cid)
        indexData = list(indexData)[9:]
        if not indexData:
            source_url = self.get_chapter_soure_url(cid=cid)
            raise ChapterNotFound("{} 请传送至哔哩哔哩漫画 APP 阅读".format(source_url))
        indexData = self.unhashContent(hashKey=hashKey, indexData=indexData)

        file = io.BytesIO(indexData)
        tmp_dir = tempfile.TemporaryDirectory()
        self.unzip(file, tmp_dir.name)
        json_file = os.path.join(tmp_dir.name, "index.dat")

        return json.load(open(json_file))

    def get_api_data(self):
        if self.api_data is None:
            data = {"comic_id": self.comicid}
            response = self.send_request("POST", url=self.api_url, data=data)
            if response.status_code == 404:
                msg = ComicbookNotFound.TEMPLATE.format(site=self.SITE,
                                                        comicid=self.comicid,
                                                        source_url=self.source_url)
                raise ComicbookNotFound(msg)
            self.api_data = response.json()
        return self.api_data

    def get_chapter_db(self):
        if self.chapter_db:
            return self.chapter_db
        api_data = self.get_api_data()
        for idx, item in enumerate(sorted(api_data["data"]["ep_list"], key=lambda x: x["ord"]), start=1):
            chapter_number = idx
            title = item['title'].strip() or str(chapter_number)
            self.chapter_db[chapter_number] = self.CItem(chapter_number=chapter_number,
                                                         cid=item["id"],
                                                         title=title)
        return self.chapter_db

    def get_comicbook_item(self):
        api_data = self.get_api_data()
        name = api_data['data']['title']
        desc = api_data['data']['evaluate'] or ""
        tag = ",".join(api_data['data']['styles'])
        author = " ".join(api_data['data']['author_name'])
        cover_image_url = api_data['data']['vertical_cover']

        chapters = []
        chapter_db = self.get_chapter_db()
        for chapter_number, item in chapter_db.items():
            chapter = ComicBookItem.create_chapter(chapter_number=chapter_number,
                                                   title=item.title)
            chapters.append(chapter)

        return ComicBookItem(name=name,
                             desc=desc,
                             tag=tag,
                             cover_image_url=cover_image_url,
                             author=author,
                             source_url=self.source_url,
                             source_name=self.SOURCE_NAME,
                             chapters=chapters)

    def get_chapter_soure_url(self, cid):
        return "https://manga.bilibili.com/m/mc{}/{}".format(self.comicid, cid)

    def get_chapter_item(self, chapter_number):
        chapter_db = self.get_chapter_db()
        if chapter_number not in chapter_db:
            msg = ChapterNotFound.TEMPLATE.format(site=self.SITE,
                                                  comicid=self.comicid,
                                                  chapter_number=chapter_number,
                                                  source_url=self.source_url)
            raise ChapterNotFound(msg)
        item = chapter_db[chapter_number]

        chapter_api_data = self.get_chapter_api_data(cid=item.cid)

        token_url = "https://manga.bilibili.com/twirp/comic.v1.Comic/ImageToken?device=h5&platform=h5"
        response = self.send_request("POST", token_url, data={"urls": json.dumps(chapter_api_data["pics"])})
        data = response.json()
        image_urls = ["{}?token={}".format(i["url"], i["token"]) for i in data["data"]]

        source_url = self.get_chapter_soure_url(cid=item.cid)
        return ChapterItem(chapter_number=chapter_number,
                           title=item.title,
                           image_urls=image_urls,
                           source_url=source_url)

    @classmethod
    def search(cls, name):
        url = "http://manga.bilibili.com/twirp/comic.v1.Comic/Search"
        response = cls.send_request(
            "POST", url, data={"key_word": name, "page_num": 1, "page_size": 9})
        data = response.json()["data"]["list"]
        rv = []
        for result in data:
            comicid = result["id"]
            name = result["org_title"]
            # or square_cover or vertical_cover
            cover_image_url = result["horizontal_cover"]
            source_url = 'http://manga.bilibili.com/detail/mc{}'.format(comicid)
            search_result_item = SearchResultItem(site=cls.SITE,
                                                  comicid=comicid,
                                                  name=name,
                                                  cover_image_url=cover_image_url,
                                                  source_url=source_url)
            rv.append(search_result_item)
        return rv

    @classmethod
    def login(cls):
        login_url = "https://manga.bilibili.com/"
        cls.selenium_login(login_url=login_url,
                           check_login_status_func=cls.check_login_status)

    @classmethod
    def check_login_status(cls):
        session = cls.get_session()
        if session.cookies.get("DedeUserID", domain=".bilibili.com"):
            return True
