# 新增平台隔离说明

## 📌 重要说明

**原有四个平台（微博、知乎、贴吧、虎扑）完全不受影响，新增平台已完全隔离！**

## 📁 目录结构

```
bishe/
├── src/crawlers/
│   ├── selenium_spiders/          # 原有的爬虫（微博、知乎、贴吧、虎扑）
│   │   ├── common.py
│   │   ├── zhihu_selenium_spider.py
│   │   ├── tieba_selenium_spider.py
│   │   └── hupu_selenium_spider.py
│   ├── weibo_spider.py            # 微博爬虫
│   └── new_platforms/             # 🆕 新增平台（完全隔离）
│       ├── README.md
│       ├── xiaohongshu_content_spider.py
│       ├── bilibili_content_spider.py
│       └── douyin_content_spider.py
├── data/cookies/                   # Cookie文件（新增平台使用）
│   ├── xiaohongshu_cookies.pkl
│   ├── bilibili_cookies.pkl
│   └── douyin_cookies.pkl
├── run_full_analysis.py            # 主流程（仅用原有四个平台）
├── run_all_crawlers.py              # 运行原有四个平台
├── run_new_crawlers.py             # 🆕 运行新增平台（评论版）
├── run_content_crawlers.py          # 🆕 运行新增平台（内容版）
└── test_content_crawlers.py         # 🆕 测试新增平台
```

## ✅ 原有平台不受影响

### 主流程入口
- `run_full_analysis.py` - 只使用原有四个平台（weibo, zhihu, tieba, hupu）
- `run_all_crawlers.py` - 只运行原有四个平台的爬虫

### 原有的四个平台
1. **微博** - `src/crawlers/weibo_spider.py`
2. **知乎** - `src/crawlers/selenium_spiders/zhihu_selenium_spider.py`
3. **贴吧** - `src/crawlers/selenium_spiders/tieba_selenium_spider.py`
4. **虎扑** - `src/crawlers/selenium_spiders/hupu_selenium_spider.py`

## 🆕 新增平台（完全隔离）

### 新增的三个平台
1. **小红书** - `src/crawlers/new_platforms/xiaohongshu_content_spider.py`
2. **B站** - `src/crawlers/new_platforms/bilibili_content_spider.py`
3. **抖音** - `src/crawlers/new_platforms/douyin_content_spider.py`

### 新增平台的运行脚本（独立使用）
- `run_new_crawlers.py` - 运行新增平台的评论版爬虫
- `run_content_crawlers.py` - 运行新增平台的内容版爬虫
- `test_content_crawlers.py` - 测试新增平台

### Cookie管理
- `save_cookies.py` - 保存各平台Cookie
- `save_bilibili_cookies.py` - 单独保存B站Cookie
- `save_douyin_cookies.py` - 单独保存抖音Cookie（长时间等待版）
- `login_and_crawl_xiaohongshu.py` - 一站式登录小红书并爬取
- `save_all_cookies.py` - 批量保存B站和抖音Cookie

## 📊 使用方式

### 使用原有四个平台（推荐）
```bash
# 运行原有四个平台爬虫
python run_all_crawlers.py

# 运行全流程分析（仅用原有四个平台）
python run_full_analysis.py
```

### 使用新增平台（可选）
```bash
# 保存Cookie（首次使用）
python save_cookies.py

# 运行新增平台内容版爬虫
python run_content_crawlers.py

# 测试新增平台
python test_content_crawlers.py
```

## 🔒 隔离保证

1. **原有代码未修改** - 原有的四个平台爬虫代码完全未动
2. **主流程不变** - `run_full_analysis.py` 只加载原有四个平台数据
3. **目录分离** - 新增平台代码单独放在 `new_platforms/` 目录
4. **运行脚本分离** - 新增平台有独立的运行脚本
5. **数据分离** - 新增平台数据文件名有明确标识（xiaohongshu_, bilibili_, douyin_）

## ✅ 验证

运行原有全流程分析，确认不受影响：
```bash
python run_full_analysis.py
```
