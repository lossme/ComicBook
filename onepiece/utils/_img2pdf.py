import os

from . import ensure_file_dir_exists
from . import find_all_image


def imgs_to_pdf(img_path_list, target_path):
    """将一组图片合成一个pdf文件
    :param str target_path: 输出pdf文件路径
    :param list img_path_list: 要合成的图片的路径列表
    :return str target_path: 输出pdf文件路径
    """
    from reportlab.lib.pagesizes import A4, portrait
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas

    a4_w, a4_h = portrait(A4)

    c = canvas.Canvas(target_path, pagesize=portrait(A4))
    for img_path in img_path_list:
        img_w, img_h = ImageReader(img_path).getSize()

        if img_w / img_h > a4_w / a4_h:
            # 横图
            ratio = a4_w / img_w
            left_margin = 0
            top_margin = (a4_h - img_h * ratio) / 2
        else:
            # 竖图
            ratio = a4_h / img_h
            left_margin = (a4_w - img_w * ratio) / 2
            top_margin = 0
        c.drawImage(img_path, left_margin, top_margin, img_w * ratio, img_h * ratio)
        c.showPage()
    ensure_file_dir_exists(target_path)
    c.save()
    return target_path


def image_dir_to_pdf_v2(img_dir, target_path, sort_by=None):
    """将一个目录下的所有图片（不递归查找）合成一个pdf文件
    :param str img_dir: 图片目录
    :param str target_path: 输出文件路径
    :param func sort_by: 排序依据，如按文件名数字大小排序 sort_by=lambda x: int(x.split('.')[0])
    :return str target_path: 输出文件路径
    """
    import img2pdf
    img_path_list = find_all_image(img_dir=img_dir, sort_by=sort_by)
    with open(target_path, "wb") as f:
        f.write(img2pdf.convert(img_path_list))


def image_dir_to_pdf_v1(img_dir, target_path, sort_by=None):
    """将一个目录下的所有图片（不递归查找）合成一个pdf文件
    :param str img_dir: 图片目录
    :param str target_path: 输出文件路径
    :param func sort_by: 排序依据，如按文件名数字大小排序 sort_by=lambda x: int(x.split('.')[0])
    :return str target_path: 输出文件路径
    """
    allow_image_suffix = ('jpg', 'jpeg', 'png', 'gif', 'webp')
    img_path_list = sorted(os.listdir(img_dir), key=sort_by)
    img_path_list = list(filter(lambda x: x.lower() not in allow_image_suffix, img_path_list))
    img_path_list = [os.path.join(img_dir, i)for i in img_path_list]
    return imgs_to_pdf(img_path_list=img_path_list, target_path=target_path)

try:
    import img2pdf
    image_dir_to_pdf = image_dir_to_pdf_v2
except ImportError:
    import reportlab
    image_dir_to_pdf = image_dir_to_pdf_v1
