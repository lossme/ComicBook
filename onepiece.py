import os
import re
import base64
import json
import time
import socket
from urllib import parse
import click
import requests
from multiprocessing.dummy import Pool as ThreadPool
try:
    from lxml import etree
except:
    pass


socket.setdefaulttimeout(15)

ILLEGAL_STR = r'\/:*?"<>|'
REPLACE_ILLEGAL_STR = str.maketrans(ILLEGAL_STR, ' '*len(ILLEGAL_STR))
HOST = 'http://ac.qq.com'


def get_all_chapter_by_lxml(id):
    """根据漫画id获取所有的章节列表: http://ac.qq.com/Comic/ComicInfo/id/505430
    args:
        id: 505430

    return:
        [(chater1_url, chater1_title), (chater2_url, chater2_title),]
    """
    comic_id = str(id)
    url = 'http://ac.qq.com/Comic/ComicInfo/id/{}'.format(id)
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


def get_all_chapter(id):
    """根据漫画id获取所有的章节列表: http://ac.qq.com/Comic/ComicInfo/id/505430
    args:
        id: 505430

    return:
        [(chater1_url, chater1_title), (chater2_url, chater2_title),]
    """
    url = 'http://ac.qq.com/Comic/ComicInfo/id/{}'.format(id)
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
    args:
        url: 章节的URL如 http://ac.qq.com/ComicView/index/id/505430/cid/884

    return:
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
            img_path = os.path.join(dir_path, str(idx+1) + '.jpg')
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


def get_task_chapter(id, chapter, interval, mode):
    """根据参数来确定下载哪些章节
    args:
        id: 漫画id
        chapter:
            下载的哪个章节,如下载最后一个章节 chapter = -1
        interval:
            下载哪部分章节,如 interval = 1-10,20-30,66
        mode:
            mode = a or mode = all,则下载该漫画的所有章节

    return:
        [(chapter_i_title, chapter_i_url), (chapter_j_title, chapter_j_url)]
    """
    all_chapter = get_all_chapter(id)
    if mode and mode[0] in ['a', 'all']:
        return all_chapter
    if not interval:
        return [all_chapter[chapter]]

    l = []
    blocks = re.split(r',|，', interval)
    for block in blocks:
        if '-' not in block:
            l.append(int(block))
        else:
            start = int(block.split('-')[0])
            end = int(block.split('-')[-1])
            for i in range(start, end+1):
                l.append(i)
    task_chapter = [all_chapter[i - 1] for i in l]
    return task_chapter


MSG = {
    'id': '漫画id，海贼王: 505430 (http://ac.qq.com/Comic/ComicInfo/id/505430)',
    'chapter': '要下载的章节chapter，默认下载最新章节。如 -c 666',
    'interval': '要下载的章节区间, 如 -i 1-5,7,9-10',
    'thread': '线程池数,默认开启8个线程池,下载多个章节时效果才明显'
}


@click.command()
@click.option('-id', '--id', default=505430, help=MSG['id'])
@click.option('-i', '--interval', default='', help=MSG['interval'])
@click.option('-c', '--chapter', default=-1, help=MSG['chapter'])
@click.option('-t', '--thread', default=8, help=MSG['thread'])
@click.argument('mode', nargs=-1)
def main(id, interval, chapter, thread, mode):
    """
    根据腾讯漫画id下载图片,默认下载海贼王最新一集。

    下载海贼王最新一集:
    python3 onepiece.py

    下载漫画 id=505430 最新一集:
    python3 onepiece.py -id 505430

    下载漫画 id=505430 所有章节:
    python3 onepiece.py -id 505430 all

    下载漫画 id=505430 第800集:
    python3 onepiece.py -id 505430 -c 800

    下载漫画 id=505430 倒数第二集:
    python3 onepiece.py -id 505430 -c -2

    下载漫画 id=505430 1到5集,7集，9到10集:
    python3 onepiece.py -id 505430 -i 1-5,7,9-10
    """
    pool = ThreadPool(thread)
    task_chapter = get_task_chapter(id, chapter, interval, mode)
    ts = time.time()
    begin_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))
    print('开始下载咯\n现在时间是:', begin_time)
    pool = ThreadPool(8)
    pool.map(download_chapter, task_chapter)
    pool.close()
    pool.join()
    cost = int(time.time() - ts)
    print('下载完成啦\n下载用了这么长时间:{0}秒'.format(cost))


if __name__ == "__main__":
    main()
