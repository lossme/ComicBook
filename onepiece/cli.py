import argparse
import os

from .comicbook import ComicBook
from .image_cache import ImageCache
from .utils import get_current_time_str
from .utils.mail import Mail
from . import VERSION


def parser_chapter(chapter):
    """将字符串描述的区间转化为一个一个数字
    :param str chapter: 类似 1-10,20-30,66 这样的字符串
    :return list number_list: [1, 2, 3, 4, ...]
    """
    appeared = set()
    rv = []
    for block in chapter.split(','):
        if '-' in block:
            start, end = block.split('-', 1)
            start, end = int(start), int(end)
            for number in range(start, end + 1):
                if number not in appeared:
                    appeared.add(number)
                    rv.append(number)
        else:
            number = int(block)
            if number not in appeared:
                appeared.add(number)
                rv.append(number)
    return rv


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

    parser.add_argument('-c', '--chapter', type=str, default="-1",
                        help="要下载的章节, 默认下载最新章节。如 -c 666 或者 -c 1-5,7,9-10")

    parser.add_argument('--worker', type=int, default=4, help="线程池数，默认开启4个线程池")

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

    parser.add_argument('--site', type=str, default='qq', choices=ComicBook.SUPPORT_SITE,
                        help="数据源网站：支持{}".format(','.join(ComicBook.SUPPORT_SITE)))

    parser.add_argument('-V', '--version', action='version', version=VERSION)

    args = parser.parse_args()
    return args


def main():
    args = parse_args()

    try:
        _chapter_number_list = [int(args.chapter), ]
    except ValueError:
        _chapter_number_list = parser_chapter(args.chapter)

    site = args.site
    comicid = args.comicid
    output_dir = args.output
    is_download_all = args.all
    is_send_mail = args.mail
    is_gen_pdf = args.pdf

    if args.mail:
        Mail.init(args.config)

    if comicid is None:
        if site == "ishuhui":
            comicid = 1
        elif site == "qq":
            comicid = 505430

    print("{} 正在获取最新数据".format(get_current_time_str()))
    ComicBook.init(worker=args.worker)
    comicbook = ComicBook.create_comicbook(site=site, comicid=comicid)
    max_chapter_number = comicbook.get_max_chapter_number()
    print("{} 更新至 {}".format(comicbook.name, max_chapter_number))

    if is_download_all:
        chapter_number_list = list(range(1, max_chapter_number))
    else:
        chapter_number_list = []
        for chapter_number in _chapter_number_list:
            if chapter_number < 0:
                chapter_number = max_chapter_number - chapter_number - 1
            chapter_number_list.append(chapter_number)

    for chapter_number in chapter_number_list:
        try:
            chapter = comicbook.get_chapter(chapter_number)
            print("正在下载 {} {} {}".format(comicbook.name, chapter_number, chapter.title))
            if is_gen_pdf or is_send_mail:
                pdf_path = comicbook.save_as_pdf(chapter_number=chapter_number, output_dir=output_dir)
                if is_send_mail:
                    Mail.send(subject=os.path.basename(pdf_path),
                              content=None,
                              file_list=[pdf_path, ])
            else:
                comicbook.save(chapter_number=chapter_number, output_dir=output_dir)
        except Exception as e:
            print(e)

    ImageCache.auto_clean()


if __name__ == '__main__':
    main()
