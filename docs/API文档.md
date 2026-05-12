# 上海迪士尼舆情全自动分析系统 - API文档

## 📚 目录

1. [情感分析API](#1-情感分析api)
2. [知识图谱API](#2-知识图谱api)
3. [多模态分析API](#3-多模态分析api)
4. [舆情传播API](#4-舆情传播api)
5. [情感演化API](#5-情感演化api)
6. [工具函数API](#6-工具函数api)

---

## 1. 情感分析API

### 1.1 analyze_sentiment

**功能**: 分析单条文本的情感

**位置**: `src.analysis.sentiment_analysis`

**参数**:

| 参数名 | 类型 | 必需 | 默认值 | 描述 |
|--------|------|------|--------|------|
| text | str | 是 | - | 待分析的文本 |
| preferred | str | 否 | "snownlp" | 分析方式: "snownlp", "deepseek", "hybrid" |

**返回值**:

```python
{
    "polarity": str,           # 情感极性: "积极", "中性", "消极"
    "polarity_label": str,     # 同polarity
    "csi_score": int,          # CSI满意度指数 (0-100)
    "specific_emotion": str,   # 具体情绪
    "intensity": str,          # 情感强度 (1-5)
    "urgency": str,            # 紧急度 (1-10)
    "need_improvement": str,   # 是否需要改进: "是", "否"
    "reason": str,             # 分析原因/推理
    "analysis_method": str     # 分析方法: "snownlp", "deepseek"
}
```

**示例**:

```python
from src.analysis.sentiment_analysis import analyze_sentiment

result = analyze_sentiment("迪士尼真的太好玩了！", preferred="snownlp")
print(result["polarity"])  # 输出: 积极
print(result["csi_score"]) # 输出: 85
```

---

### 1.2 analyze_dataframe

**功能**: 批量分析DataFrame中的文本

**位置**: `src.analysis.sentiment_analysis`

**参数**:

| 参数名 | 类型 | 必需 | 默认值 | 描述 |
|--------|------|------|--------|------|
| df | DataFrame | 是 | - | 包含评论数据的DataFrame |
| content_col | str | 否 | "content" | 内容列名 |
| preferred | str | 否 | "hybrid" | 分析方式 |
| deepseek_ratio | float | 否 | 0.1 | DeepSeek分析比例 (0.05-0.3) |

**返回值**: DataFrame（包含新增的分析结果列）

**示例**:

```python
from src.analysis.sentiment_analysis import analyze_dataframe
import pandas as pd

df = pd.DataFrame({
    "content": ["迪士尼很好玩", "排队太长了"],
    "platform": ["微博", "微博"]
})

result_df = analyze_dataframe(df, preferred="hybrid", deepseek_ratio=0.1)
print(result_df[["content", "polarity_label", "csi_score"]])
```

---

### 1.3 call_deepseek_api

**功能**: 调用DeepSeek API进行分析

**位置**: `src.analysis.sentiment_analysis`

**参数**:

| 参数名 | 类型 | 必需 | 默认值 | 描述 |
|--------|------|------|--------|------|
| messages | list | 是 | - | 消息列表 |

**返回值**: dict

**示例**:

```python
from src.analysis.sentiment_analysis import call_deepseek_api

messages = [
    {"role": "system", "content": "你是情感分析专家"},
    {"role": "user", "content": "分析这句话的情感：迪士尼很好玩"}
]

result = call_deepseek_api(messages)
print(result["content"])
```

---

## 2. 知识图谱API

### 2.1 KnowledgeGraphBuilder

**功能**: 知识图谱构建器

**位置**: `src.analysis.knowledge_graph`

**类方法**:

#### __init__()

初始化知识图谱构建器

#### add_comment(text, comment_id)

添加单条评论到图谱

**参数**:
- `text` (str): 评论文本
- `comment_id` (str, optional): 评论ID

#### build_from_dataframe(df, content_col, id_col)

从DataFrame构建图谱

**参数**:
- `df` (DataFrame): 数据DataFrame
- `content_col` (str): 内容列名，默认"content"
- `id_col` (str): ID列名

#### get_graph_data()

获取图谱数据（用于可视化）

**返回值**:
```python
{
    "nodes": [...],  # 节点列表
    "edges": [...],  # 边列表
    "stats": {...}   # 统计信息
}
```

#### get_insights()

获取图谱洞察

**返回值**:
```python
{
    "top_mentioned_entities": [...],    # 最常提及实体
    "most_criticized_entities": [...],  # 被批评最多实体
    "most_praised_entities": [...],     # 被赞扬最多实体
    "entity_distribution": {...}        # 实体分布
}
```

#### save_graph(output_path)

保存图谱到JSON文件

**示例**:

```python
from src.analysis.knowledge_graph import KnowledgeGraphBuilder

builder = KnowledgeGraphBuilder()
builder.build_from_dataframe(df)

insights = builder.get_insights()
print(insights["top_mentioned_entities"])

builder.save_graph("data/viz/knowledge_graph.json")
```

---

### 2.2 EntityExtractor

**功能**: 实体提取器

**位置**: `src.analysis.knowledge_graph`

**方法**:

#### extract_entities(text)

从文本中提取实体

**参数**:
- `text` (str): 输入文本

**返回值**: List[Dict]

```python
[
    {
        "text": "服务",
        "type": "服务",
        "start": 0,
        "end": 2
    },
    ...
]
```

---

## 3. 多模态分析API

### 3.1 MultimodalSentimentAnalyzer

**功能**: 多模态情感分析器

**位置**: `src.analysis.multimodal_sentiment`

**类方法**:

#### __init__()

初始化分析器

#### set_weights(text_weight, emoji_weight, image_weight)

设置各模态权重

**参数**:
- `text_weight` (float): 文本权重，默认0.6
- `emoji_weight` (float): 表情权重，默认0.3
- `image_weight` (float): 图片权重，默认0.1

#### analyze(text, image_path, image_url, image_description, use_text_analysis)

多模态情感分析

**参数**:
- `text` (str): 文本内容
- `image_path` (str, optional): 图片路径
- `image_url` (str, optional): 图片URL
- `image_description` (str, optional): 图片描述
- `use_text_analysis` (bool): 是否使用文本分析，默认True

**返回值**:
```python
{
    "final_sentiment": str,      # 最终情感: "positive", "negative", "neutral"
    "final_polarity": str,       # 最终极性: "积极", "中性", "消极"
    "final_emotion": str,        # 最终情绪
    "final_score": float,        # 最终分数 (-1 to 1)
    "csi_score": int,            # CSI指数 (0-100)
    "text_analysis": {...},      # 文本分析结果
    "emoji_analysis": {...},     # 表情分析结果
    "image_analysis": {...},     # 图片分析结果
    "weights_used": {...},       # 使用的权重
    "modalities_used": {...}     # 使用的模态
}
```

**示例**:

```python
from src.analysis.multimodal_sentiment import MultimodalSentimentAnalyzer

analyzer = MultimodalSentimentAnalyzer()
analyzer.set_weights(text_weight=0.6, emoji_weight=0.3, image_weight=0.1)

result = analyzer.analyze("迪士尼太好玩了！😊🎉")
print(result["final_polarity"])  # 输出: 积极
```

---

### 3.2 EmojiAnalyzer

**功能**: 表情符号分析器

**位置**: `src.analysis.multimodal_sentiment`

**方法**:

#### extract_emojis(text)

提取文本中的表情符号

#### analyze_emoji_sentiment(text)

分析表情符号的情感

---

## 4. 舆情传播API

### 4.1 PublicOpinionAnalyzer

**功能**: 舆情传播分析器

**位置**: `src.analysis.opinion_propagation`

**类方法**:

#### add_post(post_id, author, content, timestamp, platform, sentiment, replies_to, reposts_of)

添加单条帖子

#### build_from_dataframe(df, ...)

从DataFrame构建网络

#### calculate_pagerank(damping_factor, max_iterations, tol)

计算PageRank

**参数**:
- `damping_factor` (float): 阻尼系数，默认0.85
- `max_iterations` (int): 最大迭代次数，默认100
- `tol` (float): 收敛阈值，默认1e-6

#### find_influential_nodes(top_k)

找到影响力节点

**参数**:
- `top_k` (int): 返回前k个节点

**返回值**: List[Dict]

#### get_network_data()

获取网络数据

#### get_insights()

获取传播分析洞察

#### save_analysis(output_path)

保存分析结果

**示例**:

```python
from src.analysis.opinion_propagation import PublicOpinionAnalyzer

analyzer = PublicOpinionAnalyzer()
analyzer.build_from_dataframe(df)
analyzer.calculate_pagerank()

top_nodes = analyzer.find_influential_nodes(top_k=10)
print(top_nodes)
```

---

## 5. 情感演化API

### 5.1 SentimentEvolutionAnalyzer

**功能**: 情感动态演化分析器

**位置**: `src.analysis.sentiment_evolution`

**类方法**:

#### prepare_time_series(df, time_col, sentiment_col, csi_col, content_col, time_window)

准备时间序列数据

#### detect_evolution_phases(df, csi_col, threshold)

检测演化阶段

**返回值**:
```python
[
    {
        "start_date": datetime,
        "end_date": datetime,
        "start_csi": float,
        "end_csi": float,
        "trend": str,  # "improving", "stable", "declining"
        "magnitude": float
    },
    ...
]
```

#### analyze_sentiment_shift(df, sentiment_col, window_size)

分析情感转移

**返回值**:
```python
{
    "transition_matrix": {...},  # 转移矩阵
    "window_shifts": [...],      # 窗口变化
    "sentiment_order": [...]     # 情感顺序
}
```

#### detect_emerging_topics(df, content_col, time_col, window_days, top_k)

检测新兴话题

#### get_evolution_insights(df)

获取演化分析洞察

#### save_analysis(insights, output_path)

保存分析结果

**示例**:

```python
from src.analysis.sentiment_evolution import SentimentEvolutionAnalyzer

analyzer = SentimentEvolutionAnalyzer("data/viz")
insights = analyzer.get_evolution_insights(df)

print(insights["evolution_phases"])
print(insights["emerging_topics"])
```

---

## 6. 工具函数API

### 6.1 PerformanceMonitor

**功能**: 性能监控器

**位置**: `src.utils.performance_monitor`

**类方法**:

#### start_timer(name)

开始计时

#### stop_timer(name)

停止计时

#### record_metric(name, value)

记录指标

#### get_system_info()

获取系统信息

**返回值**:
```python
{
    "timestamp": str,
    "cpu": {"percent": float, "count": int},
    "memory": {"total": float, "available": float, "percent": float, "used": float},
    "disk": {"total": float, "used": float, "free": float, "percent": float}
}
```

#### get_metrics_summary()

获取指标摘要

#### save_log()

保存日志

---

### 6.2 timing_decorator

**功能**: 计时装饰器

**位置**: `src.utils.performance_monitor`

**使用方法**:

```python
from src.utils.performance_monitor import timing_decorator, PerformanceMonitor

monitor = PerformanceMonitor()

@timing_decorator(monitor)
def my_function():
    # 函数逻辑
    pass

my_function()
print(monitor.function_stats["my_function"])
```

---

## 附录

### A. 错误码

| 错误码 | 描述 | 解决方案 |
|--------|------|---------|
| E001 | API密钥无效 | 检查DEEPSEEK_API_KEY配置 |
| E002 | 网络连接失败 | 检查网络连接 |
| E003 | 数据格式错误 | 检查CSV文件格式 |
| E004 | 内存不足 | 减少批处理数据量 |
| E005 | 文件不存在 | 检查文件路径 |

### B. 配置参数

| 参数名 | 默认值 | 描述 |
|--------|--------|------|
| MAX_RETRIES | 3 | 最大重试次数 |
| TIMEOUT | 30 | 超时时间(秒) |
| PAGE_LOAD_WAIT | 5 | 页面加载等待时间(秒) |
| DEFAULT_SENTIMENT_MODE | "hybrid" | 默认情感分析模式 |
| DEFAULT_DEEPSEEK_RATIO | 0.1 | 默认DeepSeek分析比例 |

---

**文档版本**: 3.0
**最后更新**: 2026年2月28日