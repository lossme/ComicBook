import time

ILLEGAL_STR = r'\/:*?"<>|'


def safe_filename(filename, replace=' '):
    """文件名过滤非法字符串
    """
    replace_illegal_str = str.maketrans(ILLEGAL_STR, replace * len(ILLEGAL_STR))
    return filename.translate(replace_illegal_str)


def get_current_time_str():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
