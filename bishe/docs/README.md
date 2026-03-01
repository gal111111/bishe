# 公共设施满意度分析系统

## 📋 项目概述

**项目主题**：基于多源数据的公共设施满意度分析与预警系统

**核心目标**：
1. 从知乎、微博等平台爬取公共设施相关的用户评论
2. 对评论进行情感分析和满意度评分
3. 建立公共设施满意度预警机制
4. 提供多维度的分析结果和可视化展示

## 🏗️ 技术栈

- **爬虫技术**：Selenium (知乎)、API爬虫 (微博)
- **数据处理**：Python、Pandas
- **情感分析**：DeepSeek-V3大模型
- **时序分析**：ARIMA、Prophet、LSTM
- **预警系统**：静态阈值、动态异常检测、组合预警
- **可视化**：Matplotlib、Plotly、Streamlit
- **AI优化**：DeepSeek-V3搜索关键词优化

## 🚀 快速开始

### 环境要求

- Python 3.7+
- 依赖包：
  ```bash
  pip install -r requirements.txt
  ```

### 运行系统

1. **全自动爬取和分析**
   ```bash
   python test_auto_crawl.py 设施名称
   ```
   例如：
   ```bash
   python test_auto_crawl.py 广州图书馆
   ```

2. **运行前端展示**
   ```bash
   python -m streamlit run app.py
   ```
   访问：http://localhost:8501

## 📁 项目结构

```
bishe/
├── auto_analyzer.py              # 全自动分析流程
├── app.py                         # Streamlit前端
├── main.py                        # 主入口
├── test_auto_crawl.py             # 测试自动爬取
├── ai_search_optimizer.py         # AI搜索优化
├── requirements.txt               # 依赖包
├── TECHNICAL_ARCHITECTURE.md      # 技术架构文档
│
├── analysis/
│   ├── sentiment_analysis.py      # 情感分析（DeepSeek + CSI）
│   ├── data_cleaning.py           # 数据清洗模块
│   ├── alert_system.py            # 预警系统
│   ├── timeseries_analysis.py     # 时序分析（ARIMA/Prophet/LSTM）
│   ├── topic_discovery.py         # 主题发现（LDA/BERTopic）
│   └── rag_support.py             # RAG增强检索
│
├── selenium_spiders/
│   ├── zhihu_selenium_spider.py   # 知乎爬虫（Selenium）
│   └── weibo_api_spider.py        # 微博爬虫（API）
│
├── visualization/
│   └── dashboard.py               # 可视化仪表板
│
├── utils/
│   ├── deepseek_client.py         # DeepSeek API客户端
│   └── quick_analysis.py          # 快速分析工具
│
└── data/                          # 数据目录
    ├── large_raw_data.csv         # 原始数据
    ├── analyzed_comments.csv      # 分析结果
    ├── ai_research_report.csv     # AI研究报告
    └── viz/                       # 可视化图表
```

## 🎯 核心功能

### 1. AI优化搜索关键词

系统使用DeepSeek-V3大模型自动优化搜索关键词，生成更相关的搜索词，提高爬取效率和数据质量。

### 2. 多平台数据爬取

- **知乎**：使用Selenium爬取回答和评论
- **微博**：使用API爬取帖子和评论
- **贴吧/虎扑**：使用备用爬虫

### 3. 智能数据预处理

- 数据清洗：缺失值处理、异常值检测
- 文本清洗：特殊符号过滤、停用词删除、分词
- 非评论元素过滤：使用AI过滤系统生成的操作按钮、时间戳等

### 4. 情感分析与满意度评分

- **DeepSeek大模型**：情感极性分析、情绪细分类
- **CSI满意度模型**：综合情感得分、紧急度、情感修饰因子
- **方面级情感分析**：识别具体评价方面

### 5. 预警系统

- **静态预警**：基于固定阈值的预警
- **动态预警**：基于Isolation Forest的异常检测
- **组合预警**：情感倾向+满意度得分双重触发
- **自适应预警**：基于历史统计的动态阈值

### 6. 时序分析与预测

- **ARIMA**：短期趋势预测
- **Prophet**：含节假日效应预测
- **LSTM**：长时序预测
- **变点检测**：识别满意度突变点

### 7. 可视化展示

- **静态图表**：满意度趋势图、情感分布饼图
- **交互图表**：可缩放的时间序列图、热力图
- **Streamlit前端**：实时可视化、预警推送

## 📊 分析维度

1. **时间维度**：日/周/月/季度满意度趋势
2. **空间维度**：不同地区、设施类型对比
3. **情感维度**：积极/中性/消极分布、情绪细分类
4. **主题维度**：LDA/BERTopic主题建模
5. **预警维度**：静态/动态/组合预警

## 🛠️ 技术特点

- **AI驱动**：使用DeepSeek-V3大模型进行情感分析和搜索优化
- **并行处理**：使用ThreadPoolExecutor提高爬取速度
- **智能过滤**：严格过滤非评论元素，确保数据质量
- **全国范围**：默认使用全国范围进行爬取，无需指定地区
- **真实数据**：只爬取真实数据，不使用模拟数据
- **多源融合**：融合知乎、微博等多平台数据

## 📝 使用说明

### 1. 全自动爬取和分析

```bash
# 语法
python test_auto_crawl.py 设施名称

# 示例：分析广州图书馆
python test_auto_crawl.py 广州图书馆

# 示例：分析国家博物馆
python test_auto_crawl.py 国家博物馆
```

### 2. 查看分析结果

分析完成后，结果会保存在 `data/` 目录：
- `analyzed_comments.csv`：情感分析结果
- `ai_research_report.csv`：AI研究报告
- `alert_results.csv`：预警结果
- `timeseries/`：时序分析结果和图表
- `viz/`：可视化图表

### 3. 前端展示

```bash
python -m streamlit run app.py
```

在前端页面，您可以：
- 上传自定义数据
- 调整分析参数
- 查看实时可视化
- 接收预警通知

## 🔍 技术架构

详细技术架构请参考：[TECHNICAL_ARCHITECTURE.md](TECHNICAL_ARCHITECTURE.md)

## 📚 参考资料

- **情感分析**：BERT、Sentence-BERT
- **时序预测**：ARIMA、Prophet、LSTM
- **异常检测**：Isolation Forest、IQR、Z-score
- **主题建模**：LDA、BERTopic
- **预警系统**：各类公共设施满意度预警相关论文

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

本项目采用MIT许可证。