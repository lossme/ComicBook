import os
import smtplib
from smtplib import SMTP_SSL
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart


def send_email(sender, sender_passwd, receivers, smtp_server,
               smtp_port, subject, content=None, file_list=None, debug=None):
    """"
    Args:
        sender: 发送者账户
        sender_passwd: 发送者账户密码
        receivers: 邮件接收者列表，如 ['xxx@qq.com', 'yyy@qq.com']
        smpt_host: SMPT主机
        smtp_port: SMPT服务端口（SSL）
        subject: 邮件主题/标题
        content: 正文内容
        file_list: 附件的路径列表
    Returns:
        None
    """
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ';'.join(receivers)

    if content is not None:
        msg.attach(MIMEText(content, 'plain', 'utf-8'))

    if file_list is not None:
        for file in file_list:
            msg.attach(built_attach(file))

    try:
        s = SMTP_SSL(smtp_server, smtp_port)
        if debug:
            s.set_debuglevel(1)
        s.login(sender, sender_passwd)
        s.sendmail(sender, receivers, msg.as_string())
        s.quit()
    except smtplib.SMTPException:
        print('发送邮件时出现错误！')
        raise


def built_attach(filepath):
    """构建邮件附件
    Args:
        filepath: 文件路径
    Returns:
        attach: 邮件附件
    """
    dirname, filename = os.path.split(filepath)
    attach = MIMEApplication(open(filepath, "rb").read())
    attach.add_header('Content-Disposition', 'attachment', filename=('utf-8', '', filename))
    return attach
