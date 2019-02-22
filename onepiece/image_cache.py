import re
import os
import hashlib
import time
import shutil
import warnings

import requests
from PIL import Image


class ImageDownloadError():
    pass


HERE = os.path.abspath(os.path.dirname(__file__))


def calc_str_md5(s):
    return hashlib.md5(s.encode()).hexdigest()


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


class ImageCache():
    CACHE_DIR = os.path.abspath(os.path.join(HERE, os.path.pardir, ".cache/image_cache"))
    URL_PATTERN = re.compile(r'^https?://.*')
    EXPIRE = 10 * 24 * 60 * 60   # 缓存有效期 10 天
    session = requests.Session()

    @classmethod
    def set_cache_dir(cls, cache_dir):
        os.makedirs(cache_dir, exist_ok=True)
        cls.CACHE_DIR = cache_dir

    @classmethod
    def to_path(cls, image_path_or_url):
        if not cls.URL_PATTERN.match(image_path_or_url):
            return image_path_or_url
        s = calc_str_md5(image_path_or_url)
        return os.path.join(cls.CACHE_DIR, s[0:2], s[2:4], s[4:6], s)

    @classmethod
    @retry(times=3, delay=1)
    def download_image(cls, image_url, target_path):
        try:
            response = cls.session.get(image_url)
            if response.status_code != 200:
                raise ImageDownloadError('图片下载失败: status_code={} image_url={}'.format(response.status_code, image_url))
        except Exception as e:
            raise ImageDownloadError("图片下载失败: image_url={} error: {}".format(image_url, e))
        image_dir = os.path.dirname(target_path)
        os.makedirs(image_dir, exist_ok=True)
        with open(target_path, 'wb') as f:
            f.write(response.content)
        return target_path

    @classmethod
    def get_cache_path(cls, image_path_or_url):
        image_path = cls.to_path(image_path_or_url)
        if not os.path.exists(image_path):
            if cls.URL_PATTERN.match(image_path_or_url):
                cls.download_image(image_url=image_path_or_url, target_path=image_path)
        return image_path

    @classmethod
    def get_thumbnail_cached_path(cls, image_path_or_url, size=(250, 250)):
        """
        :param str image_path_or_url: 原图路径/url
        """
        path = cls.get_cache_path(image_path_or_url)
        thumbnail_cached_path = "{}_{}x{}".format(path, size[0], size[1])
        if not os.path.exists(thumbnail_cached_path):
            image = Image.open(path)
            image = image.convert("RGB")
            image.thumbnail(size, Image.ANTIALIAS)
            image.save(thumbnail_cached_path, quality=95, format='JPEG')
        return thumbnail_cached_path

    @classmethod
    def open_image(cls, image_path_or_url):
        image_path = cls.get_cache_path(image_path_or_url)
        return Image.open(image_path)

    @classmethod
    def auto_clean(cls):
        """
        清除超过有效期的文件
        """
        now = time.time()
        for file_path in walk(cls.CACHE_DIR):
            if now - os.path.getctime(file_path) > cls.EXPIRE:
                os.remove(file_path)

    @classmethod
    def delete(cls, image_path_or_url):
        image_path = cls.to_path(image_path_or_url)
        if os.path.exists(image_path):
            os.remove(image_path)

    @classmethod
    def remove_thumbnail(cls):
        """
        删除所有缩略图
        """
        pattern = re.compile(r".*?\w{32}_\d+x\d+$")
        for file_path in walk(cls.CACHE_DIR):
            if pattern.match(file_path):
                os.remove(file_path)

    @classmethod
    def remove_cache(cls):
        try:
            shutil.rmtree(cls.CACHE_DIR)
        except Exception as e:
            warnings.warn(str(e))
        cls.set_cache_dir(cache_dir=cls.CACHE_DIR)
