import os

from .utils import safe_filename


def download_chapter(comic_title, chapter_number, chapter_title, chapter_pics,
                     site_name, output, is_generate_pdf, is_send_email, session):
    """下载整个章节的图片，按漫画名按章节保存
    Args:
        str comic_title: 漫画名
        int chapter_number: 第几集
        str chapter_title: 章节标题
        list / generator chapter_pics: 该集所有图片
        site_name: 站点名 如腾讯漫画，鼠绘漫画
        output: 文件保存路径
        is_generate_pdf: 是否生成pdf
        is_send_email: 是否发送邮件
    Returns:
        chapter_dir: 当前章节漫画目录
    """
    site_name = safe_filename(site_name)
    comic_title = safe_filename(comic_title)
    if chapter_number:
        chapter_title = '第{}话 {}'.format(chapter_number, chapter_title)
    chapter_title = safe_filename(chapter_title)

    chapter_dir = os.path.join(output, site_name, comic_title, chapter_title)
    if not os.path.exists(chapter_dir):
        os.makedirs(chapter_dir)

    print('正在下载', chapter_title)
    for idx, img_url in enumerate(chapter_pics, start=1):
        suffix = img_url.rsplit('.', 1)[-1]
        img_path = os.path.join(chapter_dir, '{}.{}'.format(idx, suffix))
        if os.path.exists(img_path) and os.path.getsize(img_path) != 0:
            print('图片已存在, pass', img_path)
            continue
        try:
            response = session.get(img_url)
            with open(img_path, 'wb') as f:
                f.write(response.content)
        except Exception as e:
            raise Exception('这张图片下载出错', chapter_title, img_url, str(e))
    if is_generate_pdf or is_send_email:
        from .utils.img2pdf import image_dir_to_pdf
        pdf_dir = os.path.join(output, site_name, 'pdf - {}'.format(comic_title))
        pdf_path = os.path.join(pdf_dir, '{}.pdf'.format(chapter_title))
        if not os.path.exists(pdf_dir):
            os.makedirs(pdf_dir)

        image_dir_to_pdf(img_dir=chapter_dir,
                         output=pdf_path,
                         sort_by=lambda x: int(x.split('.')[0]))
        if is_send_email:
            from .utils.mail import send_email
            from . import config
            send_email(sender=config.SENDER,
                       sender_passwd=config.SENDER_PASSWD,
                       receivers=config.RECEIVERS,
                       smtp_server=config.SMTP_SERVER,
                       smtp_port=config.SMTP_PORT,
                       subject=chapter_title,
                       content=None,
                       file_list=[pdf_path])
    return chapter_dir
