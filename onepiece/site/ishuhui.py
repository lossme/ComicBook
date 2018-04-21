import re
import os
import random
import time
import json
import functools
import requests
from multiprocessing.dummy import Pool as ThreadPool

from onepiece.utils import safe_filename, parser_interval


class IshuhuiComicBook():

    def __init__(self, args=None):
        self.args = args
        self.session = requests.session()
        self.name = '鼠绘漫画'

    def wget(self, url, **kwargs):
        return self.session.get(url, **kwargs)

    def get_html(self, url):
        response = self.wget(url)
        return response.text

    def get_detail_list(self, _id):
        """根据章节的URL获取该章节的图片列表
        Args:
            _id: 章节的URL如 http://hanhuazu.cc/cartoon/post?id=10694，id为10694

        Returns:
            [pic1_url, pic2_url,]
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
        pic_list = []
        for title, url in img_data.items():
            full_url = 'http:{}{}'.format(cdn_url, url.replace('upload/', ''))
            pic_list.append(full_url)
        return pic_list

    def download_chapter(self, chapter, output, is_generate_pdf=None, is_send_email=None):
        """下载整个章节的图片，按漫画名按章节保存
        Args:
            chapter:
                要下载的章节，chapter = (_id, comic_title, chapter_name)
            output:
                文件保存路径
        Returns:
            dir_path: 当前章节漫画目录
        """
        _id, comic_title, chapter_name = chapter
        title = '{} {}'.format(comic_title, chapter_name)
        comic_title = '{} {}'.format(self.name, comic_title)
        comic_title = safe_filename(comic_title)
        chapter_name = safe_filename(chapter_name)

        print('正在下载', chapter_name)
        try:
            chapter_pic_list = self.get_detail_list(_id)
        except Exception as e:
            print('error', title, str(e))
            return

        chapter_dir = os.path.join(output, comic_title, chapter_name)
        if not os.path.exists(chapter_dir):
            os.makedirs(chapter_dir)

        for idx, img_url in enumerate(chapter_pic_list, start=1):
            suffix = img_url.rsplit('.', 1)[-1]
            try:
                img_path = os.path.join(chapter_dir, '{}.{}'.format(idx, suffix))
                if os.path.exists(img_path) and os.path.getsize(img_path) != 0:
                    print('图片已存在, pass', img_path)
                    continue
                with open(img_path, 'wb') as f:
                    response = self.wget(img_url)
                    f.write(response.content)
            except Exception as e:
                print('这张图片下载出错', title, img_url)

        if is_generate_pdf or is_send_email:
            from onepiece.utils.img2pdf import image_dir_to_pdf
            pdf_dir = os.path.join(output, 'pdf - {}'.format(comic_title))
            pdf_path = os.path.join(pdf_dir, '{}.pdf'.format(chapter_name))
            if not os.path.exists(pdf_dir):
                os.makedirs(pdf_dir)

            image_dir_to_pdf(img_dir=chapter_dir,
                             output=pdf_path,
                             sort_by=lambda x: int(x.split('.')[0]))
            if is_send_email:
                from onepiece.utils.mail import send_email
                from onepiece import config
                send_email(sender=config.SENDER,
                           sender_passwd=config.SENDER_PASSWD,
                           receivers=config.RECEIVERS,
                           smtp_server=config.SMTP_SERVER,
                           smtp_port=config.SMTP_PORT,
                           subject=title,
                           content=None,
                           file_list=[pdf_path])
        return chapter_dir

    def get_all_chapter(self, comicid):
        """根据漫画id获取所有的章节列表: http://ac.qq.com/Comic/ComicInfo/id/505430
        Args:
            id: 505430

        Returns:
            [(_id, chater1_title), (_id, chater2_title),]
        """

        url = 'http://www.ishuhui.com/cartoon/book/{}'.format(comicid)
        html = requests.get(url).text
        r = re.search(r'<meta name=ver content="(.*?)">', html)
        ver = json.loads(r.group(1).replace('&#34;', '"'))

        url = 'http://api.ishuhui.com/cartoon/book_ish/ver/{ver}/id/{comicid}.json'\
            .format(ver=random.choice(list(ver.values())), comicid=comicid)
        data = requests.get(url).json()
        comic_title = data['data']['book']['name']
        return comic_title, sorted(data['data']['cartoon']['0']['posts'].items(),
                                   key=lambda x: int(x[0].split('-')[-1]))

    def get_task_chapter(self, comicid, chapter=None, chapter_list=None, download_all=None):
        comic_title, all_chapter = self.get_all_chapter(comicid)
        if chapter:
            number = all_chapter[chapter - 1][0].split('-')[-1]
            for src in all_chapter[chapter - 1][1]:
                chapter_name = '第{}话 {}'.format(number, src['title'])
                _id = src['id']
                source = src['source']
                if source == 1:
                    return [(_id, comic_title, chapter_name)]
            print('该类型资源暂不支持下载！ '.format(chapter_name))
            return []

        task_chapter = []
        all_chapter_len = len(all_chapter)

        for chapter in chapter_list:
            if chapter > all_chapter_len:
                continue
            number = all_chapter[chapter - 1][0].split('-')[-1]
            for src in all_chapter[chapter - 1][1]:
                chapter_name = '第{}话 {}'.format(number, src['title'])
                _id = src['id']
                source = src['source']
                if source == 1:
                    task_chapter.append((_id, comic_title, chapter_name, number))
                    break
            print('该类型资源暂不支持下载！ 第 {} 集 {}'.format(number, chapter_name))
        return task_chapter

    def run(self):
        thread = self.args.thread
        comicid = self.args.comicid
        chapter = self.args.chapter
        interval = self.args.interval
        download_all = self.args.all
        output = self.args.output
        chapter_list = list(parser_interval(interval)) if interval else None
        is_generate_pdf = self.args.pdf
        is_send_email = self.args.mail

        pool = ThreadPool(thread)
        task_chapter = self.get_task_chapter(comicid=comicid,
                                             chapter=chapter,
                                             chapter_list=chapter_list,
                                             download_all=download_all)
        print(task_chapter)
        ts = time.time()
        begin_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))
        print('开始下载咯\n现在时间是:', begin_time)
        pool = ThreadPool(8)

        download_chapter_to_output = functools.partial(self.download_chapter,
                                                       output=output,
                                                       is_generate_pdf=is_generate_pdf,
                                                       is_send_email=is_send_email)
        pool.map(download_chapter_to_output, task_chapter)
        pool.close()
        pool.join()
        cost = int(time.time() - ts)
        print('下载完成啦\n下载用了这么长时间:{0}秒'.format(cost))
