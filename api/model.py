import pytz
import hashlib
import logging

from . import db
from . import const

timezone = pytz.timezone(const.TIME_ZONE)
logger = logging.getLogger(__name__)


class TaskStatus():
    INIT = 1
    RUNNING = 2
    DONE = 3
    FAIL = -1

    TO_DESC = {
        INIT: '初始化',
        RUNNING: '运行中',
        DONE: '完成',
        FAIL: '失败',
    }

    DONE_STATUS = [DONE, FAIL]
    UNDONE_STATUS = [INIT, RUNNING]

    @classmethod
    def to_desc(cls, status):
        return cls.TO_DESC.get(status, status)


class CrawlerTask(db.Model):
    __tablename__ = 'crawler_task'

    id = db.Column(db.Integer, primary_key=True, comment="主键id")
    site = db.Column(db.String(40), comment='站点site')
    comicid = db.Column(db.String(100), comment='漫画id')

    name = db.Column(db.String(100), comment='漫画名字')
    source_url = db.Column(db.String(1000), comment='漫画来源')

    chapter = db.Column(db.String(1000), comment='任务下载的章节 如: 1-10,15,20')
    is_all = db.Column(db.Integer, comment='是否下载所有章节')
    send_mail = db.Column(db.Integer, comment='是否发送邮件 0 否 1 是')
    gen_pdf = db.Column(db.Integer, comment='是否生成pdf文件')
    receivers = db.Column(db.String(1000), comment='邮件接收列表 如: aaa@qq.com,bbb@qq.com')
    status = db.Column(db.Integer, index=True, comment='任务状态 1 初始化 2 运行中 3 完成 -1 失败')
    reason = db.Column(db.String(1000), comment='任务失败原因')

    hash_code = db.Column(db.String(32), comment='任务去重字段')

    create_time = db.Column(db.DateTime, server_default=db.func.now(), index=True,
                            comment='任务创建时间')
    update_time = db.Column(db.DateTime, server_default=db.func.now(), server_onupdate=db.func.now(),
                            index=True, comment='更新时间')

    start_time = db.Column(db.DateTime, comment='任务开始时间')
    cost_time = db.Column(db.Integer, comment='任务耗费时间 单位秒')

    def __repr__(self):
        return '<CrawlerTask %s-%s %s>' % (self.site, self.comicid, self.source_url)

    @classmethod
    def gen_hash(cls, **kwargs):
        obj = hashlib.md5()
        fields = ['site', 'comicid', 'chapter', 'is_all', 'gen_pdf', 'send_mail', 'receivers', ]
        args = [kwargs.get(field) for field in fields]
        s = "-".join(map(str, args))
        obj.update(s.encode())
        return obj.hexdigest()

    def to_dict(self):
        create_time = self.format_time(self.create_time)
        update_time = self.format_time(self.update_time)
        start_time = self.format_time(self.start_time)
        status = TaskStatus.to_desc(self.status)
        return dict(
            id=self.id,
            site=self.site,
            comicid=self.comicid,
            name=self.name,
            chapter=self.chapter,
            source_url=self.source_url,
            send_mail=self.send_mail,
            gen_pdf=self.gen_pdf,
            receivers=self.receivers,
            status=status,
            is_all=self.is_all,
            reason=self.reason or "",
            create_time=create_time,
            update_time=update_time,
            start_time=start_time,
            cost_time=self.cost_time or 0,
        )

    def format_time(self, dt):
        if not dt:
            return ""
        return pytz.utc.localize(dt).astimezone(timezone).strftime('%Y-%m-%d %H:%M:%S')
