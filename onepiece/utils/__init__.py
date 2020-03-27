import time

ILLEGAL_STR = r'\/:*?"<>|'


def safe_filename(filename, replace=' '):
    """文件名过滤非法字符串
    """
    replace_illegal_str = str.maketrans(
        ILLEGAL_STR, replace * len(ILLEGAL_STR))
    new_filename = filename.translate(replace_illegal_str).strip()
    if new_filename:
        return new_filename
    raise Exception('文件名不合法. new_filename={}'.format(new_filename))


def get_current_time_str():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


def parser_chapter_str(chapter_str, last_chapter_number, is_all=None):
    """将字符串描述的区间转化为一个一个数字
    :param str chapter: 类似 1-10,20-30,66 这样的字符串
    :return list number_list: [1, 2, 3, 4, ...]
    """
    if is_all:
        return list(range(1, last_chapter_number + 1))

    try:
        chapter_number = int(chapter_str)
        if chapter_number < 0:
            chapter_number = last_chapter_number + chapter_number + 1
        return [chapter_number, ]
    except ValueError:
        pass

    appeared = set()
    chapter_number_list = []
    for block in chapter_str.split(','):
        if '-' in block:
            start, end = block.split('-', 1)
            start, end = int(start), int(end)
            for number in range(start, end + 1):
                if number not in appeared:
                    appeared.add(number)
                    chapter_number_list.append(number)
        else:
            number = int(block)
            if number not in appeared:
                appeared.add(number)
                chapter_number_list.append(number)
    return chapter_number_list
