# 公共设施满意度全自动分析系统 - 运行指南

## 系统功能

✅ **全自动爬虫**：输入关键词 → 自动爬取知乎和微博
✅ **AI分析**：使用DeepSeek大模型进行情感分析
✅ **预警系统**：静态预警、动态预警、组合预警、自适应预警
✅ **时间序列分析**：满意度趋势分析、变化点检测、预测
✅ **可视化**：生成各种图表和报告

## 运行准备

### 1. 安装依赖（如果尚未安装）

```bash
# 进入项目目录
cd e:\bishe\bishe

# 安装基本依赖
pip install -r requirements.txt

# 安装可选依赖（用于时间序列分析）
pip install prophet statsmodels ruptures
```

### 2. 准备Edge驱动

驱动文件已存在于：`e:\bishe\bishe\edgedriver_win64\msedgedriver.exe`

### 3. 配置API密钥

在 `.env` 文件中配置 DeepSeek API 密钥：

```
DEEPSEEK_API_KEY=sk-gxclqeqaklaobomgciagbofmkmeoeciizwqdsmiicsqqlobc
DEEPSEEK_API_URL=https://api.siliconflow.cn/v1/chat/completions
DEEPSEEK_MODEL=deepseek-ai/DeepSeek-V3
```

## 运行步骤

### 方案一：使用完整自动化脚本（推荐）

```bash
# 运行自动化爬虫和分析系统
python crawl_and_analyze.py
```

**运行流程：**

1. **输入关键词**：例如 `广州图书馆`
2. **知乎爬取**：
   - 系统会打开Edge浏览器
   - 您需要扫码登录知乎
   - 输入关键词搜索
   - 选择相关问题
   - 选择要爬取的回答
3. **微博爬取**：
   - 系统会提示您输入微博Cookie
   - 您需要从浏览器复制Cookie
   - 输入包含关键词的微博链接
4. **自动分析**：
   - 数据合并和格式化
   - AI情感分析
   - 预警系统运行
   - 时间序列分析
   - 可视化生成

### 方案二：分步运行

#### 1. 先运行知乎爬虫
```bash
python selenium_spiders\zhihu_selenium_spider.py
```

#### 2. 再运行微博爬虫
```bash
python selenium_spiders\weibo_api_spider.py
```

#### 3. 最后运行分析
```bash
python auto_analyzer.py
```

## 输出结果

分析完成后，结果会保存在以下位置：

### 核心结果文件
- `data/analyzed_comments.csv` - AI分析结果
- `data/ai_research_report.csv` - AI研究报告
- `data/alert_results.csv` - 预警结果
- `data/alert_report.txt` - 预警报告

### 可视化图表
- `data/viz/` - 各种可视化图表
- `data/timeseries/` - 时间序列分析结果

### 前端展示

运行前端展示：

```bash
streamlit run app.py
```

访问地址：http://localhost:8501

## 技术架构

### 核心模块

1. **爬虫模块**：
   - `selenium_spiders/zhihu_selenium_spider.py` - 知乎爬虫
   - `selenium_spiders/weibo_api_spider.py` - 微博爬虫

2. **分析模块**：
   - `analysis/sentiment_analysis.py` - 情感分析
   - `analysis/alert_system.py` - 预警系统
   - `analysis/timeseries_analysis.py` - 时间序列分析
   - `analysis/data_cleaning.py` - 数据清洗

3. **工具模块**：
   - `data_formatter.py` - 数据格式化
   - `auto_analyzer.py` - 自动分析器
   - `crawl_and_analyze.py` - 完整自动化流程

### 算法说明

1. **数据清洗**：
   - 缺失值处理
   - 异常值检测
   - 文本清洗

2. **情感分析**：
   - 规则引擎
   - TextCNN模型
   - DeepSeek大模型

3. **预警系统**：
   - 静态预警：基于阈值
   - 动态预警：Isolation Forest异常检测
   - 组合预警：情感倾向+满意度得分
   - 自适应预警：基于历史统计的自适应阈值

4. **时间序列分析**：
   - 变化点检测：PELT算法
   - 趋势分析：移动平均
   - 预测：Prophet模型

## 常见问题

### 1. Edge浏览器启动失败

**解决方案**：系统已配置了相关参数，一般情况下不会出现此问题。

### 2. 知乎登录失败

**解决方案**：
- 确保网络正常
- 扫码登录时动作要快
- 若Cookie失效，系统会自动提示重新登录

### 3. 微博Cookie获取方法

**获取步骤**：
1. 打开微博网页版
2. 登录账号
3. 按 F12 打开开发者工具
4. 切换到 "网络" 标签
5. 刷新页面
6. 选择任意请求
7. 复制 "Cookie" 字段的完整内容

### 4. API调用失败

**解决方案**：
- 检查 `.env` 文件中的API密钥是否正确
- 确保网络能够访问硅基流动API
- 系统会自动重试失败的API调用

## 运行示例

### 示例1：分析广州图书馆

```bash
python crawl_and_analyze.py
```

输入：`广州图书馆`

**预期输出**：
- 爬取知乎和微博关于广州图书馆的评论
- 生成分析报告
- 运行预警系统
- 生成趋势图和预测

### 示例2：分析国家图书馆

```bash
python crawl_and_analyze.py
```

输入：`国家图书馆`

## 结果查看

### 1. 数据文件

所有分析结果都保存在 `data/` 目录中，您可以使用Excel或Python查看。

### 2. 可视化图表

图表保存在 `data/viz/` 和 `data/timeseries/` 目录中。

### 3. 前端展示

运行 `streamlit run app.py` 后，在浏览器中查看交互式仪表盘。

## 注意事项

⚠️ **爬虫合规**：请遵守各平台的爬虫规则，不要过度爬取
⚠️ **API费用**：使用DeepSeek API会产生费用，请合理使用
⚠️ **网络稳定性**：爬取过程需要稳定的网络连接
⚠️ **浏览器兼容性**：确保您的Edge浏览器是最新版本

---

**祝您使用愉快！** 🎉

如有问题，请查看技术架构文档或联系技术支持。