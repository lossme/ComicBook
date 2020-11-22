import time
import os
import logging
import zipfile

from PIL import Image

logger = logging.getLogger(__name__)

ILLEGAL_STR = r'\/:*?"<>|'


def safe_filename(filename, replace=' '):
    """文件名过滤非法字符串
    """
    replace_illegal_str = str.maketrans(
        ILLEGAL_STR, replace * len(ILLEGAL_STR))
    new_filename = filename.translate(replace_illegal_str).strip()
    if new_filename:
        return new_filename
    raise Exception('文件名不合法. new_filename={}'.format(new_filename))


def get_current_time_str():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


def parser_chapter_str(chapter_str, last_chapter_number, is_all=None):
    """将字符串描述的区间转化为一个一个数字
    :param str chapter: 类似 1-10,20-30,66 这样的字符串
    :return list number_list: [1, 2, 3, 4, ...]
    """
    if is_all:
        return list(range(1, last_chapter_number + 1))

    try:
        chapter_number = int(chapter_str)
        if chapter_number < 0:
            chapter_number = last_chapter_number + chapter_number + 1
        return [chapter_number, ]
    except ValueError:
        pass

    appeared = set()
    chapter_number_list = []
    for block in chapter_str.split(','):
        if '-' in block:
            start, end = block.split('-', 1)
            start, end = int(start), int(end)
            for number in range(start, end + 1):
                if number not in appeared:
                    appeared.add(number)
                    chapter_number_list.append(number)
        else:
            number = int(block)
            if number not in appeared:
                appeared.add(number)
                chapter_number_list.append(number)
    return chapter_number_list


def find_all_image(img_dir, sort_by=None):
    allow_image_suffix = ('jpg', 'jpeg', 'png', 'gif', 'webp')
    img_path_list = sorted(os.listdir(img_dir), key=sort_by)
    img_path_list = list(filter(lambda x: x.lower() not in allow_image_suffix, img_path_list))
    img_path_list = [os.path.join(img_dir, i)for i in img_path_list]
    return img_path_list


def ensure_file_dir_exists(filepath):
    if filepath and isinstance(filepath, str):
        file_dir = os.path.dirname(filepath)
        if file_dir and not os.path.exists(file_dir):
            os.makedirs(file_dir, exist_ok=True)


def image_dir_to_single_image(img_dir, target_path, sort_by=None, quality=95):
    max_height = 65500
    img_path_list = find_all_image(img_dir=img_dir, sort_by=sort_by)
    img_list = [Image.open(i) for i in img_path_list]
    width = img_list[0].size[0]

    # 图片太大 先分组
    group = 0
    imgs_group = [dict(width=width, height=0, imgs=[])]
    for img in img_list:
        if imgs_group[group]['height'] + img.size[1] >= max_height:
            group += 1
            imgs_group.append(dict(width=width, height=0, imgs=[]))
        imgs_group[group]['imgs'].append(img)
        imgs_group[group]['height'] += img.size[1]

    for idx, item in enumerate(imgs_group, start=1):
        width = item['width']
        height = item['height']
        new_img = Image.new('RGB', (width, height))
        current_h = 0
        img_path = '.'.join([target_path.rsplit('.')[0] + f'-{idx}'] + target_path.rsplit('.')[1:])
        for img in item['imgs']:
            new_img.paste(img, box=(0, current_h))
            current_h += img.size[1]
        new_img.save(img_path, quality=quality)

    return img_path


def image_dir_to_zipfile(img_dir, target_path):
    f = zipfile.ZipFile(target_path, 'w', zipfile.ZIP_DEFLATED)
    arc_basename = os.path.basename(img_dir.rstrip('/'))
    for dirpath, dirnames, filenames in os.walk(img_dir):
        for filename in filenames:
            f.write(os.path.join(dirpath, filename), arcname=os.path.join(arc_basename, filename))
    f.close()
    return target_path
