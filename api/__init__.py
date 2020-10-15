import logging
from collections import defaultdict
from flask import Flask, jsonify


def create_app():
    init_logger()
    app = Flask(__name__)
    app.config['JSON_AS_ASCII'] = False
    app.url_map.strict_slashes = False

    from .views import app as main_app
    app.register_blueprint(main_app)
    app.add_url_rule('/', 'index', index)
    return app


def init_logger(level=None):
    level = level or logging.INFO
    logger = logging.getLogger()
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s %(name)s [%(levelname)s] %(message)s",
        datefmt='%Y/%m/%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(level)
    return logger


def index():
    from onepiece.comicbook import ComicBook
    examples = defaultdict(list)
    for site, crawler in ComicBook.CRAWLER_CLS_MAP.items():
        # 漫画信息
        examples[site].append('/api/{site}/comic/{comicid}'.format(
            site=site, comicid=crawler.DEFAULT_COMICID))

        # 章节详情
        examples[site].append('/api/{site}/comic/{comicid}/1'.format(
            site=site, comicid=crawler.DEFAULT_COMICID))

        # 搜索
        examples[site].append('/api/{site}/search?name={name}&page={page}'.format(
            site=site, name=crawler.DEFAULT_SEARCH_NAME, page=1))

        # 最近更新
        examples[site].append('/api/{site}/latest?page={page}'.format(
            site=site, page=1))

        # 查看所有tags
        examples[site].append('/api/{site}/tags'.format(site=site))

        # 根据tag查询
        if crawler.TAGS:
            tag = crawler.TAGS[0]['name']
        else:
            tag = ''
        examples[site].append('/api/{site}/list?tag={tag}&page={page}'.format(
            site=site, tag=tag, page=1))

    return jsonify(
        {
            "examples": examples
        }
    )
