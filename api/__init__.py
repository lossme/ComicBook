import logging
import os
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

from onepiece.utils import ensure_file_dir_exists
from onepiece.session import SessionMgr
from onepiece.comicbook import ComicBook
from onepiece.crawlerbase import CrawlerBase
from onepiece.worker import WorkerPoolMgr

from .const import ConfigKey
from . import const
from .common import get_cookies_path

db = SQLAlchemy()
login_manager = LoginManager()

ONEPIECE_FLASK_CONFIG = os.environ.get('ONEPIECE_FLASK_CONFIG') or 'api.config.Config'


def create_app(cfg=ONEPIECE_FLASK_CONFIG):
    app = Flask(__name__)
    app.config.from_object(cfg)
    log_level = app.config.get(ConfigKey.LOG_LEVEL)
    init_logger(level=log_level)
    app.url_map.strict_slashes = False

    if app.config.get(ConfigKey.SQLITE_FILE):
        ensure_file_dir_exists(app.config.get(ConfigKey.SQLITE_FILE))

    db.init_app(app)
    login_manager.init_app(app)

    from .api.views import (
        app as api_app,
        aggregate_app,
    )
    from .manage.views import manage_app
    from .user.views import app as user_app
    from .views import app as index_app
    app.register_blueprint(index_app)
    app.register_blueprint(api_app)
    app.register_blueprint(aggregate_app)
    app.register_blueprint(manage_app)
    app.register_blueprint(user_app)

    init_session(app)
    WorkerPoolMgr.set_worker(const.POOL_SIZE)
    init_db(app)
    if not app.config.get('USERS'):
        app.config['LOGIN_DISABLED'] = True
    return app


def init_session(app):
    CrawlerBase.DRIVER_PATH = app.config.get('DRIVER_PATH', '')
    CrawlerBase.DRIVER_TYPE = app.config.get('DRIVER_TYPE', '')
    CrawlerBase.HEADLESS = True
    with app.app_context():
        proxy_config = app.config.get(ConfigKey.CRAWLER_PROXY, {})
        for site in ComicBook.CRAWLER_CLS_MAP:
            proxy = proxy_config.get(site)
            if proxy:
                SessionMgr.set_proxy(site=site, proxy=proxy)
            cookies_path = get_cookies_path(site=site)
            if os.path.exists(cookies_path):
                SessionMgr.load_cookies(site=site, path=cookies_path)


def init_db(app):
    if app.config.get(ConfigKey.SQLITE_FILE):
        ensure_file_dir_exists(app.config.get(ConfigKey.SQLITE_FILE))
    with app.app_context():
        db.create_all()


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
