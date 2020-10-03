import re
import json

import execjs
from bs4 import BeautifulSoup
import logging

from ..crawlerbase import (
    CrawlerBase,
    ChapterItem,
    ComicBookItem,
    Citem,
    SearchResultItem)
from ..exceptions import ChapterNotFound, ComicbookNotFound

logger = logging.getLogger(__name__)


class ManhuaguiCrawler(CrawlerBase):

    SITE = "manhuagui"
    SOURCE_NAME = "漫画柜"
    DEFAULT_COMICID = 19430
    DEFAULT_COMIC_NAME = '鬼灭之刃'

    def __init__(self, comicid=None):
        try:
            execjs.get()
        except Exception:
            raise RuntimeError('请先安装nodejs。 https://nodejs.org/zh-cn/')
        super().__init__()
        self.comicid = comicid

    @property
    def source_url(self):
        return "https://www.manhuagui.com/comic/{}".format(self.comicid)

    def get_comicbook_item(self):
        html = self.get_html(self.source_url)
        soup = BeautifulSoup(html, 'html.parser')
        name = soup.find('div', {'class': 'book-title'}).h1.text
        desc = soup.find('div', {'id': 'intro-all'}).p.text

        li_list = soup.find('ul', {'class': 'detail-list cf'}).find_all('li')
        tag_soup = li_list[1].find_all('strong')[0]
        tag = ','.join([a.get('title') for a in tag_soup.previous_element.find_all('a')])
        author_soup = li_list[1].find_all('strong')[1]
        author = author_soup.previous_element.a.get('title')
        cover_image_url = soup.find('div', attrs={'class': 'book-cover fl'}).p.img.get('src')
        citem_dict = {}

        def _sort_func(s):
            href = s.a.get('href')
            return href.split('.')[0].split('/')[-1]
        c_list = soup.find('div', {'class': 'chapter-list'}).find_all('li')
        for idx, li_soup in enumerate(sorted(c_list, key=_sort_func), start=1):
            href = li_soup.a.get('href')
            title = li_soup.a.get('title')
            full_url = "https://www.manhuagui.com" + href
            citem_dict[idx] = Citem(
                chapter_number=idx,
                title=title,
                url=full_url)

        return ComicBookItem(name=name,
                             desc=desc,
                             tag=tag,
                             cover_image_url=cover_image_url,
                             author=author,
                             source_url=self.source_url,
                             source_name=self.SOURCE_NAME,
                             citem_dict=citem_dict)

    def get_chapter_item(self, citem):
        url = citem.url
        html = self.get_html(url)
        data = self.extract_mhg_js(html)
        image_urls = []
        prefix = 'https://i.hamreus.com'
        for i in data['files']:
            url = prefix + data['path'] + i + '?e=%(e)s&m=%(m)s' % (data['sl'])
            image_urls.append(url)
        return ChapterItem(chapter_number=citem.chapter_number,
                           title=citem.title,
                           image_urls=image_urls,
                           source_url=url)

    def extract_mhg_js(self, html):
        js = '(function' + re.findall('function(.*?)</script>', html)[0]
        fun = """
                var LZString = (function() {
                var f = String.fromCharCode;
                var keyStrBase64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=";
                var baseReverseDic = {};
                function getBaseValue(alphabet, character) {
                    if (!baseReverseDic[alphabet]) {
                        baseReverseDic[alphabet] = {};
                        for (var i = 0; i < alphabet.length; i++) {
                            baseReverseDic[alphabet][alphabet.charAt(i)] = i
                        }
                    }
                    return baseReverseDic[alphabet][character]
                }
                var LZString = {
                    decompressFromBase64: function(input) {
                        if (input == null)
                            return "";
                        if (input == "")
                            return null;
                        return LZString._0(input.length, 32, function(index) {
                            return getBaseValue(keyStrBase64, input.charAt(index))
                        })
                    },
                    _0: function(length, resetValue, getNextValue) {
                        var dictionary = [], next, enlargeIn = 4, dictSize = 4, numBits = 3, entry = "", result = [], i, w, bits, resb, maxpower, power, c, data = {
                            val: getNextValue(0),
                            position: resetValue,
                            index: 1
                        };
                        for (i = 0; i < 3; i += 1) {
                            dictionary[i] = i
                        }
                        bits = 0;
                        maxpower = Math.pow(2, 2);
                        power = 1;
                        while (power != maxpower) {
                            resb = data.val & data.position;
                            data.position >>= 1;
                            if (data.position == 0) {
                                data.position = resetValue;
                                data.val = getNextValue(data.index++)
                            }
                            bits |= (resb > 0 ? 1 : 0) * power;
                            power <<= 1
                        }
                        switch (next = bits) {
                        case 0:
                            bits = 0;
                            maxpower = Math.pow(2, 8);
                            power = 1;
                            while (power != maxpower) {
                                resb = data.val & data.position;
                                data.position >>= 1;
                                if (data.position == 0) {
                                    data.position = resetValue;
                                    data.val = getNextValue(data.index++)
                                }
                                bits |= (resb > 0 ? 1 : 0) * power;
                                power <<= 1
                            }
                            c = f(bits);
                            break;
                        case 1:
                            bits = 0;
                            maxpower = Math.pow(2, 16);
                            power = 1;
                            while (power != maxpower) {
                                resb = data.val & data.position;
                                data.position >>= 1;
                                if (data.position == 0) {
                                    data.position = resetValue;
                                    data.val = getNextValue(data.index++)
                                }
                                bits |= (resb > 0 ? 1 : 0) * power;
                                power <<= 1
                            }
                            c = f(bits);
                            break;
                        case 2:
                            return ""
                        }
                        dictionary[3] = c;
                        w = c;
                        result.push(c);
                        while (true) {
                            if (data.index > length) {
                                return ""
                            }
                            bits = 0;
                            maxpower = Math.pow(2, numBits);
                            power = 1;
                            while (power != maxpower) {
                                resb = data.val & data.position;
                                data.position >>= 1;
                                if (data.position == 0) {
                                    data.position = resetValue;
                                    data.val = getNextValue(data.index++)
                                }
                                bits |= (resb > 0 ? 1 : 0) * power;
                                power <<= 1
                            }
                            switch (c = bits) {
                            case 0:
                                bits = 0;
                                maxpower = Math.pow(2, 8);
                                power = 1;
                                while (power != maxpower) {
                                    resb = data.val & data.position;
                                    data.position >>= 1;
                                    if (data.position == 0) {
                                        data.position = resetValue;
                                        data.val = getNextValue(data.index++)
                                    }
                                    bits |= (resb > 0 ? 1 : 0) * power;
                                    power <<= 1
                                }
                                dictionary[dictSize++] = f(bits);
                                c = dictSize - 1;
                                enlargeIn--;
                                break;
                            case 1:
                                bits = 0;
                                maxpower = Math.pow(2, 16);
                                power = 1;
                                while (power != maxpower) {
                                    resb = data.val & data.position;
                                    data.position >>= 1;
                                    if (data.position == 0) {
                                        data.position = resetValue;
                                        data.val = getNextValue(data.index++)
                                    }
                                    bits |= (resb > 0 ? 1 : 0) * power;
                                    power <<= 1
                                }
                                dictionary[dictSize++] = f(bits);
                                c = dictSize - 1;
                                enlargeIn--;
                                break;
                            case 2:
                                return result.join('')
                            }
                            if (enlargeIn == 0) {
                                enlargeIn = Math.pow(2, numBits);
                                numBits++
                            }
                            if (dictionary[c]) {
                                entry = dictionary[c]
                            } else {
                                if (c === dictSize) {
                                    entry = w + w.charAt(0)
                                } else {
                                    return null
                                }
                            }
                            result.push(entry);
                            dictionary[dictSize++] = w + entry.charAt(0);
                            enlargeIn--;
                            w = entry;
                            if (enlargeIn == 0) {
                                enlargeIn = Math.pow(2, numBits);
                                numBits++
                            }
                        }
                    }
                };
                return LZString
            }
            )();
            String.prototype.splic = function(f) {
                return LZString.decompressFromBase64(this).split(f)
            }
            ;

        """
        comic = execjs.compile(fun).eval(js)
        imgData = re.findall(r"SMH\.imgData\((.*?)\)\.preInit\(\)\;", comic)[0]
        return json.loads(imgData)

    def get_image_headers(self):
        headers = {
            'referer': 'https://www.manhuagui.com/',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36'
        }
        return headers

    def search(self, name):
        url = 'https://www.manhuagui.com/s/{}.html'.format(name)
        html = self.get_html(url)
        soup = BeautifulSoup(html, 'html.parser')
        li_list = soup.find_all('li', {'class': 'cf'})
        rv = []
        for li_soup in li_list:
            name = li_soup.find('div', {'class': 'book-cover'}).a.get('title')
            cover_image_url = li_soup.find('div', {'class': 'book-cover'}).a.img.get('src')
            href = li_soup.find('div', {'class': 'book-cover'}).a.get('href')
            comicid = href.split('/')[2]
            source_url = 'https://www.manhuagui.com' + href
            search_result_item = SearchResultItem(site=self.SITE,
                                                  comicid=comicid,
                                                  name=name,
                                                  cover_image_url=cover_image_url,
                                                  source_url=source_url)
            rv.append(search_result_item)
        return rv

    def login(self):
        login_url = "https://www.manhuagui.com/user/login"
        self.selenium_login(login_url=login_url,
                            check_login_status_func=self.check_login_status)

    def check_login_status(self):
        session = self.get_session()
        if session.cookies.get("my", domain=".manhuagui.com"):
            return True
