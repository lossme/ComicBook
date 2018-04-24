import re
import random
import json
import queue
import requests


class IshuhuiComicBook():

    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.146 Safari/537.36'
    }

    def __init__(self):
        self.session = requests.session()
        self.name = '鼠绘漫画'
        self.task_queue = queue.Queue()

    def wget(self, url, **kwargs):
        if 'headers' not in kwargs:
            kwargs['headers'] = self.headers
        return self.session.get(url, **kwargs)

    def get_html(self, url):
        response = self.wget(url)
        return response.text

    def get_chapter_pics(self, _id):
        """根据章节的URL获取该章节的图片列表
        Args:
            _id: 章节的URL如 http://hanhuazu.cc/cartoon/post?id=10694，id为10694

        Yield:
            pic_url
        """
        url = 'http://hanhuazu.cc/cartoon/post?id={_id}'.format(_id=_id)
        html = self.get_html(url)
        cdn_str = re.search(r'<meta name=img-url content="(.*?)"', html).group(1).replace('&#34;', '"')
        cdn_info = json.loads(cdn_str)
        cdn_url = random.choice(cdn_info)

        ver_str = re.search(r'<meta name=ver content="(.*?)">', html).group(1).replace('&#34;', '"')
        ver_info = json.loads(ver_str)
        ver = random.choice(list(ver_info.values()))

        url = 'http://hhzapi.ishuhui.com/cartoon/post/ver/{ver}/id/{_id}.json'.format(ver=ver, _id=_id)
        response = self.wget(url)
        data = response.json()
        img_data = json.loads(data['data']['content_img'])
        for url in img_data.values():
            pic_url = 'http:{}{}'.format(cdn_url, url.replace('upload/', ''))
            yield pic_url

    def get_all_chapter(self, comicid):
        """根据漫画id获取所有的章节列表: http://ac.qq.com/Comic/ComicInfo/id/505430
        Args:
            id: 505430
        """
        url = 'http://www.ishuhui.com/cartoon/book/{}'.format(comicid)
        html = requests.get(url).text
        r = re.search(r'<meta name=ver content="(.*?)">', html)
        ver = json.loads(r.group(1).replace('&#34;', '"'))

        url = 'http://api.ishuhui.com/cartoon/book_ish/ver/{ver}/id/{comicid}.json'\
            .format(ver=random.choice(list(ver.values())), comicid=comicid)
        data = requests.get(url).json()
        comic_title = data['data']['book']['name']
        all_chapter = {}
        for key, value in data['data']['cartoon']['0']['posts'].items():
            chapter_number = int(key.replace('n-', ''))
            all_chapter[chapter_number] = value
        return comic_title, all_chapter

    def get_task_chapter(self, comicid, chapter_number_list=None, is_download_all=None):
        comic_title, all_chapter = self.get_all_chapter(comicid)
        max_chapter_number = max(all_chapter.keys())
        if is_download_all:
            chapter_number_list = list(max_chapter_number.keys())
        for idx in chapter_number_list:
            chapter_number = idx if idx >= 0 else max_chapter_number + idx + 1
            value = all_chapter.get(chapter_number)
            if value is None:
                print('找不到第{}集资源'.format(chapter_number))
                continue
            is_invalid = True
            chapter_title = ''
            for src in value:
                if src['source'] in [1, 5]:
                    chapter_title = src['title']
                    data = {
                        'chapter_number': chapter_number,
                        'chapter_title': chapter_title,
                        'comic_title': comic_title,
                        'chapter_pics': self.get_chapter_pics(src['id']),
                        'site_name': self.name
                    }
                    self.task_queue.put(data)
                    is_invalid = False
                    break
            if is_invalid:
                print('暂不支持的资源类型：{} 第{}集 {}'.format(comic_title, chapter_number, chapter_title))
        return self.task_queue
