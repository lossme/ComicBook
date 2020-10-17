import logging
from flask import (
    Flask,
    jsonify,
    current_app
)


def create_app(cfg='api.config.ProductionConfig'):
    app = Flask(__name__)
    app.config.from_object(cfg)
    log_level = app.config.get('LOG_LEVEL')
    init_logger(level=log_level)

    app.url_map.strict_slashes = False
    from .views import app as api_app
    from .views import aggregate_app
    app.register_blueprint(api_app)
    app.register_blueprint(aggregate_app)
    app.add_url_rule('/', 'index', index)
    return app


def create_dev_app():
    return create_app(cfg='api.config.DevelopmentConfig')


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
    prefix = current_app.config.get('URL_PREFIX', '')
    examples = []
    for site, crawler in ComicBook.CRAWLER_CLS_MAP.items():
        item = dict(site=site, source_name=crawler.SOURCE_NAME, examples=[])
        examples.append(item)

        site_examples = item['examples']
        # 漫画信息
        site_examples.append(prefix + '/api/{site}/comic/{comicid}'.format(
            site=site, comicid=crawler.DEFAULT_COMICID))

        # 章节详情
        site_examples.append(prefix + '/api/{site}/comic/{comicid}/1'.format(
            site=site, comicid=crawler.DEFAULT_COMICID))

        # 搜索
        site_examples.append(prefix + '/api/{site}/search?name={name}&page={page}'.format(
            site=site, name=crawler.DEFAULT_SEARCH_NAME, page=1))

        # 最近更新
        site_examples.append(prefix + '/api/{site}/latest?page={page}'.format(
            site=site, page=1))

        # 查看所有tags
        site_examples.append(prefix + '/api/{site}/tags'.format(site=site))

        # 根据tag查询
        site_examples.append(prefix + '/api/{site}/list?tag={tag}&page={page}'.format(
            site=site, tag=crawler.DEFAULT_TAG, page=1))

    aggregate_examples = []
    aggregate_examples.append(prefix + '/aggregate/search?name=海贼&site=bilibili,u17')

    return jsonify(
        {
            "api_examples": examples,
            "aggregate_examples": aggregate_examples
        }
    )
