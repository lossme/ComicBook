import argparse
import time
import os
from concurrent.futures import ThreadPoolExecutor


from .site import ComicBook
from .utils import parser_interval
from .utils.mail import Mail
from .downloader import Downloader
from . import VERSION


def parse_args():
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

    parser = argparse.ArgumentParser()

    parser.add_argument('-id', '--comicid', type=int,
                        help="漫画id，海贼王: 505430 (http://ac.qq.com/Comic/ComicInfo/id/505430)")

    parser.add_argument('--name', type=str, help="漫画名")

    parser.add_argument('-i', '--interval', type=str,
                        help="要下载的章节区间, 如 -i 1-5,7,9-10")

    parser.add_argument('-c', '--chapter', type=int, default=-1,
                        help="要下载的章节chapter，默认下载最新章节。如 -c 666")

    parser.add_argument('-t', '--thread', type=int, default=8,
                        help="线程池数，默认开启8个线程池，下载多个章节时效果才明显")

    parser.add_argument('--all', action='store_true',
                        help="若设置了则下载该漫画的所有章节, 如 --all")

    parser.add_argument('--pdf', action='store_true',
                        help="若设置了则生成pdf文件, 如 --pdf")

    parser.add_argument('--mail', action='store_true',
                        help="若设置了则发送到邮箱, 如 --mail。需要预先配置邮件信息。\
                        可以参照config.ini.example文件，创建并修改config.ini文件"
                        )

    parser.add_argument('--config', default="config.ini",
                        help="配置文件路径，默认取当前目录下的config.ini"
                        )

    parser.add_argument('-o', '--output', type=str, default='./download',
                        help="文件保存路径，默认保存在当前路径下的download文件夹")

    parser.add_argument('--site', type=str, default='qq', choices=ComicBook.ALL_SITE,
                        help="数据源网站：支持{}".format(','.join(ComicBook.ALL_SITE)))

    parser.add_argument('-V', '--version', action='version', version=VERSION)

    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    chapter_number_list = [args.chapter]
    if args.interval:
        chapter_number_list = parser_interval(args.interval)
    comic_book = ComicBook.create(site=args.site)
    task = comic_book.get_task_chapter(comicid=args.comicid,
                                       name=args.name,
                                       chapter_number_list=chapter_number_list,
                                       is_download_all=args.all)
    if args.mail:
        Mail.init(args.config)

    ts = time.time()
    begin_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))
    print('任务开始咯\n现在时间是:', begin_time)

    with ThreadPoolExecutor(max_workers=args.thread) as executor:
        downloader = Downloader()
        for chapter in task:
            future = executor.submit(downloader.download_chapter,
                                     chapter=chapter,
                                     output_dir=args.output,
                                     is_generate_pdf=args.pdf or args.mail)
            if args.mail:
                future.add_done_callback(
                    lambda future: Mail.send(subject=os.path.basename(future.result()[1]),
                                             content=None,
                                             file_list=[future.result()[1]]))
    cost = int(time.time() - ts)
    print('任务完成啦\n总共用了这么长时间:{0}秒'.format(cost))


if __name__ == '__main__':
    main()
