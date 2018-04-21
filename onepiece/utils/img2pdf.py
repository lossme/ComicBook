import os

from PIL import Image as PILImage
from reportlab.platypus import SimpleDocTemplate, Image, PageBreak
from reportlab.lib.pagesizes import A4, landscape


def imgs_to_pdf(output, img_path_list):
    """将一组图片合成一个pdf文件
    Args:
        output: 输出pdf文件路径
        img_path_list: 要合成的图片的路径列表
    Returns:
        output: 输出pdf文件路径
    """
    a4_w, a4_h = landscape(A4)
    a4_ratio = a4_h / a4_w

    all_page = []
    for img_path in img_path_list:
        img_w, img_h = PILImage.open(img_path).size

        # 自动拉伸
        ratio = 1
        if img_w / img_h > a4_ratio:
            ratio = a4_w / img_w
        else:
            ratio = a4_h / img_h
        img = Image(img_path, img_w * ratio, img_h * ratio)

        all_page.append(img)
        all_page.append(PageBreak())
    pdf = SimpleDocTemplate(output, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    pdf.build(all_page)
    return output


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
