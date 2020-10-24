import re
import json
from urllib.parse import urljoin
import logging

import execjs
from bs4 import BeautifulSoup

from ..crawlerbase import CrawlerBase

logger = logging.getLogger(__name__)


class ManhuaguiCrawler(CrawlerBase):

    SITE = "manhuagui"
    SITE_INDEX = "https://www.manhuagui.com/"
    SOURCE_NAME = "漫画柜"

    IMAGE_URL_PREFIX = 'https://i.hamreus.com'
    LOGIN_URL = urljoin(SITE_INDEX, "/user/login")
    REQUIRE_JAVASCRIPT = True

    DEFAULT_COMICID = 19430
    DEFAULT_SEARCH_NAME = '鬼灭之刃'
    TAGS = [
        dict(name='连载漫画', tag='lianzai'),
        dict(name='完结漫画', tag='wanjie'),
    ]

    def __init__(self, comicid=None):
        super().__init__()
        self.comicid = comicid

    @property
    def source_url(self):
        return self.get_source_url(self.comicid)

    def get_source_url(self, comicid):
        return urljoin(self.SITE_INDEX, "/comic/{}".format(comicid))

    def get_comicbook_item(self):
        html = self.get_html(self.source_url)
        soup = BeautifulSoup(html, 'html.parser')
        name = soup.find('div', {'class': 'book-title'}).h1.text
        desc = soup.find('div', {'id': 'intro-all'}).p.text

        li_list = soup.find('ul', {'class': 'detail-list'}).find_all('li')
        tag_soup = li_list[1].find_all('strong')[0]
        tag = ','.join([a.get('title') for a in tag_soup.previous_element.find_all('a')])
        author_soup = li_list[1].find_all('strong')[1]
        author = author_soup.previous_element.a.get('title')
        img = soup.find('div', attrs={'class': 'book-cover'}).p.img
        cover_image_url = img.get('data-src') or img.get('src')
        status = soup.find('li', {'class': 'status'}).span.span.text
        book = self.new_comicbook_item(name=name,
                                       desc=desc,
                                       tag=tag,
                                       cover_image_url=cover_image_url,
                                       author=author,
                                       source_url=self.source_url,
                                       status=status)
        for a in tag_soup.previous_element.find_all('a'):
            name = a.get('title')
            href = a.get('href')
            tag = href.replace('/list/', '').replace('/', '')
            book.add_tag(name=name, tag=tag)

        chapter_soup = soup.find('div', {'class': 'chapter'})
        h4_list = chapter_soup.find_all('h4')
        div_list = chapter_soup.find_all('div', {'class': 'chapter-list'})
        idx = 1
        ext_idx = 1
        volume_idx = 1
        for h4, div in zip(h4_list, div_list):
            for ul in div.find_all('ul'):
                for li in reversed(ul.find_all('li')):
                    href = li.a.get('href')
                    title = li.a.get('title')
                    full_url = urljoin(self.SITE_INDEX, href)
                    if h4.text.strip() == '单行本':
                        book.add_volume(chapter_number=volume_idx, title=title, source_url=full_url)
                        volume_idx += 1
                    elif h4.text.strip() == '番外篇':
                        book.add_ext_chapter(chapter_number=ext_idx, title=title, source_url=full_url)
                        ext_idx += 1
                    elif h4.text.strip() == '单话':
                        book.add_chapter(chapter_number=idx, title=title, source_url=full_url)
                        idx += 1
        return book

    def get_chapter_item(self, citem):
        html = self.get_html(citem.source_url)
        data = self.extract_mhg_js(html)
        image_urls = []
        for i in data['files']:
            url = self.IMAGE_URL_PREFIX + data['path'] + i + '?e=%(e)s&m=%(m)s' % (data['sl'])
            image_urls.append(url)
        return self.new_chapter_item(chapter_number=citem.chapter_number,
                                     title=citem.title,
                                     image_urls=image_urls,
                                     source_url=citem.source_url)

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

    def search(self, name, page=1, size=None):
        url = urljoin(self.SITE_INDEX, '/s/{}_p{}.html'.format(name, page))
        html = self.get_html(url)
        soup = BeautifulSoup(html, 'html.parser')
        li_list = soup.find_all('li', {'class': 'cf'})
        result = self.new_search_result_item()
        for li_soup in li_list:
            name = li_soup.find('div', {'class': 'book-cover'}).a.get('title')
            img = li_soup.find('div', {'class': 'book-cover'}).a.img
            cover_image_url = img.get('data-src') or img.get('src')
            href = li_soup.find('div', {'class': 'book-cover'}).a.get('href')
            comicid = href.split('/')[2]
            source_url = self.get_source_url(comicid)
            status = li_soup.find('span', {'class': 'tt'}).text
            result.add_result(comicid=comicid,
                              name=name,
                              cover_image_url=cover_image_url,
                              source_url=source_url,
                              status=status)
        return result

    def latest(self, page=1):
        url = 'https://www.manhuagui.com/update/'
        soup = self.get_soup(url)
        result = self.new_search_result_item()
        for div in soup.find_all('div', {'class': 'latest-list'})[page - 1:page]:
            for li in div.find_all('li'):
                name = li.img.get('alt')
                cover_image_url = li.img.get('data-src') or li.img.get('src')
                href = li.a.get('href')
                comicid = href.split('/')[2]
                source_url = self.get_source_url(comicid)
                status = li.find('span', {'class': 'tt'}).text
                result.add_result(comicid=comicid,
                                  name=name,
                                  cover_image_url=cover_image_url,
                                  source_url=source_url,
                                  status=status)
        return result

    def get_tags(self):
        item = self.new_tags_item()
        url = 'https://www.manhuagui.com/list/'
        soup = self.get_soup(url)
        div_list = soup.find('div', {'class': 'filter-nav'}).find_all('div', {'class': 'filter'})
        for idx, div in enumerate(div_list, start=1):
            category = div.label.get_text().strip().replace('：', '')
            for li in div.find_all('li'):
                name = li.a.text
                tag = li.a.get('href').replace('/list/', '').replace('/', '')
                if tag:
                    tag = '%s_%s' % (idx, tag)
                    item.add_tag(category=category, name=name, tag=tag)
        return item

    def get_tag_result(self, tag, page=1):
        result = self.new_search_result_item()
        if tag:
            params = {}
            for i in tag.split(','):
                if re.match(r'\d+_.*', i):
                    idx, t = i.split('_', 1)
                    params[int(idx)] = t
                else:
                    params[0] = i
            query = '_'.join([i[1] for i in sorted(params.items(), key=lambda x: x[0])])
            url = "https://www.manhuagui.com/list/%s/index_p%s.html" % (query, page)
        else:
            url = 'https://www.manhuagui.com/list/index_p%s.html' % page

        soup = self.get_soup(url)
        ul = soup.find('ul', {'id': 'contList'})
        if not ul:
            return result
        for li in ul.find_all('li'):
            status = li.find('span', {'class': 'tt'}).text
            name = li.img.get('alt')
            cover_image_url = li.img.get('data-src') or li.img.get('src')
            href = li.a.get('href')
            comicid = href.split('/')[2]
            source_url = self.get_source_url(comicid)
            result.add_result(comicid=comicid,
                              name=name,
                              cover_image_url=cover_image_url,
                              source_url=source_url,
                              status=status)
        return result

    def login(self):
        self.selenium_login(login_url=self.LOGIN_URL,
                            check_login_status_func=self.check_login_status)

    def check_login_status(self):
        session = self.get_session()
        if session.cookies.get("my", domain=".manhuagui.com"):
            return True
