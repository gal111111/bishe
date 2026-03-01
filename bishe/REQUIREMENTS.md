# 上海迪士尼数据分析系统全流程落地指令（最终版+数据格式规范）
**核心新增约束**：所有爬取/处理/分析数据强制遵循统一格式；迭代优先、可视化展示要求保持不变
**项目根路径**：`e:\bishe\bishe\`

## 一、核心原则（补充数据格式规范原则）
1. **迭代优先**：所有修改基于现有文件，非必要不新建；
2. **可视化强制**：浏览器可见+控制台进度+日志记录；
3. **格式统一**：所有平台数据遵循相同的字段/存储格式，字段类型、编码、命名规则完全统一。

## 二、数据格式规范（全平台强制遵循）
### 2.1 通用基础格式（所有CSV文件）
| 规范项 | 强制要求 | 示例/说明 |
|--------|----------|-----------|
| 编码 | UTF-8（无BOM） | 禁止使用GBK/GB2312，避免中文乱码 |
| 分隔符 | 逗号（,） | 禁止使用制表符/分号，确保Excel/Pandas可直接读取 |
| 行尾符 | \n（LF） | 统一换行格式，兼容Windows/Linux |
| 表头 | 必须包含，字段名英文小写+下划线，禁止中文/空格 | 如：`platform,content,content_clean` |
| 空值处理 | 空值填充为`NULL`，禁止空字符串/空格 | 缺失的点赞数填`NULL`，而非空/0 |
| 日期格式 | 统一为`YYYY-MM-DD HH:MM:SS` | 如：`2026-02-23 14:30:25` |
| 数值格式 | 整数/浮点数，禁止字符串格式 | 点赞数填`128`，而非`"128"`/`"128个"` |

### 2.2 爬取原始数据格式（单平台CSV）
#### 字段清单（所有平台必须包含以下字段，扩展字段放在末尾）
| 字段名 | 字段类型 | 非空要求 | 说明 | 示例 |
|--------|----------|----------|------|------|
| `platform` | 字符串 | 非空 | 平台标识（固定值） | `weibo`/`zhihu`/`tieba`/`hupu` |
| `post_id` | 字符串 | 非空 | 帖子唯一ID（平台内去重） | 微博：`MWeibo123456`；知乎：`Zhihu789012` |
| `content` | 字符串 | 非空 | 原始文本内容（未清洗） | 包含表情、@、#话题、换行等原始内容 |
| `publish_time` | 字符串 | 允许空 | 帖子发布时间（无则填NULL） | `2026-02-22 09:35:00` |
| `like_count` | 整数 | 允许空 | 点赞数（无则填NULL） | `128`/`NULL` |
| `comment_count` | 整数 | 允许空 | 评论数（无则填NULL） | `36`/`NULL` |
| `crawl_time` | 字符串 | 非空 | 爬取时间（统一格式） | `2026-02-23 15:00:10` |
| `url` | 字符串 | 非空 | 帖子原始URL | `https://s.weibo.com/weibo?q=上海迪士尼&xxx` |

#### 各平台扩展字段（仅补充，不修改基础字段）
| 平台 | 扩展字段 | 类型 | 说明 |
|------|----------|------|------|
| 微博 | `comment_content` | 字符串 | 单条评论内容（1行1条评论，对应1个post_id） |
| 微博 | `comment_publish_time` | 字符串 | 评论发布时间 |
| 知乎 | `author` | 字符串 | 回答作者昵称 |
| 贴吧 | `reply_content` | 字符串 | 帖子回复内容 |
| 虎扑 | `forward_count` | 整数 | 转发数 |

#### 单平台原始数据文件命名规范
```
# 格式：{平台名}_raw_关键词_爬取日期.csv
示例：
weibo_raw_上海迪士尼_20260223.csv
zhihu_raw_上海迪士尼_20260223.csv
tieba_raw_上海迪士尼_20260223.csv
hupu_raw_上海迪士尼_20260223.csv
# 保存路径：e:\bishe\bishe\data\raw\（新增raw子目录，仅这1个新目录）
```

### 2.3 清洗后数据格式（merged/cleaned文件）
#### 合并后原始数据（merged_all_platform.csv）
| 字段名 | 字段类型 | 来源 | 说明 |
|--------|----------|------|------|
| `id` | 整数 | 自增 | 全局唯一ID（1,2,3...） |
| `platform` | 字符串 | 单平台文件 | 统一为`weibo`/`zhihu`/`tieba`/`hupu` |
| `post_id` | 字符串 | 单平台文件 | 保留原平台post_id |
| `content` | 字符串 | 单平台文件 | 原始内容 |
| `publish_time` | 字符串 | 单平台文件 | 统一格式，空值填NULL |
| `like_count` | 整数 | 单平台文件 | 空值填NULL |
| `comment_count` | 整数 | 单平台文件 | 空值填NULL |
| `crawl_time` | 字符串 | 单平台文件 | 统一格式 |
| `url` | 字符串 | 单平台文件 | 原始URL |
| `extend_fields` | JSON字符串 | 单平台扩展字段 | 存储各平台扩展字段（如微博评论、知乎作者） |

#### 清洗后数据（cleaned_all_data.csv）
在合并后原始数据基础上新增以下字段：
| 新增字段 | 字段类型 | 说明 |
|----------|----------|------|
| `content_clean` | 字符串 | 清洗后文本（去特殊符号/换行/@/话题，仅保留纯文本） |
| `content_length` | 整数 | 清洗后文本长度（字符数） |
| `is_valid` | 布尔值 | 是否为有效数据（length≥10为True，否则False） |

### 2.4 分析结果数据格式
#### 情感分析结果（analyzed_comments.csv）
| 字段名 | 字段类型 | 说明 |
|--------|----------|------|
| `id` | 整数 | 关联cleaned_all_data的id |
| `platform` | 字符串 | 平台标识 |
| `content_clean` | 字符串 | 清洗后文本 |
| `sentiment_score` | 浮点数 | 情感得分（0-1） |
| `sentiment_label` | 字符串 | 情感标签（positive/neutral/negative） |
| `sentiment_source` | 字符串 | 分析来源（api/本地snownlp） |
| `analyze_time` | 字符串 | 分析时间（YYYY-MM-DD HH:MM:SS） |

#### 分析汇总结果（analysis_result.json）
```json
{
  "sentiment_dist": [
    {"label": "positive", "count": 整数, "ratio": 浮点数},
    {"label": "neutral", "count": 整数, "ratio": 浮点数},
    {"label": "negative", "count": 整数, "ratio": 浮点数}
  ],
  "keyword_top20": [
    {"word": "字符串", "count": 整数, "ratio": 浮点数}
  ],
  "platform_heat": [
    {"platform": "字符串", "like_total": 整数, "comment_total": 整数, "post_total": 整数}
  ],
  "generate_time": "YYYY-MM-DD HH:MM:SS"
}
```

## 三、环境前置配置（补充数据格式相关配置）
在`src/crawlers/selenium_spiders/common.py`中新增**数据格式工具函数**（仅新增，不修改原有逻辑）：
```python
# common.py - 新增数据格式规范函数
import csv
import json
import time
from datetime import datetime

def init_csv_header(file_path, base_fields):
    """初始化CSV文件表头（确保格式规范）"""
    with open(file_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=base_fields)
        writer.writeheader()

def format_time_str(time_str):
    """统一时间格式为YYYY-MM-DD HH:MM:SS，失败返回NULL"""
    if not time_str or time_str == "NULL":
        return "NULL"
    try:
        # 适配各平台不同时间格式
        if "分钟前" in time_str or "小时前" in time_str:
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # 解析常见时间格式
        dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return "NULL"

def format_numeric_value(value):
    """统一数值格式，非数字返回NULL"""
    if not value or value == "NULL":
        return "NULL"
    try:
        return int(value)
    except:
        return "NULL"

def save_to_csv规范(data, file_path, fields):
    """按规范保存数据到CSV"""
    with open(file_path, 'a', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        # 格式化每条数据
        for row in data:
            # 时间字段格式化
            if "publish_time" in row:
                row["publish_time"] = format_time_str(row["publish_time"])
            if "crawl_time" not in row:
                row["crawl_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # 数值字段格式化
            for num_field in ["like_count", "comment_count", "forward_count"]:
                if num_field in row:
                    row[num_field] = format_numeric_value(row[num_field])
            # 空值替换为NULL
            for k, v in row.items():
                if v is None or v == "":
                    row[k] = "NULL"
            writer.writerow(row)
    # 可视化打印
    print(f"\033[34m[格式规范]\033[0m 已保存{len(data)}条数据到{file_path}，格式符合规范")
```

## 四、核心任务迭代修改（补充数据格式约束）
### 4.1 微博爬虫优化（weibo_spider.py）
1. **新增格式约束**：
   - 爬取数据前，调用`init_csv_header`初始化表头（基础字段+微博扩展字段）；
   - 保存数据时必须使用`save_to_csv规范`函数，确保时间/数值格式统一；
   - post_id生成规则：`weibo_` + 帖子URL中的数字ID（确保唯一）；
2. **可视化补充**：控制台打印`[格式规范] 正在校验微博第{idx}条数据格式...`，格式错误时暂停修复。

### 4.2 多平台爬虫（知乎/贴吧/虎扑）
1. **统一格式适配**：
   - 所有平台爬虫必须调用`common.py`中的格式工具函数；
   - post_id生成规则：`平台名_` + 平台内唯一标识（如知乎回答ID、贴吧帖子ID）；
   - 扩展字段统一存入`extend_fields`（JSON字符串格式）；
2. **命名规范**：文件保存到`data/raw/`，严格遵循`{平台名}_raw_上海迪士尼_日期.csv`命名规则。

### 4.3 数据处理与分析（auto_analyzer.py）
1. **清洗阶段格式约束**：
   - 合并多平台数据时，强制校验字段完整性（缺失基础字段的行直接过滤）；
   - `content_clean`字段必须去除所有特殊符号（@、#、表情、换行、空格）；
   - `is_valid`字段严格按长度≥10判定，无效数据单独保存到`data/cleaned_invalid_data.csv`；
2. **分析阶段格式约束**：
   - 情感得分保留4位小数（如0.7892）；
   - 情感标签统一为英文（positive/neutral/negative），禁止中文；
   - `analysis_result.json`必须包含`generate_time`字段，格式统一。

## 五、全流程验收标准（补充格式验收）
1. **格式合规性**：
   - 所有CSV文件编码为UTF-8，表头命名符合规范，无中文/空格；
   - 时间字段统一为`YYYY-MM-DD HH:MM:SS`，数值字段无字符串格式；
   - JSON文件缩进为2，编码UTF-8，字段名英文小写；
2. **数据完整性**：
   - 基础字段无缺失，扩展字段按平台规范补充；
   - 空值统一为`NULL`，无空字符串/空格；
3. **文件命名**：
   - 单平台原始数据按`{平台名}_raw_关键词_日期.csv`命名，保存到`data/raw/`；
   - 合并/清洗/分析文件命名与路径符合规范。

## 六、其他要求（保持不变）
1. 迭代优先：所有格式规范逻辑基于现有文件新增，非必要不新建文件；
2. 可视化展示：爬取/处理过程中实时打印格式校验进度，格式错误时暂停并提示；
3. 日志记录：新增`logs/format_check.log`，记录格式校验结果、错误原因、修复方式。

# 上海迪士尼数据分析系统全流程落地指令（最终版）
**核心新增约束**：所有修改基于现有文件/流程迭代，非必要不新建文件；爬取流程全程可视化展示（浏览器可见+控制台实时进度+日志）
**项目根路径**：`e:\bishe\bishe\`

## 一、核心原则（优先遵循）
1. **迭代优先**：所有功能修改基于现有文件（`weibo_spider.py/common.py/auto_analyzer.py`），仅在现有文件无法兼容时，新建独立py文件并**集成到主流程**（标注集成方式）；
2. **可视化强制要求**：
   - 浏览器：全程可见模式运行，禁止无头模式；
   - 控制台：实时打印爬取进度（如`[微博-第3条帖子] 已爬取18条评论 | 总进度：3/50`）；
   - 日志：每步操作记录到`e:\bishe\bishe\logs\crawl_progress.log`（含时间、平台、操作、结果）。

## 二、环境前置配置（基于现有环境迭代）
### 2.1 驱动配置（修改现有爬虫的驱动初始化逻辑）
找到`src/crawlers/selenium_spiders/common.py`中`__init__`方法，修改驱动配置（**仅新增/修改以下代码**）：
```python
# 原代码中添加Edge驱动路径+可视化配置
from selenium.webdriver.edge.service import Service

# 1. 硬编码驱动路径（适配项目目录）
self.driver_service = Service(executable_path="E:\bishe\bishe\edgedriver_win64\msedgedriver.exe")
# 2. 保留现有options，新增可视化/反爬配置
self.edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
self.edge_options.add_argument("--disable-blink-features=AutomationControlled")
self.edge_options.add_argument("--start-maximized")  # 窗口最大化，便于查看爬取过程
# 3. 初始化驱动（替换原有driver初始化）
self.driver = webdriver.Edge(service=self.driver_service, options=self.edge_options)
```

### 2.2 依赖安装（基于现有虚拟环境）
激活`e:\bishe\bishe\.venv`，执行以下命令（仅补充缺失依赖，不重复安装）：
```bash
# 仅安装未安装的包
pip install loguru  # 用于可视化日志
pip install statsmodels prophet tensorflow  # 补全分析依赖
pip install jieba snownlp  # 补全文本分析依赖
```

## 三、核心任务1：微博爬虫优化（基于weibo_spider.py迭代）
### 3.1 迭代修改点（仅在原文件中新增/修改，不新建）
| 原文件位置 | 修改内容 | 可视化要求 |
|------------|----------|------------|
| `weibo_spider.py` - `crawl`方法 | 1. 新增`enter_post_detail`函数（点击帖子详情页）<br>2. 新增`crawl_comments`函数（展开+爬取评论）<br>3. 保留原有搜索逻辑，仅扩展详情页/评论爬取 | 1. 控制台打印：`[微博] 进入帖子详情页：{帖子标题}`<br>2. 控制台打印：`[微博-评论] 已加载{已加载数}/{总数}条评论` |
| `weibo_spider.py` - 数据保存 | 1. 扩展原有保存逻辑，新增评论字段<br>2. 保存路径仍为`data/weibo_comments_上海迪士尼.csv`，新增列：评论内容、评论时间 | 控制台打印：`[微博-保存] 第{idx}条帖子数据已保存，含{len(comments)}条评论` |
| `weibo_spider.py` - 异常处理 | 1. 新增断点记录（保存已爬取帖子ID到`data/crawl_breakpoint.json`）<br>2. 定位失败时暂停，打印：`[暂停修复] 元素定位失败：{选择器}，修复后按任意键继续` | 日志记录：`[异常] {时间} - {失败原因} - 断点位置：第{idx}条帖子` |

### 3.2 核心迭代代码片段（插入到weibo_spider.py中）
```python
# 新增：进入帖子详情页（集成到原有爬取逻辑）
def enter_post_detail(self, post_elem, post_idx):
    try:
        # 定位详情链接（适配微博DOM）
        detail_link = post_elem.find_element(By.CSS_SELECTOR, '.card-wrap .content a[href*="weibo.com"]')
        print(f"[微博-第{post_idx+1}条帖子] 正在进入详情页...")
        detail_link.click()
        time.sleep(2)
        # 可视化：控制台高亮提示
        print(f"\033[32m[成功]\033[0m 微博第{post_idx+1}条帖子详情页已打开")
        return True
    except Exception as e:
        print(f"\033[31m[暂停修复]\033[0m 第{post_idx+1}条帖子详情页定位失败：{e}")
        input("修复后按任意键继续...")  # 暂停流程
        return False

# 新增：爬取评论（集成到详情页逻辑后）
def crawl_comments(self, post_idx):
    comments = []
    # 1. 加载更多评论（循环点击）
    while True:
        try:
            load_more_btn = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.more-comment-btn')))
            load_more_btn.click()
            time.sleep(1)
            current_count = len(self.driver.find_elements(By.CSS_SELECTOR, '.comment-item'))
            print(f"[微博-第{post_idx+1}条帖子] 评论加载中：{current_count}条")
        except:
            break
    # 2. 提取评论
    comment_elems = self.driver.find_elements(By.CSS_SELECTOR, '.comment-item .WB_text')
    for elem in comment_elems:
        comments.append(elem.text.strip())
    print(f"\033[32m[成功]\033[0m 微博第{post_idx+1}条帖子爬取到{len(comments)}条评论")
    return comments
```

## 四、核心任务2：多平台爬虫（基于common.py迭代，非必要不新建）
### 4.1 迭代方案（优先复用common.py基类）
1. **知乎/贴吧/虎扑爬虫**：
   - 基于`common.py`的通用爬虫基类，在`src/crawlers/selenium_spiders/`下**复用原有空白文件**（`zhihu_selenium_spider.py/tieba_selenium_spider.py/hupu_selenium_spider.py`），不新建文件；
   - 每个平台爬虫继承`common.py`中的`BaseSeleniumSpider`类，仅重写`crawl`方法（爬取逻辑）；
   - 可视化要求：控制台打印`[知乎/贴吧/虎扑] 已爬取{已爬数}/{目标数}条，当前内容：{内容预览}`。

2. **集成到主流程**：
   - 修改`auto_analyzer.py`，在原有微博爬虫执行后，新增调用知乎/贴吧/虎扑爬虫的逻辑（**仅新增调用代码，不修改原有分析逻辑**）：
   ```python
   # auto_analyzer.py - 数据爬取阶段新增
   from src.crawlers.selenium_spiders.zhihu_selenium_spider import ZhihuSpider
   from src.crawlers.selenium_spiders.tieba_selenium_spider import TiebaSpider
   from src.crawlers.selenium_spiders.hupu_selenium_spider import HupuSpider

   # 原有微博爬虫执行逻辑保留
   # 新增多平台爬虫调用
   zhihu_spider = ZhihuSpider()
   zhihu_spider.crawl(keyword="上海迪士尼", target_count=100)
   tieba_spider = TiebaSpider()
   tieba_spider.crawl(keyword="上海迪士尼", target_count=100)
   hupu_spider = HupuSpider()
   hupu_spider.crawl(keyword="上海迪士尼", target_count=100)
   ```

## 五、核心任务3：数据处理与分析（基于auto_analyzer.py迭代）
### 5.1 迭代修改点（仅扩展原有逻辑，不新建）
1. **数据清洗**：在原有清洗逻辑中，新增多平台数据合并（读取知乎/贴吧/虎扑CSV，合并到`上海迪士尼_merged_data.csv`）；
2. **情感分析**：
   - 保留原有DeepSeek API调用逻辑，新增硅基流动API配置（替换API Key）：
     ```python
     # auto_analyzer.py - 情感分析函数中修改
     API_KEY = "sk-gxclqeqaklaobomgciagbofmkmeoeciizwqdsmiicsqqlobc"
     ```
   - 新增API失败降级逻辑（调用失败时自动用snownlp），控制台打印：`[分析] API调用失败，降级为本地分析`；
3. **可视化要求**：控制台打印`[分析] 已完成{平台}数据情感分析，正面{正条数}条/中性{中条数}条/负面{负条数}条`。

## 六、核心任务4：前端展示（基于现有文件集成，不新建）
1. **后端接口**：在`auto_analyzer.py`末尾新增Flask接口逻辑（**不新建app.py**），保留原有分析逻辑：
   ```python
   # auto_analyzer.py - 末尾新增
   from flask import Flask, jsonify
   app = Flask(__name__)
   # 加载分析结果（复用原有分析结果变量）
   @app.route("/api/sentiment")
   def get_sentiment():
       return jsonify(sentiment_dist)
   # 其他接口同理
   if __name__ == "__main__":
       # 原有全流程分析逻辑保留
       run_full_analysis()
       # 启动Flask服务
       app.run(debug=True, port=5000)
   ```
2. **前端页面**：将`index.html`保存到`static/`目录（项目根目录新建static文件夹，仅这1个新文件夹），页面中API地址指向`http://127.0.0.1:5000/api/xxx`；
3. **可视化要求**：启动Flask时控制台打印`[前端] 服务已启动：http://127.0.0.1:5000/static/index.html`。

## 七、全流程运行规则（迭代原有执行逻辑）
1. **执行入口**：仍使用`auto_analyzer.py`作为主入口（**不新建执行脚本**），执行顺序：
   环境检查 → 微博爬虫 → 多平台爬虫 → 数据清洗 → 情感分析 → 前端服务启动；
2. **暂停修复规则**：
   - 爬虫阶段：定位失败/浏览器断开时，控制台打印暂停提示，按任意键继续（修复后无需重启全流程）；
   - 分析阶段：API调用失败时，自动降级并记录，不暂停流程；
3. **可视化全程覆盖**：
   - 每阶段开始/结束打印：`[阶段-{序号}] {阶段名} 开始/结束，耗时{时长}`；
   - 关键操作（如爬取/保存/分析）打印彩色提示（成功绿色、异常红色、进度蓝色）；
   - 所有操作记录到`logs/crawl_progress.log`，包含时间戳、操作人、操作内容、结果。

## 八、验收标准（新增可视化维度）
1. **迭代要求**：除`static/index.html`和`logs/`目录外，无其他新建文件，所有修改基于原有文件；
2. **可视化要求**：
   - 浏览器全程可见，爬取过程可直观看到页面点击/滚动/评论加载；
   - 控制台实时打印进度，无静默运行；
   - 日志文件完整记录每步操作，可追溯问题；
3. **数据要求**：微博≥200条（含评论），知乎/贴吧/虎扑各≥100条，总数据量≥500条；
4. **流程要求**：单环节失败可暂停修复，修复后从断点继续，无需重启全流程。

## 九、后续修改规则
1. 所有新要求均在现有文件/逻辑基础上迭代，仅当修改量过大（如重构核心逻辑）时，新建py文件并在`auto_analyzer.py`中导入集成；
2. 每次修改需在文件中添加注释：`# 2026-02-23 新增：{修改内容} - {修改原因}`；
3. 可视化要求始终优先，任何修改不得隐藏爬取过程（禁止无头模式、静默运行）。