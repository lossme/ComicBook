import os
import re
import base64
import json
import time
import socket
from urllib import parse
import argparse
import requests
from multiprocessing.dummy import Pool as ThreadPool
try:
    from lxml import etree
except:
    pass


socket.setdefaulttimeout(15)

ILLEGAL_STR = r'\/:*?"<>|'
REPLACE_ILLEGAL_STR = str.maketrans(ILLEGAL_STR, ' ' * len(ILLEGAL_STR))
HOST = 'http://ac.qq.com'


def get_all_chapter_by_lxml(comic_id):
    """根据漫画id获取所有的章节列表: http://ac.qq.com/Comic/ComicInfo/id/505430
    Args:
        comic_id: 505430

    Returns:
        [(chater1_url, chater1_title), (chater2_url, chater2_title),]
    """
    comic_id = str(comic_id)
    url = 'http://ac.qq.com/Comic/ComicInfo/id/{}'.format(comic_id)
    html = requests.get(url).text
    tree = etree.HTML(html)
    a_tags = tree.xpath("//ol[@class='chapter-page-all works-chapter-list']/li/p/span/a")
    all_chapter = []
    for a in a_tags:
        title = a.get('title')
        url = parse.urljoin(HOST, a.get('href'))
        if comic_id not in url:
            continue
        all_chapter.append((title, url))
    return all_chapter


def get_all_chapter(comic_id):
    """根据漫画id获取所有的章节列表: http://ac.qq.com/Comic/ComicInfo/id/505430
    Args:
        id: 505430

    Returns:
        [(chater1_url, chater1_title), (chater2_url, chater2_title),]
    """
    url = 'http://ac.qq.com/Comic/ComicInfo/id/{}'.format(comic_id)
    html = requests.get(url).text
    ol = re.search(r'''(<ol class="chapter-page-all works-chapter-list".+?</ol>)''', html, re.S).group()
    all_atag = re.findall(r'''<a.*?title="(.*?)".*?href="(.*?)">(.*?)</a>''', ol, re.S)
    all_chapter = []
    for item in all_atag:
        title, url, _title = item
        url = parse.urljoin(HOST, url)
        all_chapter.append((title, url))
    return all_chapter


def get_detail_list(url):
    """根据章节的URL获取该章节的图片列表
    Args:
        url: 章节的URL如 http://ac.qq.com/ComicView/index/id/505430/cid/884

    Returns:
        [pic1_url, pic2_url,]
    """
    pic_list = []
    html = requests.get(url).text
    bs64_data = re.search(r"var DATA.+?= '(.+)'", html).group(1)[1:]
    json_str = base64.b64decode(bs64_data).decode('utf-8')
    datail_list = json.loads(json_str)['picture']
    [pic_list.append(i['url']) for i in datail_list]
    return pic_list


def download_chapter(chapter):
    """下载整个章节的图片，按漫画名按章节保存在当前目录下
    """
    title, chapter_url = chapter
    try:
        print('正在下载', title)
        chapter_pic_list = get_detail_list(chapter_url)
    except Exception as e:
        print('error', title, str(e))
        return
    comic_name, chapter_title = title.split('：', 1)
    dir_path = os.path.join(filter_filename(comic_name), filter_filename(chapter_title))
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    for idx, img_url in enumerate(chapter_pic_list):
        try:
            img_path = os.path.join(dir_path, str(idx + 1) + '.jpg')
            if os.path.exists(img_path) and os.path.getsize(img_path) != 0:
                print('图片已存在, pass', img_path)
                continue
            with open(img_path, 'wb') as f:
                f.write(requests.get(img_url).content)
        except Exception as e:
            print('这张图片下载出错', title, img_url)


def filter_filename(filename):
    """windows文件名过滤非法字符串
    """
    return filename.translate(REPLACE_ILLEGAL_STR)


def get_task_chapter(comic_id, chapter, interval, mode):
    """根据参数来确定下载哪些章节
    Args:
        comic_id: 漫画id
        chapter:
            下载的哪个章节,如下载最后一个章节 chapter = -1
        interval:
            下载哪部分章节,如 interval = 1-10,20-30,66
        mode:
            mode = a or mode = all,则下载该漫画的所有章节

    Returns:
        [(chapter_i_title, chapter_i_url), (chapter_j_title, chapter_j_url)]
    """
    all_chapter = get_all_chapter(comic_id)
    if mode and mode[0] in ['a', 'all']:
        return all_chapter
    if not interval:
        chapter = chapter - 1 if chapter > 0 else chapter
        return [all_chapter[chapter]]

    task_chapter = []
    all_chapter_len = len(all_chapter)
    blocks = re.split(r',|，', interval)
    for block in blocks:
        if '-' not in block:
            try:
                chapter_int = int(block)
            except ValueError:
                print('参数写错了,查看帮助: python3 onepiece.py --help')
                exit()
            if chapter_int <= all_chapter_len:
                task_chapter.append(all_chapter[chapter_int - 1])
        else:
            start, end = block.split('-', 1)
            try:
                start, end = int(start), int(end)
                for chapter in all_chapter[start - 1:end]:
                    task_chapter.append(chapter)
            except ValueError:
                print('参数写错了,查看帮助: python3 onepiece.py --help')
                exit()
    return task_chapter


def main(comic_id=505430, interval=None, chapter=-1, thread=8, mode=None):
    pool = ThreadPool(thread)
    task_chapter = get_task_chapter(comic_id, chapter, interval, mode)
    ts = time.time()
    begin_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))
    print('开始下载咯\n现在时间是:', begin_time)
    pool = ThreadPool(8)
    pool.map(download_chapter, task_chapter)
    pool.close()
    pool.join()
    cost = int(time.time() - ts)
    print('下载完成啦\n下载用了这么长时间:{0}秒'.format(cost))


def cli():
    """
    根据腾讯漫画id下载图片,默认下载海贼王最新一集。

    下载海贼王最新一集:
    python3 onepiece.py

    下载漫画 id=505430 最新一集:
    python3 onepiece.py -id 505430

    下载漫画 id=505430 所有章节:
    python3 onepiece.py -id 505430 -m all

    下载漫画 id=505430 第800集:
    python3 onepiece.py -id 505430 -c 800

    下载漫画 id=505430 倒数第二集:
    python3 onepiece.py -id 505430 -c -2

    下载漫画 id=505430 1到5集,7集，9到10集:
    python3 onepiece.py -id 505430 -i 1-5,7,9-10
    """
    MSG = {
        'comic_id': '漫画id，海贼王: 505430 (http://ac.qq.com/Comic/ComicInfo/id/505430)',
        'chapter': '要下载的章节chapter，默认下载最新章节。如 -c 666',
        'interval': '要下载的章节区间, 如 -i 1-5,7,9-10',
        'thread': '线程池数,默认开启8个线程池,下载多个章节时效果才明显',
        'mode': '下载模式，若为 a/all 则下载该漫画的所有章节, 如 -m all'
    }
    parser = argparse.ArgumentParser()
    parser.add_argument('-id', '--comic_id', type=int, default=505430, help=MSG['comic_id'])
    parser.add_argument('-i', '--interval', type=str, help=MSG['interval'])
    parser.add_argument('-c', '--chapter', type=int, default=-1, help=MSG['chapter'])
    parser.add_argument('-t', '--thread', type=int, default=8, help=MSG['thread'])
    parser.add_argument('-m', '--mode', type=str, help=MSG['mode'])
    args = parser.parse_args()
    main(comic_id=args.comic_id, interval=args.interval, chapter=args.chapter, thread=args.thread, mode=args.mode)

if __name__ == "__main__":
    cli()
