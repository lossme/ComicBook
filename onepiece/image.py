import re
import os
import time
import logging
import PIL.Image
from PIL import UnidentifiedImageError
from concurrent.futures import ThreadPoolExecutor

from .exceptions import ImageDownloadError
from .session import SessionMgr
from .utils import ensure_file_dir_exists


HERE = os.path.abspath(os.path.dirname(__file__))
PROJECT_HOME = os.path.abspath(os.path.join(HERE, os.path.pardir))

logger = logging.getLogger(__name__)


def retry(times=3, delay=0):
    def _wrapper1(func):
        def _wrapper2(*args, **kwargs):
            i = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    i += 1
                    if i > times:
                        raise e
                    time.sleep(delay)
        return _wrapper2
    return _wrapper1


def walk(rootdir):
    for parent, dirnames, filenames in os.walk(rootdir):
        for filename in filenames:
            yield os.path.join(parent, filename)


class WorkerPoolMgr(object):
    WORKER_POOL = None
    POOL_SIZE = 4

    @classmethod
    def get_pool(cls):
        if cls.WORKER_POOL is None:
            cls.WORKER_POOL = ThreadPoolExecutor(max_workers=cls.POOL_SIZE)
        return cls.WORKER_POOL

    @classmethod
    def set_worker(cls, worker=4):
        cls.POOL_SIZE = worker
        if cls.WORKER_POOL:
            cls.WORKER_POOL._max_workers = worker


class ImageDownloader(object):
    URL_PATTERN = re.compile(r'^https?://.*')

    def __init__(self, site):
        self.site = site

        self.image_download_pool = None
        self.pool_size = 4
        self.timeout = 30

    def set_timeout(self, timeout=30):
        self.timeout = timeout

    def get_session(self):
        return SessionMgr.get_session(site=self.site)

    @retry(times=3, delay=1)
    def download_image(self, image_url, target_path, image_pipeline=None, **kwargs):
        if os.path.exists(target_path):
            try:
                self.verify_image(target_path)
                return target_path
            except Exception:
                pass
        try:
            session = self.get_session()
            response = session.get(image_url, timeout=self.timeout, **kwargs)
            if response.status_code != 200:
                msg = 'img download error: url=%s status_code=%s' % (image_url, response.status_code)
                raise ImageDownloadError(msg)
        except Exception as e:
            msg = "img download error: url=%s error: %s" % (image_url, e)
            raise ImageDownloadError(msg) from e
        ensure_file_dir_exists(target_path)
        with open(target_path, 'wb') as f:
            f.write(response.content)
        try:
            self.verify_image(target_path)
        except UnidentifiedImageError as e:
            os.unlink(target_path)
            raise ImageDownloadError(f'Corrupt image from {image_url}') from e

        if image_pipeline:
            image_pipeline(target_path)
        return target_path

    def verify_image(self, image_path):
        suffix = image_path.split('.')[-1]
        webp_head = bytes.fromhex("524946462A73010057454250")
        if suffix.lower() == 'webp':
            head = open(image_path, 'rb').read(12)
            if head[:4] == webp_head[:4] and head[-4:] == webp_head[-4:]:
                return True
        with PIL.Image.open(image_path) as img:
            img.verify()

    def download_images(self, image_urls, output_dir, image_pipelines=None, **kwargs):
        """下载出错只打印出警告信息，不抛出异常
        """
        pool = WorkerPoolMgr.get_pool()
        future_list = []
        for idx, image_url in enumerate(image_urls, start=1):
            ext = self.find_suffix(image_url)
            target_path = os.path.join(output_dir.rstrip(), "{}.{}".format(idx, ext))
            if image_pipelines:
                image_pipeline = image_pipelines[idx - 1]
            else:
                image_pipeline = None
            future = pool.submit(
                self.download_image,
                image_url=image_url,
                target_path=target_path,
                image_pipeline=image_pipeline,
                **kwargs)
            future_list.append(future)

        # 等全部图片下载完成
        for future in future_list:
            try:
                future.result()
            except Exception as e:
                logger.warn('image download error. error=%s', e)
        return output_dir

    @staticmethod
    def find_suffix(image_url, default='jpg',
                    allow=frozenset(['jpg', 'png', 'jpeg', 'gif', 'webp'])):
        """从图片url提取图片扩展名
        :param image_url: 图片链接
        :param default: 扩展名不在 allow 内，则返回默认扩展名
        :param allow: 允许的扩展名
        :return ext: 扩展名，不包含.
        """
        url = image_url.split('?')[0]
        ext = url.rsplit('.', 1)[-1].lower()
        if ext in allow:
            return ext
        return default
