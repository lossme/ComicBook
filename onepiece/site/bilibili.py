import io
import json
import zipfile
import re
import logging
import datetime
import math
from urllib.parse import urljoin


from ..crawlerbase import CrawlerBase
from ..exceptions import ChapterNotFound, ComicbookNotFound

logger = logging.getLogger(__name__)


class BilibiliCrawler(CrawlerBase):

    SITE = "bilibili"
    SITE_INDEX = 'https://manga.bilibili.com/'

    SOURCE_NAME = "哔哩哔哩漫画"
    DATA_HOST = "https://i0.hdslb.com/"

    COMICBOOK_API = "https://manga.bilibili.com/twirp/comic.v1.Comic/ComicDetail?device=h5&platform=h5"
    CHAPTER_API = "https://manga.bilibili.com/twirp/comic.v1.Comic/Index?device=h5&platform=h5"
    IMAGE_TOKEN_API = "https://manga.bilibili.com/twirp/comic.v1.Comic/ImageToken?device=h5&platform=h5"
    SEARCH_API = "https://manga.bilibili.com/twirp/comic.v1.Comic/Search?device=pc&platform=web"
    LOGIN_URL = SITE_INDEX

    DEFAULT_COMICID = 'mc24742'
    DEFAULT_SEARCH_NAME = '海贼王'
    DEFAULT_TAG = 'is_finish_0'

    def __init__(self, comicid=None):
        super().__init__()
        self.comicid = comicid.replace("mc", "") if comicid else ''

    @property
    def source_url(self):
        return self.get_source_url(self.comicid)

    def get_source_url(self, comicid):
        return urljoin(self.SITE_INDEX, "/m/detail/mc{}".format(comicid))

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
        url = self.CHAPTER_API
        response = self.send_request("POST", url, data={"ep_id": cid})

        data = response.json()["data"]
        url = urljoin(self.DATA_HOST, data)
        response = self.send_request("GET", url)
        indexData = response.content
        hashKey = self.generateHashKey(seasonId=self.comicid, episodeId=cid)
        indexData = list(indexData)[9:]
        if not indexData:
            source_url = self.get_chapter_soure_url(cid=cid)
            raise ChapterNotFound(f"please go to bilibili comics APP to read. {source_url}")
        indexData = self.unhashContent(hashKey=hashKey, indexData=indexData)

        file = io.BytesIO(indexData)
        obj = zipfile.ZipFile(file)
        data = json.loads(obj.read("index.dat"))
        return data

    def get_api_data(self):
        data = {"comic_id": self.comicid}
        response = self.send_request("POST", url=self.COMICBOOK_API, data=data)
        if response.status_code == 404:
            msg = ComicbookNotFound.TEMPLATE.format(site=self.SITE,
                                                    comicid=self.comicid,
                                                    source_url=self.source_url)
            raise ComicbookNotFound(msg)
        return response.json()

    def get_comicbook_item(self):
        api_data = self.get_api_data()
        name = api_data['data']['title']
        desc = api_data['data']['evaluate'] or ""
        tag = ",".join(api_data['data']['styles'])
        author = " ".join(api_data['data']['author_name'])
        cover_image_url = api_data['data']['vertical_cover']
        status = "完结" if api_data['data']['is_finish'] == 1 else "连载"
        book = self.new_comicbook_item(name=name,
                                       desc=desc,
                                       tag=tag,
                                       cover_image_url=cover_image_url,
                                       author=author,
                                       source_url=self.source_url,
                                       status=status)
        for idx, item in enumerate(sorted(api_data["data"]["ep_list"], key=lambda x: x["ord"]), start=1):
            chapter_number = idx
            cid = item['id']
            title = item['title'].strip() or str(chapter_number)
            url = self.get_chapter_soure_url(cid)
            book.add_chapter(chapter_number=chapter_number, source_url=url, cid=cid, title=title)
        return book

    def get_chapter_soure_url(self, cid):
        return urljoin(
            self.SITE_INDEX, "/m/mc{}/{}".format(self.comicid, cid))

    def get_chapter_item(self, citem):
        chapter_api_data = self.get_chapter_api_data(cid=citem.cid)
        token_url = self.IMAGE_TOKEN_API
        response = self.send_request("POST", token_url, data={"urls": json.dumps(chapter_api_data["pics"])})
        data = response.json()
        image_urls = ["{}?token={}".format(i["url"], i["token"]) for i in data["data"]]
        return self.new_chapter_item(chapter_number=citem.chapter_number,
                                     title=citem.title,
                                     image_urls=image_urls,
                                     source_url=citem.source_url)

    def search(self, name, page=1, size=None):
        size = size or 20
        if page > 50:
            return []
        url = self.SEARCH_API
        response = self.send_request(
            "POST", url, data={"key_word": name, "page_num": page, "page_size": size})
        data = response.json()
        result = self.new_search_result_item()
        for i in data["data"]["list"]:
            comicid = i["id"]
            title = i["title"]
            name = re.sub(r'<[^>]+>', '', title, re.S)
            status = "完结" if i['is_finish'] == 1 else "连载"

            # or square_cover or vertical_cover
            cover_image_url = i["horizontal_cover"]
            source_url = self.get_source_url(comicid)
            result.add_result(comicid=comicid,
                              name=name,
                              cover_image_url=cover_image_url,
                              source_url=source_url,
                              status=status)
        return result

    def latest(self, page=1):
        url = 'https://manga.bilibili.com/twirp/comic.v1.Comic/GetDailyPush?device=pc&platform=web'
        today = datetime.date.today()
        date = (today - datetime.timedelta(page)).strftime('%Y-%m-%d')
        page_size = 10
        page_num = 1
        params = {
            'date': date,
            'page_num': page_num,
            'page_size': page_size
        }
        response = self.send_request("POST", url, data=params)
        data = response.json()
        total = data['data']['total']
        total_page = math.ceil(total / page_size)
        data_list = data["data"]["list"]
        for page_num in range(2, total_page + 1):
            params = {
                'date': date,
                'page_num': page_num,
                'page_size': page_size
            }
            response = self.send_request("POST", url, data=params)
            data = response.json()
            data_list.extend(data["data"]["list"])
        result = self.new_search_result_item()
        for i in data_list:
            comicid = i["comic_id"]
            title = i["title"]
            name = re.sub(r'<[^>]+>', '', title, re.S)
            # or square_cover or vertical_cover
            cover_image_url = i["vertical_cover"]
            source_url = self.get_source_url(comicid)
            result.add_result(comicid=comicid,
                              name=name,
                              cover_image_url=cover_image_url,
                              source_url=source_url)
        return result

    def get_tags(self):
        url = 'https://manga.bilibili.com/twirp/comic.v1.Comic/AllLabel?device=pc&platform=web'
        response = self.send_request("POST", url, data={})
        data = response.json()
        tags_item = self.new_tags_item()
        for (key, category, param_key) in [('styles', '题材', 'style_id'),
                                           ('areas', '地区', 'area_id'),
                                           ('status', '进度', 'is_finish'),
                                           ('prices', '收费', 'is_free'),
                                           ('orders', '排序', 'order')]:
            for i in data['data'][key]:
                name = i['name']
                id = i['id']
                tag = '%s_%s' % (param_key, id)
                tags_item.add_tag(category=category, name=name, tag=tag)
        return tags_item

    def get_tag_result(self, tag, page=1):
        params = {
            'area_id': -1,
            'is_finish': -1,
            'is_free': -1,
            'order': 0,
            'page_num': page,
            'page_size': 20,
            'style_id': -1,
        }
        if tag:
            for i in tag.split(','):
                key, _id = i.rsplit('_', 1)
                params[key] = int(_id)
        url = 'https://manga.bilibili.com/twirp/comic.v1.Comic/ClassPage?device=pc&platform=web'
        response = self.send_request("POST", url, data=params)
        data = response.json()

        result = self.new_search_result_item()
        for i in data['data']:
            comicid = i["season_id"]
            name = i["title"]
            cover_image_url = i["horizontal_cover"]
            source_url = self.get_source_url(comicid)
            status = "完结" if i['is_finish'] == 1 else "连载"
            result.add_result(comicid=comicid,
                              name=name,
                              cover_image_url=cover_image_url,
                              source_url=source_url,
                              status=status)
        return result

    def login(self):
        self.selenium_login(login_url=self.LOGIN_URL,
                            check_login_status_func=self.check_login_status)

    def check_login_status(self):
        session = self.get_session()
        if session.cookies.get("DedeUserID", domain=".bilibili.com"):
            return True
