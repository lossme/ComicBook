import re
import os
import time
import warnings
import PIL.Image
from concurrent.futures import ThreadPoolExecutor

from .exceptions import ImageDownloadError
from .session import Session


HERE = os.path.abspath(os.path.dirname(__file__))
PROJECT_HOME = os.path.abspath(os.path.join(HERE, os.path.pardir))


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


class ImageDownloader():
    URL_PATTERN = re.compile(r'^https?://.*')

    def __init__(self):
        self._session = None

        self.image_download_pool = None
        self.pool_size = 4
        self.verify = True
        self.timeout = 30

    def set_verify(self, verify=True):
        self.verify = verify

    def set_worker(self, worker=4):
        self.worker = worker

    def set_timeout(self, timeout=30):
        self.timeout = timeout

    def get_session(self):
        if self._session is None:
            self._session = Session.create_session()
        return self._session

    def get_pool(self):
        if self.image_download_pool is None:
            self.image_download_pool = ThreadPoolExecutor(max_workers=self.pool_size)
        return self.image_download_pool

    @retry(times=3, delay=1)
    def download_image(self, image_url, target_path, **kwargs):
        if os.path.exists(target_path):
            try:
                self.verify_image(target_path)
                return target_path
            except Exception:
                pass
        try:
            session = self.get_session()
            response = session.get(image_url, verify=self.verify, timeout=self.timeout, **kwargs)
            if response.status_code != 200:
                msg = 'img download error: url=%s status_code=%s' % (image_url, response.status_code)
                raise ImageDownloadError(msg)
        except Exception as e:
            msg = "img download error: url=%s error: %s" % (image_url, e)
            raise ImageDownloadError(msg) from e

        image_dir = os.path.dirname(target_path)
        os.makedirs(image_dir, exist_ok=True)
        with open(target_path, 'wb') as f:
            f.write(response.content)

        try:
            self.verify_image(target_path)
        except Exception as e:
            os.unlink(target_path)
            raise ImageDownloadError(f'Corrupt image from {image_url}') from e
        return target_path

    def verify_image(self, image_path):
        with PIL.Image.open(image_path) as img:
            img.verify()

    def download_images(self, image_urls, output_dir, **kwargs):
        """下载出错只打印出警告信息，不抛出异常
        """
        pool = self.get_pool()
        future_list = []
        for idx, image_url in enumerate(image_urls, start=1):
            ext = self.find_suffix(image_url)
            target_path = os.path.join(output_dir.rstrip(), "{}.{}".format(idx, ext))
            future = pool.submit(
                self.download_image,
                image_url=image_url, target_path=target_path, **kwargs)
            future_list.append(future)

        # 等全部图片下载完成
        for future in future_list:
            try:
                future.result()
            except Exception as e:
                warnings.warn(str(e))
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
