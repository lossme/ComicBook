import logging
import functools
from concurrent.futures import ThreadPoolExecutor

from . import const


logger = logging.getLogger(__name__)

THREAD_POOL = None


def get_pool():
    global THREAD_POOL
    if THREAD_POOL is None:
        pool_size = const.POOL_SIZE
        THREAD_POOL = ThreadPoolExecutor(max_workers=pool_size)
    return THREAD_POOL


def concurrent_run(zip_args):
    pool = get_pool()
    future_list = []
    for func, kwargs in zip_args:
        future = pool.submit(func, **kwargs)
        future_list.append(future)
    ret = []
    for future in future_list:
        try:
            result = future.result()
            for i in result:
                ret.append(i)
        except Exception:
            logger.exception('task error. future=%s future._exception=%s', future, future._exception)
    return ret


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


def run_in_background(func, **kwargs):
    pool = get_pool()
    pool.submit(func, **kwargs)
