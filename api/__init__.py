import logging
from flask import (
    Flask,
    jsonify,
    current_app
)
from flask_sqlalchemy import SQLAlchemy
from onepiece.utils import ensure_file_dir_exists
from .const import ConfigKey


db = SQLAlchemy()


def create_app(cfg='api.config.Config'):
    app = Flask(__name__)
    app.config.from_object(cfg)
    log_level = app.config.get(ConfigKey.LOG_LEVEL)
    init_logger(level=log_level)
    app.url_map.strict_slashes = False

    if app.config.get(ConfigKey.SQLITE_FILE):
        ensure_file_dir_exists(app.config.get(ConfigKey.SQLITE_FILE))

    db.init_app(app)

    from .views import (
        app as api_app,
        aggregate_app,
        manage_app
    )

    app.register_blueprint(api_app)
    app.register_blueprint(aggregate_app)
    app.register_blueprint(manage_app)
    app.add_url_rule('/', 'index', index)
    return app


def create_dev_app():
    return create_app(cfg='api.config.DevelopmentConfig')


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


def index():
    from onepiece.comicbook import ComicBook
    prefix = current_app.config.get(ConfigKey.URL_PREFIX, '')
    examples = []
    for site, crawler in ComicBook.CRAWLER_CLS_MAP.items():
        item = dict(
            site=site,
            source_name=crawler.SOURCE_NAME,
            source_index=crawler.SITE_INDEX,
            r18=crawler.R18,
            examples=[])
        examples.append(item)

        site_examples = item['examples']
        comicid = crawler.DEFAULT_COMICID
        search_name = crawler.DEFAULT_SEARCH_NAME
        tag = crawler.DEFAULT_TAG

        site_examples.append(dict(
            desc='根据漫画id 获取漫画信息',
            api=prefix + f'/api/{site}/comic/{comicid}'
        ))

        # 章节详情
        site_examples.append(dict(
            desc='获取章节信息',
            api=prefix + f'/api/{site}/comic/{comicid}/1'
        ))

        # 搜索
        site_examples.append(dict(
            desc='搜索',
            api=prefix + f'/api/{site}/search?name={search_name}&page=1'
        ))

        # 最近更新
        site_examples.append(dict(
            desc="查看站点最近更新",
            api=prefix + f'/api/{site}/latest?page=1'
        ))

        # 查看所有tags
        site_examples.append(dict(
            desc="获取站点所有tags",
            api=prefix + f'/api/{site}/tags'
        ))

        # 根据tag查询
        site_examples.append(dict(
            desc="根据tag查询",
            api=prefix + f'/api/{site}/list?tag={tag}&page=1'
        ))

    aggregate_examples = []
    aggregate_examples.append(dict(
        desc="聚合搜索",
        api=prefix + '/aggregate/search?name=海贼&site=bilibili,u17'
    ))

    manage_examples = []
    manage_examples.append(dict(
        desc='添加任务',
        api=prefix + '/manage/task/add?site=qq&comicid=505430&chapter=-1&gen_pdf=1&send_mail=0',
    ))
    manage_examples.append(dict(
        desc='查看任务',
        api=prefix + '/manage/task/list?page=1',
    ))
    # GET获取/POST更新站点cookies
    manage_examples.append(dict(
        desc='GET获取/POST更新站点cookies',
        api=prefix + f'/manage/cookies/qq',
    ))

    return jsonify(
        {
            "api_examples": examples,
            "aggregate_examples": aggregate_examples,
            "manage_examples": manage_examples
        }
    )
