import os
import logging
import functools

from flask import (
    jsonify,
    current_app
)
from onepiece.exceptions import (
    NotFoundError,
    SiteNotSupport
)
from onepiece.worker import WorkerPoolMgr
from ..const import ConfigKey

logger = logging.getLogger(__name__)


def log_exception(func):
    @functools.wraps(func)
    def wrap(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.exception('func=%s run error. args=%s kwargs=%s',
                             func.__name__, args, kwargs)
            raise e
    return wrap


def handle_404(error):
    if isinstance(error, NotFoundError):
        return jsonify(dict(message='NotFoundError. {}'.format(error))), 404
    elif isinstance(error, SiteNotSupport):
        return jsonify(dict(message='SiteNotSupport. {}'.format(error))), 400
    else:
        return jsonify(dict(message=str(error))), 500


def get_cookies_path(site):
    cookies_path = os.path.join(current_app.config[ConfigKey.COOKIES_DIR], f'{site}.json')
    return cookies_path
