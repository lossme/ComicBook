import time

ILLEGAL_STR = r'\/:*?"<>|'


def safe_filename(filename, replace=' '):
    """文件名过滤非法字符串
    """
    replace_illegal_str = str.maketrans(ILLEGAL_STR, replace * len(ILLEGAL_STR))
    return filename.translate(replace_illegal_str)


def parser_interval(interval):
    """将字符串描述的区间转化为一个一个数字
    Args:
        interval:
             类似 1-10,20-30,66 这样的字符串
    Return:
        number_list: [1, 2, 3, 4, ...]
    """
    appeared = set()
    rv = []
    for block in interval.split(','):
        if '-' in block:
            start, end = block.split('-', 1)
            start, end = int(start), int(end)
            for number in range(start, end + 1):
                if number not in appeared:
                    appeared.add(number)
                    rv.append(number)
        else:
            number = int(block)
            if number not in appeared:
                appeared.add(number)
                rv.append(number)
    return rv


def get_current_time_str():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
