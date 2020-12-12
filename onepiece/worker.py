from concurrent.futures import ThreadPoolExecutor


class WorkerPoolMgr(object):
    WORKER_POOL = None
    POOL_SIZE = 4

    @classmethod
    def get_pool(cls):
        if cls.WORKER_POOL is None:
            cls.WORKER_POOL = ThreadPoolExecutor(max_workers=cls.POOL_SIZE)
        return cls.WORKER_POOL

    @classmethod
    def set_worker(cls, worker=4):
        cls.POOL_SIZE = worker
        if cls.WORKER_POOL:
            cls.WORKER_POOL._max_workers = worker


def concurrent_run(zip_args):
    pool = WorkerPoolMgr.get_pool()
    future_list = []
    for func, kwargs in zip_args:
        future = pool.submit(func, **kwargs)
        future_list.append(future)
    ret = []
    for future in future_list:
        try:
            result = future.result()
            for i in result:
                ret.append(i)
        except Exception:
            logger.exception('task error. future=%s future._exception=%s', future, future._exception)
    return ret


def run_in_background(func, **kwargs):
    pool = WorkerPoolMgr.get_pool()
    pool.submit(func, **kwargs)
