import os
import re
import base64
import json
import functools
import time
from urllib import parse
from multiprocessing.dummy import Pool as ThreadPool

import requests

from onepiece.utils import safe_filename, parser_interval


QQ_COMIC_HOST = 'http://ac.qq.com'


class QQComicBook:
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.146 Safari/537.36'
    }

    def __init__(self, args):
        self.args = args
        self.session = requests.session()
        self.name = '腾讯漫画'

    def wget(self, url, **kwargs):
        if 'headers' not in kwargs:
            kwargs['headers'] = self.headers
        return self.session.get(url, **kwargs)

    def get_html(self, url):
        response = self.wget(url)
        return response.text

    def get_all_chapter_by_lxml(self, comicid):
        """根据漫画id获取所有的章节列表: http://ac.qq.com/Comic/ComicInfo/id/505430
        Args:
            comicid: 505430

        Returns:
            [(chater1_url, chater1_title), (chater2_url, chater2_title),]
        """
        from lxml import etree
        comicid = str(comicid)
        url = 'http://ac.qq.com/Comic/ComicInfo/id/{}'.format(comicid)
        html = self.get_html(url)
        tree = etree.HTML(html)
        a_tags = tree.xpath("//ol[@class='chapter-page-all works-chapter-list']/li/p/span/a")
        all_chapter = []
        for a in a_tags:
            title = a.get('title')
            url = parse.urljoin(QQ_COMIC_HOST, a.get('href'))
            if comicid not in url:
                continue
            all_chapter.append((title, url))
        return all_chapter

    def get_all_chapter(self, comicid):
        """根据漫画id获取所有的章节列表: http://ac.qq.com/Comic/ComicInfo/id/505430
        Args:
            id: 505430

        Returns:
            [(chater1_url, chater1_title), (chater2_url, chater2_title),]
        """
        url = 'http://ac.qq.com/Comic/ComicInfo/id/{}'.format(comicid)
        html = self.get_html(url)
        ol = re.search(r'''(<ol class="chapter-page-all works-chapter-list".+?</ol>)''', html, re.S).group()
        all_atag = re.findall(r'''<a.*?title="(.*?)".*?href="(.*?)">(.*?)</a>''', ol, re.S)
        all_chapter = []
        for item in all_atag:
            title, url, _title = item
            comic_title, chapter_name = title.split('：', 1)
            url = parse.urljoin(QQ_COMIC_HOST, url)
            all_chapter.append((url, comic_title, chapter_name))
        return all_chapter

    def get_detail_list(self, url):
        """根据章节的URL获取该章节的图片列表
        Args:
            url: 章节的URL如 http://ac.qq.com/ComicView/index/id/505430/cid/884

        Returns:
            [pic1_url, pic2_url,]
        """
        pic_list = []
        html = self.get_html(url)
        bs64_data = re.search(r"var DATA.+?= '(.+)'", html).group(1)[1:]
        json_str = base64.b64decode(bs64_data).decode('utf-8')
        datail_list = json.loads(json_str)['picture']
        [pic_list.append(i['url']) for i in datail_list]
        return pic_list

    def download_chapter(self, chapter, output, is_generate_pdf=None, is_send_email=None):
        """下载整个章节的图片，按漫画名按章节保存
        Args:
            chapter:
                要下载的章节，chapter = (chapter_url, comic_title, chapter_name)
            output:
                文件保存路径
        Returns:
            dir_path: 当前章节漫画目录
        """
        chapter_url, comic_title, chapter_name = chapter
        title = '{} {}'.format(comic_title, chapter_name)
        comic_title = '{} {}'.format(self.name, comic_title)
        comic_title = safe_filename(comic_title)
        chapter_name = safe_filename(chapter_name)
        print('正在下载', title)
        try:
            chapter_pic_list = self.get_detail_list(chapter_url)
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

    def get_task_chapter(self, comicid, chapter=None, chapter_list=None, download_all=None):
        """根据参数来确定下载哪些章节
        Args:
            comicid: 漫画id
            chapter:
                下载的哪个章节，如下载最后一个章节 chapter = -1
            chapter_list:
                需要下载的章节列表，如 chapter_list = [1, 2, 3]
            download_all:
                若设置成True，则下载该漫画的所有章节

        Returns:
            [(chapter_i_title, chapter_i_url), (chapter_j_title, chapter_j_url)]
        """
        all_chapter = self.get_all_chapter(comicid)
        if download_all:
            return all_chapter
        if chapter:
            idx = chapter - 1 if chapter > 0 else chapter
            return [all_chapter[idx]]

        task_chapter = []
        all_chapter_len = len(all_chapter)
        for c in chapter_list:
            if c <= all_chapter_len:
                task_chapter.append(all_chapter[c - 1])
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
