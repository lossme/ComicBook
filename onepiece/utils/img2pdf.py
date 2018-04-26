import os

from reportlab.lib.pagesizes import A4, portrait
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


def imgs_to_pdf(output, img_path_list):
    """将一组图片合成一个pdf文件
    Args:
        output: 输出pdf文件路径
        img_path_list: 要合成的图片的路径列表
    Returns:
        output: 输出pdf文件路径
    """
    a4_w, a4_h = portrait(A4)

    c = canvas.Canvas(output, pagesize=portrait(A4))
    for img_path in img_path_list:
        img_w, img_h = ImageReader(img_path).getSize()

        if img_w / img_h > a4_w / a4_h:
            # 宽的图片
            ratio = a4_w / img_w
            left_margin = 0
            top_margin = (a4_h - img_h * ratio) / 2
        else:
            # 长的图片
            ratio = a4_h / img_h
            left_margin = (a4_w - img_w * ratio) / 2
            top_margin = 0
        c.drawImage(img_path, left_margin, top_margin, img_w * ratio, img_h * ratio)
        c.showPage()
    c.save()


def image_dir_to_pdf(img_dir, output, sort_by=None):
    """将一个目录下的所有图片（不递归查找）合成一个pdf文件
    Args:
        img_dir: 图片目录
        output: 输出文件路径
        sort_by: 排序依据，如按文件名数字大小排序 sort_by=lambda x: int(x.split('.')[0])
    Returns:
        output: 输出文件路径
    """
    img_path_list = sorted(os.listdir(img_dir), key=sort_by)
    img_path_list = [os.path.join(img_dir, i)for i in img_path_list]
    return imgs_to_pdf(output, img_path_list)
