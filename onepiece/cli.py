import argparse
import os
import logging

from .comicbook import ComicBook
from .crawlerbase import CrawlerBase
from .utils import (
    parser_chapter_str,
    ensure_file_dir_exists
)
from .session import SessionMgr
from .image import WorkerPoolMgr
from .utils.mail import Mail
from . import VERSION

logger = logging.getLogger(__name__)
HERE = os.path.abspath(os.path.dirname(__file__))
if os.environ.get('ONEPIECE_DOWNLOAD_DIR'):
    DEFAULT_DOWNLOAD_DIR = os.environ.get('ONEPIECE_DOWNLOAD_DIR')
else:
    DEFAULT_DOWNLOAD_DIR = 'download'

if os.environ.get('MAIL_CONFIG_FILE'):
    DEFAULT_MAIL_CONFIG_FILE = os.environ.get('ONEPIECE_MAIL_CONFIG_FILE')
else:
    DEFAULT_MAIL_CONFIG_FILE = ''


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

    parser = argparse.ArgumentParser(prog="onepiece")

    parser.add_argument('-id', '--comicid', type=str,
                        help="漫画id，如海贼王: 505430 (http://ac.qq.com/Comic/ComicInfo/id/505430)")

    parser.add_argument('--name', type=str, help="漫画名")

    parser.add_argument('-c', '--chapter', type=str, default="-1",
                        help="要下载的章节, 默认下载最新章节。如 -c 666 或者 -c 1-5,7,9-10")

    parser.add_argument('--worker', type=int, default=4, help="线程池数，默认开启4个线程池")

    parser.add_argument('--all', action='store_true',
                        help="是否下载该漫画的所有章节, 如 --all")

    parser.add_argument('--pdf', action='store_true',
                        help="是否生成pdf文件, 如 --pdf")
    parser.add_argument('--single-image', action='store_true',
                        help="是否拼接成一张图片, 如 --single-image")
    parser.add_argument('--quality', type=int, default=95, help="生成长图的图片质量")

    parser.add_argument('--login', action='store_true',
                        help="是否登录账号，如 --login")

    parser.add_argument('--mail', action='store_true',
                        help="是否发送pdf文件到邮箱, 如 --mail。需要预先配置邮件信息。\
                        可以参照config.ini.example文件，创建并修改config.ini文件")

    parser.add_argument('--receivers', type=str, help="邮件接收列表，多个以逗号隔开")
    parser.add_argument('--zip', action='store_true',
                        help="打包生成zip文件")

    parser.add_argument('--config', default=DEFAULT_MAIL_CONFIG_FILE, help="邮件配置文件路径")

    parser.add_argument('-o', '--output', type=str, default=DEFAULT_DOWNLOAD_DIR,
                        help="文件保存路径，默认保存在当前路径下的download文件夹")

    s = ' '.join(['%s(%s)' % (crawler.SITE, crawler.SOURCE_NAME) for crawler in ComicBook.CRAWLER_CLS_MAP.values()])
    site_help_msg = "数据源网站：支持 %s" % s

    parser.add_argument('-s', '--site', type=str, default='qq', choices=ComicBook.CRAWLER_CLS_MAP.keys(),
                        help=site_help_msg)

    parser.add_argument('--verify', action='store_true',
                        help="verify")

    parser.add_argument('--driver-path', type=str, help="selenium driver")

    parser.add_argument('--driver-type', type=str,
                        choices=CrawlerBase.SUPPORT_DRIVER_TYPE,
                        help="支持的浏览器: {}. 默认为 {}".format(
                            ",".join(sorted(CrawlerBase.SUPPORT_DRIVER_TYPE)),
                            CrawlerBase.DEFAULT_DRIVER_TYPE)
                        )

    parser.add_argument('--session-path', type=str, help="读取或保存上次使用的session路径")
    parser.add_argument('--cookies-path', type=str, help="读取或保存上次使用的cookies路径")

    parser.add_argument('--proxy', type=str,
                        help='设置代理，如 --proxy "socks5://user:pass@host:port"')

    parser.add_argument('-V', '--version', action='version', version=VERSION)
    parser.add_argument('--debug', action='store_true', help="debug")

    args = parser.parse_args()
    return args


def init_logger(level=None):
    level = level or logging.INFO
    logger = logging.getLogger()
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s %(name)s %(lineno)s [%(levelname)s] %(message)s",
        datefmt='%Y/%m/%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(level)
    return logger


def download_main(comicbook, output_dir, chapters=None,
                  is_download_all=None, is_gen_pdf=None, is_gen_zip=None,
                  is_single_image=None, quality=None, mail=None, receivers=None, is_send_mail=None):
    quality = quality or 95
    is_gen_pdf = is_gen_pdf or mail
    chapter_str = chapters or '-1'

    logger.info("正在获取最新数据")
    comicbook.start_crawler()
    msg = ("{source_name} 【{name}】 更新至: {last_chapter_number:>03} "
           "【{last_chapter_title}】 数据来源: {source_url}").format(
        source_name=comicbook.source_name,
        name=comicbook.name,
        last_chapter_number=comicbook.last_chapter_number,
        last_chapter_title=comicbook.last_chapter_title,
        source_url=comicbook.source_url)
    logger.info(msg)
    chapter_number_list = parser_chapter_str(chapter_str=chapter_str,
                                             last_chapter_number=comicbook.last_chapter_number,
                                             is_all=is_download_all)
    for chapter_number in chapter_number_list:
        try:
            chapter = comicbook.Chapter(chapter_number)
            logger.info("正在下载 【{}】 {} 【{}】".format(
                comicbook.name, chapter.chapter_number, chapter.title))

            chapter_dir = chapter.save(output_dir=output_dir)
            logger.info("下载成功 %s", chapter_dir)
            if is_single_image:
                img_path = chapter.save_as_single_image(output_dir=output_dir, quality=quality)
                logger.info("生成长图 %s", img_path)
            if is_gen_pdf:
                pdf_path = chapter.save_as_pdf(output_dir=output_dir)
                logger.info("生成pdf文件 %s", pdf_path)

            if is_send_mail:
                mail.send(subject=os.path.basename(pdf_path),
                          content=None,
                          file_list=[pdf_path, ],
                          receivers=receivers)
            if is_gen_zip:
                zip_file_path = chapter.save_as_zip(output_dir=output_dir)
                logger.info("生成zip文件 %s", zip_file_path)
        except Exception:
            logger.exception('download comicbook error. site=%s comicid=%s chapter_number=%s',
                             comicbook.site, comicbook.comicid, chapter_number)


def main():
    args = parse_args()
    site = args.site
    session_path = args.session_path
    cookies_path = args.cookies_path

    loglevel = logging.DEBUG if args.debug else logging.INFO
    init_logger(level=loglevel)

    comicbook = ComicBook(site=args.site, comicid=args.comicid)
    if args.proxy:
        SessionMgr.set_proxy(site=site, proxy=args.proxy)
    if args.verify:
        SessionMgr.set_proxy(site=site, verify=True)

    WorkerPoolMgr.set_worker(worker=args.worker)
    comicbook.crawler.DRIVER_PATH = args.driver_path

    # 加载 session
    if session_path and os.path.exists(session_path):
        SessionMgr.load_session(site=site, path=session_path)
        logger.info('load session success. %s', session_path)

    # 加载cookies
    if cookies_path and os.path.exists(cookies_path):
        SessionMgr.load_cookies(site=site, path=cookies_path)
        logger.info('load cookies success. %s', cookies_path)

    if args.name:
        result = comicbook.search(name=args.name, limit=10)
        for item in result:
            print("comicid={}\tname={}\tsource_url={}".format(item.comicid, item.name, item.source_url))
        comicid = input("请输入要下载的comicid: ")
        comicbook.crawler.comicid = comicid
    if args.login:
        comicbook.crawler.login()

    if args.mail:
        is_send_mail = True
        mail = Mail.init(args.config)
    else:
        is_send_mail = False
        mail = None
    download_main(
        comicbook=comicbook,
        output_dir=args.output,
        chapters=args.chapter,
        is_download_all=args.all,
        is_gen_pdf=args.pdf,
        is_gen_zip=args.zip,
        is_single_image=args.single_image,
        quality=args.quality,
        mail=mail,
        is_send_mail=is_send_mail,
        receivers=args.receivers)

    # 保存 session
    if session_path:
        ensure_file_dir_exists(session_path)
        SessionMgr.export_session(site=site, path=session_path)
        logger.info("session saved. path={}".format(session_path))

    # 保存 cookies
    if cookies_path:
        ensure_file_dir_exists(cookies_path)
        SessionMgr.export_cookies(site=site, path=cookies_path)
        logger.info("cookies saved. path={}".format(cookies_path))


if __name__ == '__main__':
    main()
