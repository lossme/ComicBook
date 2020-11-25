import pytz
import hashlib
import logging
import json

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

    params = db.Column(db.String(3000), comment='任务参数')

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
    def gen_hash(cls, site, comicid, params):
        obj = hashlib.md5()
        s = "%s-%s-%s" % (site, comicid, params)
        obj.update(s.encode())
        return obj.hexdigest()

    def to_dict(self):
        create_time = self.format_time(self.create_time)
        update_time = self.format_time(self.update_time)
        start_time = self.format_time(self.start_time)
        params = json.loads(self.params) if self.params else {}
        status = TaskStatus.to_desc(self.status)
        return dict(
            id=self.id,
            site=self.site,
            comicid=self.comicid,
            name=self.name,
            params=params,
            status=status,
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
