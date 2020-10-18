import os
import configparser
import logging
import smtplib
from smtplib import SMTP_SSL
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart


logger = logging.getLogger(__name__)


class Mail():

    def __init__(self, sender, sender_passwd, smtp_server, smtp_port, receivers=None):
        self.sender = sender
        self.sender_passwd = sender_passwd
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.receivers = receivers

    @classmethod
    def init(cls, filepath):
        """读取 ini 配置文件
        """
        section = 'mail'
        parser = configparser.ConfigParser()
        parser.read(filepath)
        sender = parser.get(section, 'sender')
        sender_passwd = parser.get(section, 'sender_passwd')
        receivers = parser.get(section, 'receivers').split(',')
        smtp_server = parser.get(section, 'smtp_server')
        smtp_port = parser.get(section, 'smtp_port')
        return cls(sender=sender,
                   sender_passwd=sender_passwd,
                   smtp_server=smtp_server,
                   smtp_port=smtp_port,
                   receivers=receivers)

    def send(self, subject, content=None, file_list=None, debug=None,
             sender=None, sender_passwd=None, receivers=None):
        """"发送邮件
        :param str subject: 邮件主题/标题
        :param str content: 正文内容
        :param list file_list: 附件的路径列表
        """
        receivers = receivers or self.receivers
        sender = sender or self.sender
        sender_passwd = sender_passwd or self.sender_passwd

        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = ';'.join(receivers)

        if content is not None:
            msg.attach(MIMEText(content, 'plain', 'utf-8'))

        if file_list is not None:
            for file in file_list:
                msg.attach(self.built_attach(file))

        try:
            s = SMTP_SSL(self.smtp_server, self.smtp_port)
            if debug:
                s.set_debuglevel(1)
            s.login(sender, sender_passwd)
            logger.info('sending mail. receivers=%s subject=%s', ','.join(receivers), subject)
            s.sendmail(sender, receivers, msg.as_string())
            s.quit()
        except smtplib.SMTPException:
            logger.exception('send mail failed. subject=%s', subject)
            raise

    @classmethod
    def built_attach(cls, filepath):
        """构建邮件附件
        :param str filepath: 文件路径
        :reutrn attach: 邮件附件
        """
        dirname, filename = os.path.split(filepath)
        attach = MIMEApplication(open(filepath, "rb").read())
        attach.add_header('Content-Disposition', 'attachment', filename=('utf-8', '', filename))
        return attach
