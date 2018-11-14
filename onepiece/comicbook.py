import os
import warnings
import shutil

from concurrent.futures import ThreadPoolExecutor

import requests
from .image_cache import ImageCache


class ComicBook():

    def __init__(self, name, source_name, desc=None, tag=None):
        self.name = name
        self.desc = desc
        self.tag = tag
        self.source_name = source_name

    def __repr__(self):
        return """<ComicBook>
name={name}
desc={desc}
tag={tag}
source_name={source_name}
</ComicBook>""".format(name=self.name, desc=self.desc, tag=self.tag, source_name=self.source_name)

    def get_max_chapter_number(self):
        """需动态注入该方法的具体实现
        :return Chapter instance:
        """

    def get_chapter(self, chapter_number):
        """需动态注入该方法的具体实现
        :return Chapter instance:
        """

    def get_all_chapter(self):
        """需动态注入该方法的具体实现
        :yield Chapter instance:
        """

    def get_comicbook_dir(self, output_dir):
        comicbook_dir = os.path.join(output_dir, self.source_name, self.name)
        if not os.path.exists(comicbook_dir):
            os.makedirs(comicbook_dir)
        return comicbook_dir

    def save(self, chapter_number, output_dir):
        comicbook_dir = self.get_comicbook_dir(output_dir)
        chapter = self.get_chapter(chapter_number)
        chapter_dir, _ = chapter.save(comicbook_dir)
        return chapter_dir

    def save_as_pdf(self, chapter_number, output_dir):
        comicbook_dir = self.get_comicbook_dir(output_dir)
        chapter = self.get_chapter(chapter_number)
        pdf_path = chapter.save_as_pdf(comicbook_dir)
        return pdf_path

    def save_all(self, output_dir):
        chapter_dir_list = []
        comicbook_dir = self.get_comicbook_dir(output_dir)
        for chapter in self.get_all_chapter():
            chapter_dir, _ = chapter.save(comicbook_dir)
            chapter_dir_list.append(chapter_dir)
        return chapter_dir_list

    def save_as_pdf_all(self, output_dir):
        comicbook_dir = self.get_comicbook_dir(output_dir)
        pdf_path_list = []
        for chapter in self.get_all_chapter():
            pdf_path = chapter.save_as_pdf(comicbook_dir)
            pdf_path_list.append(pdf_path)
        return pdf_path_list


class Chapter():
    image_download_pool = ThreadPoolExecutor(max_workers=8)

    def __init__(self, title, chapter_number):
        self.title = title
        self.chapter_number = chapter_number

    def __repr__(self):
        return """<Chapter>
title={title}
chapter_number={chapter_number}
</Chapter>""".format(title=self.title, chapter_number=self.chapter_number)

    def get_chapter_images(self):
        """需动态注入该方法的具体实现
        :return ImageInfo instance list:
        """

    def save(self, output_dir):
        chapter_dir = os.path.join(output_dir, "{} {}".format(self.chapter_number, self.title))
        if not os.path.exists(chapter_dir):
            os.makedirs(chapter_dir)

        future_list = []
        for idx, image in enumerate(self.get_chapter_images(), start=1):
            ext = image.find_suffix(image.image_url)
            target_path = os.path.join(chapter_dir, "{}.{}".format(idx, ext))
            future = self.image_download_pool.submit(image.save, target_path=target_path)
            future_list.append(future)
        return chapter_dir, future_list

    def save_as_pdf(self, output_dir):
        from .utils.img2pdf import image_dir_to_pdf
        # 等全部图片下载完成
        chapter_dir, future_list = self.save(output_dir)
        for future in future_list:
            try:
                future.result()
            except Exception as e:
                warnings.warn(str(e))

        pdf_path = os.path.join(output_dir, "{} {}.pdf".format(self.chapter_number, self.title))
        image_dir_to_pdf(img_dir=chapter_dir,
                         output=pdf_path,
                         sort_by=lambda x: int(x.split('.')[0]))
        return pdf_path


class ImageInfo():
    session = requests.Session()
    TIMEOUT = 30

    def __init__(self, image_url):
        self.image_url = image_url

    def __repr__(self):
        return """<ImageInfo>
image_url={image_url}
</ImageInfo>""".format(image_url=self.image_url)

    @staticmethod
    def find_suffix(image_url, default='jpg', allow=frozenset(['jpg', 'png', 'jpeg', 'gif'])):
        """从图片url提取图片扩展名
        :param image_url: 图片链接
        :param default: 扩展名不在 allow 内，则返回默认扩展名
        :param allow: 允许的扩展名
        :return ext: 扩展名，不包含.
        """
        ext = image_url.rsplit('.', 1)[-1].lower()
        if ext not in allow:
            return default
        return ext

    def save(self, target_path):
        cache_file = ImageCache.get_cache_path(self.image_url)
        shutil.copyfile(cache_file, target_path)
