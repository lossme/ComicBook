## 接口部署

安装依赖
```sh
pip install -r requirements-api.txt
```

启动接口
```sh
gunicorn 'api:create_app()' -b "127.0.0.1:8000" --workers=2 --timeout=30

# 查看可选的配置选项 gunicorn --help
# 文档 http://docs.gunicorn.org/en/latest/settings.html
```

## 接口文档

- [1.1-获取概要信息](#11)
- [1.2-获取章节详情](#12)
- [1.3-搜索接口](#13)
- [1.4-获取最近更新](#14)
- [1.5-获取所有tag](#15)
- [1.6-根据tag搜索](#16)

### 1.1 获取概要信息

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
    "cover_image_url": "http://i0.hdslb.com/bfs/manga-static/8cfad691e8717f8c189f2b5e93a39d272708f91a.jpg",
    "crawl_time": "2020-08-16 15:06:29",
    "desc": "【此漫画的翻译由版权方提供】拥有财富、名声、权力、这世界上的一切的男人 “海盗王”高路德·罗杰，在临死之前说了一句话，让全世界的人都涌向了大海。“想要我的财宝吗？想要的话，就去拿吧，我把世界上的一切都放在了那里！”，这个世界迎来了“大海盗时代”。",
    "name": "航海王",
    "source_name": "哔哩哔哩漫画",
    "source_url": "https://manga.bilibili.com/m/detail/mc24742",
    "tag": "奇幻,热血,冒险",
    "tags": [],
    "volumes": [],
    "ext_chapters": []
}
```

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
    "title": "ROMANCE DAWN冒险的序幕"
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
            "site":"qq",
            "source_url":"https://ac.qq.com/Comic/ComicInfo/id/505430"
        },
        {
            "comicid":"531616",
            "cover_image_url":"https://manhua.qpic.cn/vertical/0/17_17_06_cb4ba7f7af603a3380bb1e5ed415804b.jpg/420",
            "name":"航海王（番外篇）",
            "site":"qq",
            "source_url":"https://ac.qq.com/Comic/ComicInfo/id/531616"
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
            "site":"qq",
            "source_url":"https://ac.qq.com/Comic/ComicInfo/id/505430"
        },
        {
            "comicid":"531616",
            "cover_image_url":"https://manhua.qpic.cn/vertical/0/17_17_06_cb4ba7f7af603a3380bb1e5ed415804b.jpg/420",
            "name":"航海王（番外篇）",
            "site":"qq",
            "source_url":"https://ac.qq.com/Comic/ComicInfo/id/531616"
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
            "source_url":"https://ac.qq.com/Comic/ComicInfo/id/623251",
            "status":""
        },
        {
            "comicid":"642093",
            "cover_image_url":"https://manhua.qpic.cn/vertical/0/27_15_21_78309f29cd87c7cc377394e7eff7451a_1558941691349.jpg/420",
            "name":"早安，亿万萌妻",
            "site":"qq",
            "source_url":"https://ac.qq.com/Comic/ComicInfo/id/642093",
            "status":""
        },
        {
            "comicid":"645275",
            "cover_image_url":"https://manhua.qpic.cn/vertical/0/10_16_25_449147333255ff67dc8641cf2973a4d5_1586507129100.jpg/420",
            "name":"这个王妃有点皮",
            "site":"qq",
            "source_url":"https://ac.qq.com/Comic/ComicInfo/id/645275",
            "status":""
        },
        {
            "comicid":"643030",
            "cover_image_url":"https://manhua.qpic.cn/vertical/0/10_19_52_b242deb1edc24b7dcd497cc5aece0c92_1562759532456.jpg/420",
            "name":"本座右手成精了",
            "site":"qq",
            "source_url":"https://ac.qq.com/Comic/ComicInfo/id/643030",
            "status":""
        },
        {
            "comicid":"629187",
            "cover_image_url":"https://manhua.qpic.cn/vertical/0/04_17_13_e5348ec4b88cbc8f5f0e8160e103cca3_1559639601458.jpg/420",
            "name":"帝少专宠霸道妻",
            "site":"qq",
            "source_url":"https://ac.qq.com/Comic/ComicInfo/id/629187",
            "status":""
        },
        {
            "comicid":"644212",
            "cover_image_url":"https://manhua.qpic.cn/vertical/0/24_13_31_539869eedd6282182391d75d1756f364_1569303113539.jpg/420",
            "name":"心动99天：甜蜜暴击",
            "site":"qq",
            "source_url":"https://ac.qq.com/Comic/ComicInfo/id/644212",
            "status":""
        },
        {
            "comicid":"633069",
            "cover_image_url":"https://manhua.qpic.cn/vertical/0/19_15_06_92de9327972ed8359bba0ad02ab2fd89_1524121604062.jpg/420",
            "name":"我被小三掰弯了",
            "site":"qq",
            "source_url":"https://ac.qq.com/Comic/ComicInfo/id/633069",
            "status":""
        },
        {
            "comicid":"549901",
            "cover_image_url":"https://manhua.qpic.cn/vertical/0/22_16_05_c63e849d48ad6e922865601bc56e0bd9_1500710755225.jpg/420",
            "name":"帝少别太猛",
            "site":"qq",
            "source_url":"https://ac.qq.com/Comic/ComicInfo/id/549901",
            "status":""
        },
        {
            "comicid":"647302",
            "cover_image_url":"https://manhua.qpic.cn/vertical/0/28_16_09_40b7c70aef129b11890d6bf7ce2d2140_1585382945490.jpg/420",
            "name":"万渣朝凰之首相大人",
            "site":"qq",
            "source_url":"https://ac.qq.com/Comic/ComicInfo/id/647302",
            "status":""
        },
        {
            "comicid":"645594",
            "cover_image_url":"https://manhua.qpic.cn/vertical/0/02_18_23_388a01ca118c1ffc490e1a1589dd843e_1575282189242.jpg/420",
            "name":"男神爸比从天降",
            "site":"qq",
            "source_url":"https://ac.qq.com/Comic/ComicInfo/id/645594",
            "status":""
        },
        {
            "comicid":"633106",
            "cover_image_url":"https://manhua.qpic.cn/vertical/0/20_15_15_34b5c9f3b44bed1b8fb1ead67f0e720b_1524208508882.jpg/420",
            "name":"囚爱",
            "site":"qq",
            "source_url":"https://ac.qq.com/Comic/ComicInfo/id/633106",
            "status":""
        },
        {
            "comicid":"647360",
            "cover_image_url":"https://manhua.qpic.cn/vertical/0/16_20_52_9aba495b6a16b44dc122e5cdd2d5a3e8_1587041532213.jpg/420",
            "name":"女皇后宫有点乱",
            "site":"qq",
            "source_url":"https://ac.qq.com/Comic/ComicInfo/id/647360",
            "status":""
        }
    ]
}
```
