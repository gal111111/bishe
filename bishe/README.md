# 上海迪士尼舆情全自动分析系统

<p align="center">
  <img src="https://img.shields.io/badge/python-3.13+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/streamlit-1.39+-brightgreen.svg" alt="Streamlit Version">
  <img src="https://img.shields.io/badge/selenium-4.20+-orange.svg" alt="Selenium Version">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License">
</p>

## 📋 项目简介

上海迪士尼舆情全自动分析系统，实现：**关键词输入 → 多平台爬取 → 数据清洗 → AI情感分析 → 可视化展示 → 智能报告一键生成**。

### ✨ 核心特性

- 🚀 **全流程自动化**: 从爬取到报告生成一键完成
- 📱 **多平台支持**: 微博、知乎、贴吧、虎扑、小红书、B站、抖音全覆盖
- 🤖 **混合分析策略**: SnowNLP快速分析 + DeepSeek深度分析（含CoT思维链提示）
- 🔬 **前沿技术集成**: 方面级情感分析、知识图谱、多模态分析、舆情传播、情感演化
- 📊 **可视化驾驶舱**: Streamlit构建的交互式展示界面
- 🧠 **RAG智能问答**: 基于检索增强生成的智能问答系统
- ⚡ **断点续跑**: 支持异常中断后继续执行
- 🐳 **Docker容器化**: 一键部署，开箱即用
- 📈 **消融实验**: 完整的对比实验和性能分析

---

## 🎯 前沿技术集成 ✨

本项目集成了多项NLP和数据挖掘领域的前沿技术：

| 技术 | 模块 | 文件 | 功能描述 |
|------|------|------|---------|
| 方面级情感分析 | 🎯 | `src/analysis/aspect_based_sentiment.py` | 提取（实体，方面，情感）三元组 ✨ 新增 |
| 知识图谱 | 🗺️ | `src/analysis/knowledge_graph.py` | 实体-关系网络构建，支持舆情溯源 |
| 多模态情感分析 | 🎨 | `src/analysis/multimodal_sentiment.py` | 文本+表情+图片综合情感分析 |
| 舆情传播分析 | 📡 | `src/analysis/opinion_propagation.py` | PageRank、影响力节点识别 |
| 情感动态演化 | ⏰ | `src/analysis/sentiment_evolution.py` | 演化阶段检测、新兴话题发现 |
| 消融实验 | 📊 | `src/analysis/ablation_study.py` | 对比不同方法的性能 ✨ 新增 |
| 多LLM协商 | 🤝 | `src/analysis/advanced_sentiment_analysis.py` | 多模型协商提升分析精度 |
| 可解释性分析 | 🔍 | `src/analysis/explainability_module.py` | SHAP值、推理链可视化 |
| 时间序列预测 | 📈 | `src/analysis/timeseries_analysis.py` | Prophet预测、变点检测 |

---

## 📁 项目结构

```
bishe/
├── src/
│   ├── analysis/                  # 分析模块
│   │   ├── sentiment_analysis.py         # 核心情感分析（混合模式+CoT提示）
│   │   ├── aspect_based_sentiment.py     # 方面级情感分析 ✨ 新增
│   │   ├── advanced_sentiment_analysis.py # 高级情感分析（多LLM协商）
│   │   ├── knowledge_graph.py            # 知识图谱构建
│   │   ├── multimodal_sentiment.py       # 多模态情感分析
│   │   ├── opinion_propagation.py        # 舆情传播分析
│   │   ├── sentiment_evolution.py        # 情感动态演化
│   │   ├── ablation_study.py             # 消融实验模块 ✨ 新增
│   │   ├── explainability_module.py      # 可解释性模块
│   │   ├── timeseries_analysis.py        # 时间序列分析
│   │   ├── academic_report.py            # 学术报告生成
│   │   └── alert_system.py               # 预警系统
│   ├── crawlers/                  # 爬虫模块
│   │   └── selenium_spiders/      # Selenium爬虫
│   │       ├── common.py          # 爬虫基类
│   │       ├── weibo_spider.py    # 微博爬虫
│   │       ├── zhihu_spider.py    # 知乎爬虫
│   │       ├── tieba_spider.py    # 贴吧爬虫
│   │       ├── hupu_spider.py     # 虎扑爬虫
│   │       ├── xiaohongshu_selenium_spider.py  # 小红书爬虫 ✨ 新增
│   │       ├── bilibili_selenium_spider.py      # B站爬虫 ✨ 新增
│   │       └── douyin_selenium_spider.py        # 抖音爬虫 ✨ 新增
│   ├── preprocessing/             # 预处理模块
│   │   └── data_cleaning.py       # 数据清洗
│   ├── visualization/             # 可视化模块
│   │   └── charts.py              # 图表生成
│   ├── utils/                     # 工具函数
│   │   ├── config_loader.py       # 配置加载
│   │   └── logger.py              # 日志工具
│   └── config/                    # 配置管理
│       └── settings.py            # 全局配置
├── data/
│   ├── raw/                       # 原始数据
│   ├── cache/                     # 缓存文件
│   ├── viz/                       # 可视化结果
│   └── ablation/                  # 消融实验结果 ✨ 新增
├── docs/                          # 文档目录
│   ├── 毕业论文辅助文档.md       # 毕业论文写作辅助
│   ├── 用户使用手册.md            # 用户使用手册
│   ├── API文档.md                # API文档
│   ├── 参考文献.md               # 参考文献
│   └── Docker部署指南.md         # Docker部署指南 ✨ 新增
├── app.py                         # Streamlit前端应用
├── run_full_analysis.py          # 全流程分析入口
├── Dockerfile                     # Docker镜像配置 ✨ 新增
├── docker-compose.yml             # Docker Compose配置 ✨ 新增
├── .dockerignore                  # Docker忽略文件 ✨ 新增
└── README.md                      # 项目说明文档
```

---

## 🚀 快速开始

### 1. 环境配置

```bash
# 克隆项目
git clone <repository-url>
cd bishe

# 安装依赖
pip install -r requirements.txt

# 配置API密钥
# 编辑 src/config/settings.py 或设置环境变量
export DEEPSEEK_API_KEY="your-api-key-here"
```

### 2. 全流程分析

```bash
# 方式1: 使用全流程脚本（推荐）
python run_full_analysis.py

# 方式2: 使用前端界面
streamlit run app.py --server.port 8502
```

### 3. 访问驾驶舱

打开浏览器访问: http://localhost:8502

---

## 🐳 Docker 一键部署（推荐）

### 使用 Docker Compose

```bash
# 克隆项目
git clone <repository-url>
cd bishe

# 构建并启动（包含Redis缓存）
docker-compose up -d --build

# 访问系统
# 前端界面：http://localhost:8502
# Redis（可选）：localhost:6379

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 单独使用 Docker

```bash
# 构建镜像
docker build -t disney-sentiment-analysis .

# 运行容器
docker run -d \
  --name disney-sentiment-analysis \
  -p 8502:8502 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  disney-sentiment-analysis
```

详细部署说明请参考：[Docker部署指南.md](docs/Docker部署指南.md)

---

## 🔬 前沿技术使用指南

### 1. 方面级情感分析（ABSA）

```python
from src.analysis.aspect_based_sentiment import AspectBasedSentimentAnalyzer

# 初始化分析器
analyzer = AspectBasedSentimentAnalyzer()

# 分析单条评论
result = analyzer.analyze("上海迪士尼的服务态度很好，但排队时间太长了")

print("三元组:", result["triples"])
print("整体情感:", result["overall_sentiment"])
print("整体分数:", result["overall_score"])
```

### 2. 知识图谱构建

```python
from src.analysis.knowledge_graph import KnowledgeGraphBuilder

# 初始化构建器
builder = KnowledgeGraphBuilder()

# 从DataFrame构建图谱
builder.build_from_dataframe(df_analyzed)

# 获取洞察
insights = builder.get_insights()
print("最常提及实体:", insights["top_mentioned_entities"])
print("被批评最多实体:", insights["most_criticized_entities"])

# 保存图谱
builder.save_graph("data/viz/knowledge_graph.json")
```

### 3. 多模态情感分析

```python
from src.analysis.multimodal_sentiment import MultimodalSentimentAnalyzer

# 初始化分析器
analyzer = MultimodalSentimentAnalyzer()

# 分析单条评论
result = analyzer.analyze(
    text="迪士尼真的太好玩了！😊🎉",
    image_description="开心的游客照片"
)

print("最终情感:", result["final_polarity"])
print("CSI指数:", result["csi_score"])
```

### 4. 舆情传播分析

```python
from src.analysis.opinion_propagation import PublicOpinionAnalyzer

# 初始化分析器
analyzer = PublicOpinionAnalyzer()

# 从DataFrame构建网络
analyzer.build_from_dataframe(df)

# 计算PageRank
analyzer.calculate_pagerank()

# 找到影响力节点
top_influencers = analyzer.find_influential_nodes(top_k=10)
print("Top 10 影响力节点:", top_influencers)
```

### 5. 情感动态演化分析

```python
from src.analysis.sentiment_evolution import SentimentEvolutionAnalyzer

# 初始化分析器
analyzer = SentimentEvolutionAnalyzer("data/viz")

# 获取演化洞察
insights = analyzer.get_evolution_insights(df)

print("演化阶段:", insights["evolution_phases"])
print("新兴话题:", insights["emerging_topics"])
```

### 6. 消融实验

```python
from src.analysis.ablation_study import run_full_ablation_study
import pandas as pd

# 准备数据（需要包含真实标签）
df = pd.read_csv("data/analyzed_comments.csv")

# 运行完整消融实验
report_df, chart_path = run_full_ablation_study(df)

# 查看实验结果
print("消融实验结果:")
print(report_df)
```

---

## 📊 混合情感分析模式

系统支持三种情感分析模式：

| 模式 | 速度 | 精度 | 适用场景 |
|------|------|------|---------|
| **SnowNLP** | ⚡⚡⚡⚡⚡ | ⭐⭐⭐ | 大规模数据快速分析 |
| **DeepSeek** | ⚡⚡ | ⭐⭐⭐⭐⭐ | 小规模精确分析 |
| **混合模式 (推荐)** | ⚡⚡⚡⚡ | ⭐⭐⭐⭐ | 平衡速度与精度 |

**混合策略**:
- 默认 10% 长文本使用 DeepSeek 深度分析
- 其余 90% 使用 SnowNLP 快速分析
- 可调节 DeepSeek 分析比例 (5% - 30%)

---

## 🎓 毕业论文写作辅助

本项目包含完整的毕业论文辅助文档：`docs/毕业论文辅助文档.md`

**文档内容**:
- ✅ 项目概述与系统架构
- ✅ 核心技术模块详解
- ✅ 前沿技术集成说明
- ✅ 实验结果与分析
- ✅ 5大创新点总结
- ✅ 论文结构建议（9章大纲）
- ✅ 核心代码示例
- ✅ 参考文献建议

---

## 📈 技术栈

| 类别 | 技术 | 版本 | 用途 |
|------|------|------|------|
| 编程语言 | Python | 3.13+ | 主要开发语言 |
| 爬虫框架 | Selenium | 4.20+ | 多平台数据爬取 |
| 浏览器驱动 | Edge WebDriver | 最新 | 浏览器自动化 |
| 情感分析 | SnowNLP | 0.12.3 | 快速本地分析 |
| 大模型 | DeepSeek API | 最新 | 深度分析 |
| 可视化 | Streamlit | 1.39+ | 交互式驾驶舱 |
| 可视化 | Plotly | 5.24+ | 图表生成 |
| 数据处理 | Pandas | 2.2+ | 数据清洗与分析 |
| 数据处理 | NumPy | 2.2+ | 数值计算 |
| 机器学习 | scikit-learn | 1.5+ | 模型训练与评估 |
| 时间序列 | Prophet | 1.1.5 | 趋势预测 |

---

## 🔧 配置说明

编辑 `src/config/settings.py` 或使用环境变量：

```python
# API配置
DEEPSEEK_API_KEY = "your-api-key"
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

# 爬虫配置
MAX_RETRIES = 3
TIMEOUT = 30
PAGE_LOAD_WAIT = 5

# 分析配置
DEFAULT_SENTIMENT_MODE = "hybrid"  # snownlp / deepseek / hybrid
DEFAULT_DEEPSEEK_RATIO = 0.1       # 5% - 30%
```

---

## 📝 开发计划

- [x] 多平台爬虫（微博、知乎、贴吧、虎扑）
- [x] 数据清洗与预处理
- [x] 混合情感分析引擎
- [x] 多LLM协商框架
- [x] 可解释性分析模块
- [x] 时间序列预测
- [x] Streamlit可视化驾驶舱
- [x] RAG智能问答
- [x] 知识图谱构建 ✨
- [x] 多模态情感分析 ✨
- [x] 舆情传播分析 ✨
- [x] 情感动态演化分析 ✨
- [x] 毕业论文辅助文档 ✨
- [x] 方面级情感分析（ABSA）✨ 新增
- [x] DeepSeek CoT思维链提示 ✨ 新增
- [x] 消融实验模块 ✨ 新增
- [x] 小红书爬虫 ✨ 新增
- [x] B站爬虫 ✨ 新增
- [x] 抖音爬虫 ✨ 新增
- [x] Docker容器化部署 ✨ 新增
- [ ] 知识图谱前端可视化集成
- [ ] 实时流式数据处理

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

---

## 📄 许可证

MIT License

---

## 👥 作者

上海迪士尼舆情分析项目组

---

## 🙏 致谢

感谢所有为本项目做出贡献的开发者！

---

**最后更新**: 2026年2月28日