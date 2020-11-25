## 接口部署

```sh
# 下载源码 clone项目 或从这里下载最新的代码并解压 https://github.com/lossme/TencentComicBook/releases
git clone git@github.com:lossme/TencentComicBook.git
# 切换工作目录
cd TencentComicBook

# 安装依赖
python3 -m pip install -r requirements-api.txt

# 复制`api/config.py.example`并命名为`api/config.py` 并根据实际情况修改`api/config.py`的参数
cp api/config.py.example api/config.py

# 启动接口
gunicorn 'api:create_app()' -b "127.0.0.1:8000" --workers=2 --timeout=10

# 查看可选的配置选项 gunicorn --help
# 文档 http://docs.gunicorn.org/en/latest/settings.html
```

## 接口文档

- [1.1 获取漫画概要信息](#11)
- [1.2 获取章节详情](#12)
- [1.3 搜索接口](#13)
- [1.4 获取最近更新](#14)
- [1.5 获取所有tag](#15)
- [1.6 根据tag搜索](#16)
- [1.7 聚合搜索](#17)
- [2.1 添加到异步任务](#21)
- [2.2 查看任务列表](#22)
- [2.3 查看站点cookies](#23)
- [2.4 更新站点cookies](#24)
- [2.5 查看站点代理配置](#25)
- [2.6 设置站点代理](#26)


### 1.1 获取漫画概要信息

`GET /api/<site>/comic/<comicid>`

请求示例
```sh
curl "http://127.0.0.1:8000/api/bilibili/comic/24742"
```

```json
{
    "author": "尾田荣一郎 集英社",
    "chapters": [
        {
            "chapter_number": 1,
            "source_url": "https://manga.bilibili.com/m/mc24742/218087",
            "title": "ROMANCE DAWN冒险的序幕"
        },
        {
            "chapter_number": 2,
            "source_url": "https://manga.bilibili.com/m/mc24742/218093",
            "title": "戴草帽的路飞"
        }
    ],
    "volumes": [],
    "ext_chapters": [],
    "cover_image_url": "http://i0.hdslb.com/bfs/manga-static/8cfad691e8717f8c189f2b5e93a39d272708f91a.jpg",
    "crawl_time": "2020-08-16 15:06:29",
    "desc": "【此漫画的翻译由版权方提供】拥有财富、名声、权力、这世界上的一切的男人 “海盗王”高路德·罗杰，在临死之前说了一句话，让全世界的人都涌向了大海。“想要我的财宝吗？想要的话，就去拿吧，我把世界上的一切都放在了那里！”，这个世界迎来了“大海盗时代”。",
    "name": "航海王",
    "source_name": "哔哩哔哩漫画",
    "site": "bilibili",
    "source_url": "https://manga.bilibili.com/m/detail/mc24742",
    "tag": "奇幻,热血,冒险",
    "tags": [
        {
            "name":"奇幻",
            "tag":"style_id_998"
        },
        {
            "name":"热血",
            "tag":"style_id_999"
        },
        {
            "name":"冒险",
            "tag":"style_id_1013"
        }
    ]
}
```

- `volumes`: 单行本 数据结构同 `chapters`
- `ext_chapters`: 番外篇 数据结构同`chapters`
- `tags`: 可用于标签搜索，如 `http://127.0.0.1:8000/api/bilibili/list?tag=style_id_998&page=1`

------

### 1.2 获取章节详情

`GET /api/<site>/comic/<comicid>/<chapter_number>`

请求示例
```sh
curl "http://127.0.0.1:8000/api/bilibili/comic/24742/1"
```

```json
{
    "chapter_number": 1,
    "image_urls": [
        "https://i0.hdslb.com/bfs/manga/a978a1834b3ad58fad020e56aaac9faaa0aa941a.jpg?token=73441250b03e3f16%3ANyuRMmMH4QSq3VoxAtaxG5yw%2Bd0%3D%3A1597561590",
        "https://i0.hdslb.com/bfs/manga/535548cebdd5d96cfa87247f07171ccebfa1efa7.jpg?token=73441250b03e3f16%3Awk76wOeUd7daRpAfc%2FHSs1Qkql0%3D%3A1597561590",
        "https://i0.hdslb.com/bfs/manga/f6e50a5bdd38af33c152f7929ee63325b519bfdc.jpg?token=73441250b03e3f16%3Ad57MJZIADxnHC%2FG9TkOIvlK1pLU%3D%3A1597561590"
    ],
    "source_url": "https://manga.bilibili.com/m/mc24742/218087",
    "title": "ROMANCE DAWN冒险的序幕",
    "source_name": "哔哩哔哩漫画",
    "site": "bilibili"
}
```

------

### 1.3 搜索接口

`GET /api/<site>/search?name={name}&page={page}`

请求示例

```sh
curl "http://127.0.0.1:8000/api/qq/search?name=海贼&page=1"
```

```json
{
    "search_result":[
        {
            "comicid":"505430",
            "cover_image_url":"https://manhua.qpic.cn/vertical/0/17_16_48_0e28c8aabf48e91d395689b5f6a7689f.jpg/420",
            "name":"航海王",
            "source_url":"https://ac.qq.com/Comic/ComicInfo/id/505430",
            "source_name": "腾讯漫画",
            "site": "qq",
        },
        {
            "comicid":"531616",
            "cover_image_url":"https://manhua.qpic.cn/vertical/0/17_17_06_cb4ba7f7af603a3380bb1e5ed415804b.jpg/420",
            "name":"航海王（番外篇）",
            "source_url":"https://ac.qq.com/Comic/ComicInfo/id/531616",
            "source_name": "腾讯漫画",
            "site": "qq",
        }
    ]
}
```

------

### 1.4 获取最近更新


`GET /api/<site>/latest?page={page}`

请求示例

```sh
curl "http://127.0.0.1:8000/api/qq/latest?page=1"
```

```json
{
    "latest":[
        {
            "comicid":"505430",
            "cover_image_url":"https://manhua.qpic.cn/vertical/0/17_16_48_0e28c8aabf48e91d395689b5f6a7689f.jpg/420",
            "name":"航海王",
            "source_url":"https://ac.qq.com/Comic/ComicInfo/id/505430",
            "source_name": "腾讯漫画",
            "site": "qq",
        }
    ]
}
```

### 1.5 获取所有tag

`GET /api/<site>/tags`

请求示例

```sh
curl "http://127.0.0.1:8000/api/qq/tags"
```

```json
{
    "tags":[
        {
            "category":"属性",
            "tags":[
                {
                    "name":"全部",
                    "tag":""
                },
                {
                    "name":"付费",
                    "tag":"vip_2"
                },
                {
                    "name":"免费",
                    "tag":"vip_1"
                }
            ]
        },
        {
            "category":"进度",
            "tags":[
                {
                    "name":"全部",
                    "tag":""
                },
                {
                    "name":"连载",
                    "tag":"finish_1"
                },
                {
                    "name":"完结",
                    "tag":"finish_2"
                }
            ]
        },
        {
            "category":"标签",
            "tags":[
                {
                    "name":"恋爱",
                    "tag":"theme_105"
                },
                {
                    "name":"玄幻",
                    "tag":"theme_101"
                },
                {
                    "name":"异能",
                    "tag":"theme_103"
                },
                {
                    "name":"恐怖",
                    "tag":"theme_110"
                },
                {
                    "name":"剧情",
                    "tag":"theme_106"
                },
                {
                    "name":"科幻",
                    "tag":"theme_108"
                },
                {
                    "name":"悬疑",
                    "tag":"theme_112"
                },
                {
                    "name":"奇幻",
                    "tag":"theme_102"
                },
                {
                    "name":"冒险",
                    "tag":"theme_104"
                },
                {
                    "name":"犯罪",
                    "tag":"theme_111"
                },
                {
                    "name":"动作",
                    "tag":"theme_109"
                },
                {
                    "name":"日常",
                    "tag":"theme_113"
                },
                {
                    "name":"竞技",
                    "tag":"theme_114"
                },
                {
                    "name":"武侠",
                    "tag":"theme_115"
                },
                {
                    "name":"历史",
                    "tag":"theme_116"
                }
            ]
        }
    ]
}
```

### 1.6 根据tag搜索

`GET /api/<site>/liat?tag={tag}&page={page}`

请求示例

```sh
# 多个标签搜索不一定支持
curl "http://127.0.0.1:8000/api/qq/list?tag=theme_105,finish_2&page=1"
```

```json
{
    "list":[
        {
            "comicid":"623251",
            "cover_image_url":"https://manhua.qpic.cn/vertical/0/12_20_16_eefe809e406d5076dd13012d48869f89_1499861764052.jpg/420",
            "name":"出柜通告",
            "site":"qq",
            "source_name":"腾讯漫画",
            "source_url":"https://ac.qq.com/Comic/ComicInfo/id/623251",
            "status":""
        },
        {
            "comicid":"642093",
            "cover_image_url":"https://manhua.qpic.cn/vertical/0/27_15_21_78309f29cd87c7cc377394e7eff7451a_1558941691349.jpg/420",
            "name":"早安，亿万萌妻",
            "site":"qq",
            "source_name":"腾讯漫画",
            "source_url":"https://ac.qq.com/Comic/ComicInfo/id/642093",
            "status":""
        }
    ]
}
```

### 1.7 聚合搜索

`GET /aggregate/search?name={name}&site={site}`

请求示例

```sh
curl "http://127.0.0.1:8000/aggregate/search?name=海贼&site=bilibili,u17"
```

```json
{
    "list":[
        {
            "comicid":24742,
            "cover_image_url":"http://i0.hdslb.com/bfs/manga-static/7bcf22ed4904a4346c7aa33887be0e6540d5908f.png",
            "name":"航海王",
            "site":"bilibili",
            "source_name":"哔哩哔哩漫画",
            "source_url":"https://manga.bilibili.com/m/detail/mc24742",
            "status":"连载"
        },
        {
            "comicid":"53210",
            "cover_image_url":"https://cover.u17i.com/2016/06/3531898_1465634794_j1xJ1WwX0zh3.small.jpg",
            "name":"当火影遇上海贼",
            "site":"u17",
            "source_name":"有妖气",
            "source_url":"https://www.u17.com/comic/53210.html",
            "status":""
        }
    ]
}
```


### 2.0 API管理相关 简单的认证

`/manage/`路由下的接口，需要在请求的headers添加`API-Secret`字段，值为`config.py`中的`MANAGE_SECRET`，若配置留空则不用验证

如
```sh
curl -H "API-Secret: 123" "http://127.0.0.1:8000/manage/proxy/qq"
```

### 2.1 添加到异步任务

`GET /manage/task/add`

- site: 站点
- comicid: 漫画id
- params: json字符串
```json
{
    "chapters": "1,2,3",  # 下载的章节数 默认下载最新一集
    "is_download_all": true,   # 是否下载全部 默认否
    "is_gen_pdf": true,   # 是否生成pdf文件 默认否
    "is_gen_zip": true,   # 是否生成zip文件 默认否
    "is_single_image": true,  # 是否生成单图文件 默认否
    "quality": 95,  # 生成的单图图片质量 默认95
    "is_send_mail": true,   # 是否发送邮件 默认否
    "receivers": "123@qq.com,456@qq.com"   # 邮件接收者，不传默认发送到配置文件里的收件人
}
```


请求示例

```sh
curl 'http://127.0.0.1:8000/manage/task/add?site=qq&comicid=505430&params={"chapters": "1","is_download_all":false}'
```

```json
{
    "data":{
        "chapter":"3",
        "comicid":"505430",
        "cost_time":0,
        "create_time":"2020-10-18 22:51:54",
        "gen_pdf":1,
        "id":1,
        "is_all":0,
        "name":"航海王",
        "reason":"",
        "receivers":"",
        "send_mail":0,
        "site":"qq",
        "source_url":"https://ac.qq.com/Comic/ComicInfo/id/505430",
        "start_time":"",
        "status":"初始化",
        "update_time":"2020-10-18 22:51:54"
    }
}
```


### 2.2 查看任务列表

`GET /manage/task/list?page={page}`

若任务超过10min，任务状态还没变成完成/失败，可能需重新添加异步任务

请求示例

```sh
curl -H "API-Secret: 123" "http://127.0.0.1:8000/manage/task/list?page=1"
```

```json
{
    "list":[
        {
            "chapter":"-11",
            "comicid":"505430",
            "cost_time":1,
            "create_time":"2020-10-18 22:51:54",
            "gen_pdf":1,
            "id":1,
            "is_all":0,
            "name":"航海王",
            "reason":"",
            "receivers":"",
            "send_mail":0,
            "site":"qq",
            "source_url":"https://ac.qq.com/Comic/ComicInfo/id/505430",
            "start_time":"2020-10-18 22:51:54",
            "status":"完成",
            "update_time":"2020-10-18 22:51:54"
        }
    ]
}
```

### 2.3 查看站点cookies
`GET /manage/cookies/{site}`

请求示例

```sh
curl -H "API-Secret: 123" "http://127.0.0.1:8000/manage/cookies/qq"
```

### 2.4 更新站点cookies

`POST /manage/cookies/{site}`


请求示例

```sh
curl -XPOST "http://127.0.0.1:8000/manage/cookies/qq" \
    -H "API-Secret: 123" \
    -H "Content-Type: application/json" -d \
'{
    "cookies": [
        {
            "domain": ".ac.qq.com",
            "name": "xxx",
            "path": "/",
            "secure": false,
            "value": "1604080000"
        }
    ],
    "cover": false
}'
```

- `cover`: 可选参数，是否覆盖，默认不覆盖


### 2.5 查看站点代理配置

`GET /manage/proxy/{site}`

请求示例

```sh
curl "http://127.0.0.1:8000/manage/proxy/qq"
```


### 2.6 设置站点代理

`GET /manage/proxy/{site}?proxy={proxy}`

请求示例

```sh
curl "http://127.0.0.1:8000/manage/proxy/wnacg?proxy=socks5://127.0.0.1:1082"
```
