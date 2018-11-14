import argparse
import importlib
import os
import re

from .image_cache import ImageCache
from .utils import get_current_time_str
from .utils.mail import Mail
from . import VERSION


HERE = os.path.abspath(os.path.dirname(__file__))


SUPPORT_SITE = list(
    map(
        lambda x: x.split(".py")[0],
        filter(
            lambda x: re.match(r"^[a-zA-Z].*?\.py$", x),
            os.listdir(os.path.join(HERE, "site"))
        )
    )
)


def create_comicbook(site, comicid):
    if site not in SUPPORT_SITE:
        raise Exception("site={} 暂不支持")

    module = importlib.import_module(".site.{}".format(site), __package__)
    return module.ComicBookCrawler.create_comicbook(comicid)


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

    parser.add_argument('--worker', type=int, default=8, help="线程池数，默认开启8个线程池")

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

    parser.add_argument('--site', type=str, default='qq', choices=SUPPORT_SITE,
                        help="数据源网站：支持{}".format(','.join(SUPPORT_SITE)))

    parser.add_argument('-V', '--version', action='version', version=VERSION)

    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    try:
        chapter_number_list = [int(args.chapter), ]
    except ValueError:
        chapter_number_list = parser_chapter(args.chapter)

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
    comicbook = create_comicbook(site=site, comicid=comicid)
    print("{} 更新至 {}".format(comicbook.name, comicbook.get_max_chapter_number()))

    if is_download_all:
        if is_send_mail or is_gen_pdf:
            pdf_path_list = comicbook.save_as_pdf_all(output_dir=output_dir)
            if is_send_mail:
                file_number = 10
                for i in range(0, len(pdf_path_list), file_number):
                    start = os.path.basename(pdf_path_list[i])
                    end = os.path.basename(pdf_path_list[i + file_number])
                    Mail.send(subject="start: {} end: {}".format(start, end),
                              content=None,
                              file_list=pdf_path_list[i:file_number])
        else:
            comicbook.save_all(output_dir=output_dir)

    else:
        for chapter_number in chapter_number_list:
            if is_gen_pdf or is_send_mail:
                pdf_path = comicbook.save_as_pdf(chapter_number=chapter_number, output_dir=output_dir)
                if is_send_mail:
                    Mail.send(subject=os.path.basename(pdf_path),
                              content=None,
                              file_list=[pdf_path, ])
            else:
                comicbook.save(chapter_number=chapter_number, output_dir=output_dir)
    ImageCache.auto_clean()


if __name__ == '__main__':
    main()
