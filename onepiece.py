import click
import os
import re
import base64
import json
import requests
import datetime
import socket
from multiprocessing.dummy import Pool as ThreadPool
try:
    from lxml import etree
except:
    pass


TIMEOUT = 15
socket.setdefaulttimeout(TIMEOUT)


def get_list(id):
    """
    根据URL获取章节列表
    url类似:http://ac.qq.com/Comic/ComicInfo/id/505430
    返回所有的章节信息
    """
    url = 'http://ac.qq.com/Comic/ComicInfo/id/{}'.format(id)
    html = requests.get(url).text
    try:
        tree = etree.HTML(html)
        a_tag = tree.xpath(
            "//ol[@class='chapter-page-all works-chapter-list']/li/p/span/a")
        all_chapter = [{'url': 'http://ac.qq.com' +
                        a.get('href'), 'title': a.get('title')} for a in a_tag]
        all_chapter = list(
            filter(lambda s: re.search(str(id), s['url']), all_chapter))
        return all_chapter
    except Exception as e:
        ol = re.search(r'(<ol class="chapter-page-all works-chapter-list".+?</ol>)', html, re.S).group()
        all_atag = re.findall(r'<a.+?>.+?</a>', ol, re.S)
        all_chapter = []
        for atag in all_atag:
            title_res = re.search(r'title="(.+?)"', atag)
            url_res = re.search(r'href="(.+?)"', atag)
            if title_res and url_res:
                title = title_res.group(1)
                url = 'http://ac.qq.com' + url_res.group(1)
                all_chapter.append({'url': url, 'title': title})
        return all_chapter


def get_detail_list(url):
    """
    根据详细URL获取章节详细页面并解析
    url类似:http://ac.qq.com/ComicView/index/id/505430/cid/884
    """
    pic_list = []
    html = requests.get(url).text
    bs64_data = re.search(r"var DATA.+?= '(.+)'", html).group(1)[1:]
    json_str = base64.b64decode(bs64_data).decode('utf-8')
    datail_list = json.loads(json_str)['picture']
    [pic_list.append(i['url']) for i in datail_list]
    return pic_list


def download_chapter(chapter):
    print('正在抓取图片地址 {0}'.format(chapter['title']))
    chapter['pic_list'] = get_detail_list(chapter['url'])
    comic_name = chapter['title'].split('：')[0]
    title = ''.join(chapter['title'].split('：')[1:])
    pic_list = chapter['pic_list']
    dir_path = os.path.join(filter_filename(
        comic_name), filter_filename(title))
    if not os.path.exists(dir_path):
        try:
            os.makedirs(dir_path)
        except:
            print('目录已存在')
    print('正在下载 {0}'.format(title))
    for i in range(1, len(pic_list)):
        try:
            url = pic_list[i]
            file_path = os.path.join(dir_path, str(i) + '.jpg')
            if is_downloaded(file_path):
                continue
            img = requests.get(url).content
            with open(file_path, 'wb') as f:
                f.write(img)
        except Exception as e:
            print('这张图片下载出错', title, pic_list[i])


def filter_filename(filename):
    '''windows文件名过滤非法字符串'''
    illegal_str = r'\/:*?"<>|'
    repalce_str = r' '*len(illegal_str)
    map_str = filename.maketrans(illegal_str, repalce_str)
    return filename.translate(map_str)


def is_downloaded(file_path):
    if os.path.exists(file_path) and os.path.getsize(file_path) != 0:
        print('{0} 文件已存在,pass'.format(file_path))
        return True
    else:
        return False


def get_task_chapter(id, chapter, interval, mode):
    all_chapter = get_list(id)
    if mode[0] in ['a','all']:
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
    'id': '请输入你想要下载的漫画的id,默认下载海贼王\n\
           如海贼王http://ac.qq.com/Comic/ComicInfo/id/505430\n\
           python3 onepiece.py -id 50430',
    'chapter': '输入要下载的章节chapter，默认下载最新章节\n\
          如倒数第二 -c -2\n\
        ',
    'interval': '下载多个章节,输入章节区间,如 -i 1-10,25,30-40',
    'thread': '线程池数,默认开启8个线程池,下载多个章节时效果才明显',
}


@click.command()
@click.option('-id', '--id', default=505430, help=MSG['id'])
@click.option('-i', '--interval', default='', help=MSG['interval'])
@click.option('-c', '--chapter', default=-1, help=MSG['chapter'])
@click.option('-t', '--thread', default=8, help=MSG['thread'])
@click.argument('mode', nargs=-1)
def main(id, interval, chapter, thread, mode):
    """
    根据腾讯漫画id下载图片

    添加 all/a 关键字即可下载所有章节

    例如 python3 onepiece.py -id 50430 all
    """
    pool = ThreadPool(thread)
    task_chapter = get_task_chapter(id, chapter, interval, mode)
    begin_time = datetime.datetime.now()
    print('开始下载咯\n现在时间是:'+str(begin_time))
    pool = ThreadPool(8)
    pool.map(download_chapter, task_chapter)
    pool.close()
    pool.join()
    cost = (datetime.datetime.now() - begin_time).seconds
    print('下载完成啦\n下载用了这么长时间:{0}秒'.format(cost))


if __name__ == "__main__":
    main()
