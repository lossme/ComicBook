import os
import smtplib
from smtplib import SMTP_SSL
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart


class Mail():
    sender = None
    sender_passwd = None
    receivers = None
    smtp_server = None
    smtp_port = None

    def __init__(self, mail_config_ini_file=None):
        if mail_config_ini_file:
            self.init(mail_config_ini_file)

    @classmethod
    def init(cls, filepath):
        """读取 ini 配置文件
        """
        import configparser

        section = 'mail'
        parser = configparser.ConfigParser()
        parser.read(filepath)
        cls.sender = parser.get(section, 'sender')
        cls.sender_passwd = parser.get(section, 'sender_passwd')
        cls.receivers = parser.get(section, 'receivers')
        cls.smtp_server = parser.get(section, 'smtp_server')
        cls.smtp_port = parser.get(section, 'smtp_port')

    @classmethod
    def send(cls, subject, content=None, file_list=None, debug=None):
        """"
        Args:
            subject: 邮件主题/标题
            content: 正文内容
            file_list: 附件的路径列表
        Returns:
            None
        """
        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['From'] = cls.sender
        msg['To'] = ';'.join(cls.receivers)

        if content is not None:
            msg.attach(MIMEText(content, 'plain', 'utf-8'))

        if file_list is not None:
            for file in file_list:
                msg.attach(cls.built_attach(file))

        try:
            s = SMTP_SSL(cls.smtp_server, cls.smtp_port)
            if debug:
                s.set_debuglevel(1)
            s.login(cls.sender, cls.sender_passwd)
            print('正在向 {} 发送 {}'.format(','.join(cls.receivers), subject))
            s.sendmail(cls.sender, cls.receivers, msg.as_string())
            s.quit()
        except smtplib.SMTPException:
            print('发送邮件时出现错误！')
            raise

    @classmethod
    def built_attach(cls, filepath):
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
