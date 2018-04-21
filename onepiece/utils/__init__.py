ILLEGAL_STR = r'\/:*?"<>|'
REPLACE_ILLEGAL_STR = str.maketrans(ILLEGAL_STR, ' ' * len(ILLEGAL_STR))


def safe_filename(filename):
    """文件名过滤非法字符串
    """
    return filename.translate(REPLACE_ILLEGAL_STR)


def parser_interval(interval):
    """将字符串描述的区间转化为一个一个数字
    Args:
        interval:
             类似 1-10,20-30,66 这样的字符串
    Yield:
        number
    """
    appeared = set()
    for block in interval.split(','):
        if '-' in block:
            start, end = block.split('-', 1)
            try:
                start, end = int(start), int(end)
                for number in range(start, end + 1):
                    if number not in appeared:
                        appeared.add(number)
                        yield number
            except ValueError:
                print('参数写错了,查看帮助: python3 onepiece.py --help')
                exit(1)
        else:
            try:
                number = int(block)
                if number not in appeared:
                    appeared.add(number)
                    yield number
            except ValueError:
                print('参数写错了,查看帮助: python3 onepiece.py --help')
                exit(1)
