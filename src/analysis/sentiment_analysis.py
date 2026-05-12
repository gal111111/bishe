# -*- coding: utf-8 -*-
"""
情感分析模块
==========
本模块实现了基于多策略融合的评论情感分析功能，主要包含以下核心能力：

1. SnowNLP本地情感分析：基于贝叶斯模型的轻量级中文情感分析，适合大规模快速处理
2. DeepSeek大模型情感分析：基于思维链（Chain-of-Thought）的深度情感理解，准确率更高
3. 混合分析策略（Hybrid）：结合SnowNLP的效率与DeepSeek的精度，按比例智能分配分析引擎
4. 情感词典匹配：基于领域情感词典和程度副词的规则化情感评分
5. CSI满意度指数计算：将情感得分映射为0-100的标准化满意度指数
6. 方面级情感分析（ABSA）：针对迪士尼主题乐园的细粒度方面情感提取

模块设计遵循"本地优先、云端增强"的原则，通过缓存机制减少API调用开销，
支持批量数据分析和AI报告生成。
"""
import os
import sys
import json
import time
import random
import pandas as pd
from typing import List, Dict, Optional, Callable

# 尝试加载.env文件
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from src.utils.deepseek_client import DeepSeekClient
except ImportError:
    # 如果deepseek_client不存在，不创建简化版本，直接设为None
    DeepSeekClient = None

# 尝试导入SnowNLP
try:
    from snownlp import SnowNLP
    HAS_SNOWNLP = True
except ImportError:
    HAS_SNOWNLP = False
    print("[WARN] 未安装SnowNLP，将使用DeepSeek API")

# 迪士尼领域方面类别
# 定义迪士尼主题乐园评论的11个核心方面类别，每个类别包含5个子方面关键词
# 用于方面级情感分析（ABSA），将评论情感归因到具体业务维度
DISNEY_ASPECTS = {
    "服务": ["服务态度", "工作人员", "客服", "服务质量", "服务效率"],
    "环境": ["卫生", "环境整洁", "空气质量", "噪音", "绿化"],
    "设施": ["游乐设施", "休息区", "厕所", "餐饮设施", "购物设施"],
    "排队": ["排队时间", "排队秩序", "排队环境", "快速通", "排队管理"],
    "价格": ["门票价格", "餐饮价格", "商品价格", "性价比", "优惠活动"],
    "时间": ["开放时间", "表演时间", "项目运行时间", "等待时间", "游玩时间"],
    "交通": ["交通便利", "停车", "公共交通", "入园速度", "离园交通"],
    "餐饮": ["餐饮质量", "餐饮种类", "餐饮价格", "餐饮环境", "餐饮服务"],
    "表演": ["烟花表演", "花车巡游", "舞台表演", "表演质量", "表演时间"],
    "住宿": ["酒店环境", "酒店服务", "酒店价格", "酒店设施", "酒店位置"],
    "其他": ["整体体验", "安全性", "便利性", "创新性", "推荐度"]
}

# 情感词典
# 包含积极、消极、中性三类情感词汇，用于基于规则的情感倾向判断
# 词典匹配时结合程度副词进行加权计算，提升情感评分的准确性
SENTIMENT_DICT = {
    "积极": ["好", "棒", "优秀", "满意", "喜欢", "赞", "推荐", "舒服", "方便", "干净", "快速", "热情", "专业", "贴心", "周到", "准时", "丰富", "精彩", "值得"],
    "消极": ["差", "糟糕", "失望", "不满", "讨厌", "坑", "贵", "慢", "脏", "乱", "吵", "拥挤", "冷漠", "不专业", "敷衍", "迟到", "单调", "无聊", "不值"],
    "中性": ["一般", "普通", "还行", "马马虎虎", "凑合", "中规中矩"]
}

# 程度副词词典
# 正向程度副词（如"非常"=1.5）放大情感强度，负向程度副词（如"不"=-1）翻转情感极性
# 计算方式：情感得分 × 程度副词乘积，实现细粒度的情感强度调节
DEGREE_ADVERBS = {
    "非常": 1.5, "特别": 1.4, "很": 1.3, "相当": 1.2, "十分": 1.2, "极其": 1.6, "超级": 1.5,
    "比较": 0.8, "有点": 0.6, "稍微": 0.5, "略微": 0.4,
    "不": -1, "没": -1, "无": -1, "非": -1, "未": -1
}

# 初始化DeepSeek客户端
# 采用多层异常捕获，确保客户端初始化失败不会影响模块加载
try:
    if DeepSeekClient:
        try:
            deepseek_client = DeepSeekClient()  # 创建DeepSeek API客户端实例
        except Exception as e:
            # 静默处理客户端创建错误（如API密钥缺失）
            deepseek_client = None
    else:
        deepseek_client = None  # DeepSeekClient模块未导入，客户端不可用
except Exception:
    # 静默处理所有初始化错误
    deepseek_client = None

# 缓存文件路径配置
# 优先使用项目根目录下的data/cache路径，失败时回退到当前目录的cache子目录
try:
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    CACHE_DIR = os.path.join(PROJECT_ROOT, "data", "cache")  # 项目级缓存目录
    SENTIMENT_CACHE_FILE = os.path.join(CACHE_DIR, "sentiment_cache.json")  # 情感分析缓存文件
    SUGGESTION_CACHE_FILE = os.path.join(CACHE_DIR, "suggestion_cache.json")  # 建议缓存文件
    
    # 确保缓存目录存在
    os.makedirs(CACHE_DIR, exist_ok=True)
except Exception:
    # 路径异常时回退到当前目录下的cache子目录
    CACHE_DIR = "./cache"
    SENTIMENT_CACHE_FILE = os.path.join(CACHE_DIR, "sentiment_cache.json")
    SUGGESTION_CACHE_FILE = os.path.join(CACHE_DIR, "suggestion_cache.json")
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
    except Exception:
        pass

# 加载缓存
def load_cache(cache_file):
    """
    加载JSON格式的缓存文件
    
    从指定路径读取缓存文件并解析为字典，用于避免重复的情感分析计算。
    采用多层异常捕获策略，确保I/O错误不会影响主流程。
    
    Args:
        cache_file: 缓存文件的绝对路径
        
    Returns:
        dict: 解析成功返回缓存字典，任何异常均返回空字典
    """
    try:
        # 检查文件是否存在
        try:
            if not os.path.exists(cache_file):
                return {}
        except Exception:
            # 静默处理路径检查错误
            return {}
        
        # 尝试打开和读取文件
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    # 静默处理JSON解析错误
                    return {}
        except Exception:
            # 静默处理文件读取错误
            pass
    except Exception:
        # 静默处理所有错误
        pass
    return {}

# 保存缓存
def save_cache(cache_file, cache):
    """
    将缓存字典序列化保存为JSON文件
    
    自动创建目标目录，以UTF-8编码和缩进格式写入，确保中文可读性。
    采用静默异常处理，避免缓存写入失败影响主业务流程。
    
    Args:
        cache_file: 缓存文件的绝对路径
        cache: 待保存的缓存字典
    """
    try:
        # 确保缓存目录存在
        try:
            os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        except Exception:
            # 静默处理目录创建错误
            pass
        
        # 尝试写入文件
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
        except Exception:
            # 静默处理文件写入错误
            pass
    except Exception:
        # 静默处理所有保存错误
        pass

# 加载已有缓存到内存
try:
    # 初始化缓存变量为空字典
    sentiment_cache = {}
    suggestion_cache = {}
    
    # 分别加载情感分析缓存和建议缓存
    try:
        sentiment_cache = load_cache(SENTIMENT_CACHE_FILE)
    except Exception:
        pass
    
    try:
        suggestion_cache = load_cache(SUGGESTION_CACHE_FILE)
    except Exception:
        pass
    
    # 静默处理，避免I/O错误
    # print(f"[OK] 缓存已加载: 情感分析 {len(sentiment_cache)} 条, 建议 {len(suggestion_cache)} 条")
except Exception:
    # 静默处理所有缓存加载错误
    sentiment_cache = {}
    suggestion_cache = {}

CACHE_FLUSH_INTERVAL = 50  # 缓存刷新阈值：每50次变更自动写盘一次
_sentiment_cache_dirty_count = 0  # 脏计数器：记录自上次写盘以来的缓存变更次数

def flush_sentiment_cache(force: bool = False):
    """
    批量刷新情感缓存，避免逐条写盘造成性能瓶颈。
    
    采用脏计数阈值机制，仅当累积变更达到CACHE_FLUSH_INTERVAL时才触发写盘，
    减少频繁I/O操作。force参数用于在分析结束时强制落盘，确保数据完整性。
    
    Args:
        force: 是否强制刷新缓存到磁盘，默认为False
    """
    global _sentiment_cache_dirty_count
    if force or _sentiment_cache_dirty_count >= CACHE_FLUSH_INTERVAL:
        save_cache(SENTIMENT_CACHE_FILE, sentiment_cache)
        _sentiment_cache_dirty_count = 0

def mark_sentiment_cache_dirty():
    """
    标记缓存变更，并按阈值自动落盘。
    
    每次情感分析结果写入缓存后调用，递增脏计数器。
    当脏计数达到CACHE_FLUSH_INTERVAL（默认50）时自动触发flush_sentiment_cache，
    实现延迟批量写入，平衡性能与数据安全。
    """
    global _sentiment_cache_dirty_count
    _sentiment_cache_dirty_count += 1
    flush_sentiment_cache(force=False)

def call_deepseek_api(messages: List[Dict[str, str]], model: str = None, temperature: float = 0.3, max_tokens: int = 1000) -> Optional[Dict[str, str]]:
    """
    调用DeepSeek大模型API进行文本分析
    
    封装DeepSeek客户端的聊天补全接口，统一异常处理策略。
    当客户端未初始化或API返回异常时，向上抛出RuntimeError，
    由调用方决定降级策略（如切换到SnowNLP本地分析）。
    
    Args:
        messages: OpenAI格式的消息列表，包含role和content字段
        model: 指定模型名称，默认使用客户端配置的模型
        temperature: 生成温度，越低越确定，范围0-1，默认0.3
        max_tokens: 最大生成token数，默认1000
        
    Returns:
        Optional[Dict[str, str]]: 成功时返回{"content": "模型回复内容"}
        
    Raises:
        RuntimeError: 客户端未初始化或API返回格式异常时抛出
    """
    if not deepseek_client:
        raise RuntimeError("DeepSeek客户端未初始化，请检查API密钥配置")

    # 调用DeepSeek聊天补全接口，传入消息列表和生成参数
    response = deepseek_client.chat_completion(
        messages=messages,
        model=model,
        temperature=temperature,  # 低温度（0.3）确保输出稳定可解析
        max_tokens=max_tokens
    )

    # 解析API响应，提取第一个choice中的content字段
    if response and "choices" in response and len(response["choices"]) > 0:
        content = response["choices"][0]["message"]["content"]
        return {"content": content}
    else:
        raise RuntimeError("DeepSeek API返回格式异常，无法解析响应内容")

def extract_aspects(text: str) -> List[Dict[str, str]]:
    """
    从文本中提取方面及其情感（方面级情感分析ABSA的核心函数）
    
    遍历DISNEY_ASPECTS词典，通过关键词匹配识别文本中涉及的方面，
    并调用analyze_aspect_sentiment计算每个匹配方面的情感得分。
    若文本未匹配到任何方面，则默认归为"整体体验"方面。
    
    Args:
        text: 待分析的评论文本
        
    Returns:
        List[Dict[str, str]]: 方面及其情感的列表，每个元素包含：
            - category: 方面所属类别（如"服务"、"环境"）
            - aspect: 具体方面名称（如"服务态度"、"排队时间"）
            - polarity: 情感极性
            - intensity: 情感强度
            - specific_emotion: 具体情绪
            - csi_score: CSI满意度指数
    """
    aspects = []  # 存储所有匹配到的方面及其情感分析结果
    
    # 确保text是字符串
    text = str(text) if text is not None else ""
    
    # 遍历所有方面类别，通过子方面关键词进行文本匹配
    for aspect_category, sub_aspects in DISNEY_ASPECTS.items():
        # 检查文本是否包含该方面类别下的子方面关键词
        for sub_aspect in sub_aspects:
            if sub_aspect in text:
                # 关键词命中，调用情感分析函数计算该方面的情感得分
                aspect_sentiment = analyze_aspect_sentiment(text, sub_aspect)
                # 将分析结果组装为结构化字典，包含类别、方面和四项情感指标
                aspects.append({
                    "category": aspect_category,
                    "aspect": sub_aspect,
                    "polarity": aspect_sentiment["polarity"],
                    "intensity": aspect_sentiment["intensity"],
                    "specific_emotion": aspect_sentiment["specific_emotion"],
                    "csi_score": aspect_sentiment["csi_score"]
                })
    
    # 兜底策略：若未匹配到任何方面，使用"整体体验"作为默认方面
    # 确保每条评论至少有一个方面的情感分析结果
    if not aspects:
        # 直接使用analyze_aspect_sentiment分析整体情感
        general_sentiment = analyze_aspect_sentiment(text, "整体体验")
        aspects.append({
            "category": "其他",
            "aspect": "整体体验",
            "polarity": general_sentiment["polarity"],
            "intensity": general_sentiment["intensity"],
            "specific_emotion": general_sentiment["specific_emotion"],
            "csi_score": general_sentiment["csi_score"]
        })
    
    return aspects

def analyze_aspect_sentiment(text: str, aspect: str) -> Dict[str, str]:
    """
    分析特定方面的情感（基于情感词典的规则化分析方法）
    
    通过情感词典匹配和程度副词加权，计算文本在指定方面的情感得分，
    并将得分映射为情感极性、强度和CSI满意度指数。
    
    Args:
        text: 待分析的评论文本
        aspect: 要分析的具体方面（如"服务态度"、"排队时间"等）
        
    Returns:
        Dict[str, str]: 包含以下字段的情感分析结果：
            - polarity: 情感极性（"积极"/"消极"/"中性"）
            - intensity: 情感强度（1-5，5为最强）
            - specific_emotion: 具体情绪描述（如"满意"、"失望"）
            - csi_score: CSI满意度指数（0-100）
    """
    # 默认返回值：中性情感，强度3级，CSI 50分
    default_result = {
        "polarity": "中性",       # 情感极性：积极/消极/中性
        "intensity": "3",         # 情感强度：1-5级
        "specific_emotion": "中性", # 具体情绪描述
        "csi_score": "50"         # CSI满意度指数：0-100
    }
    
    # 计算情感得分，初始化为0（中性）
    sentiment_score = 0.0
    degree_factor = 1.0  # 程度副词累积因子，初始为1.0（无修饰）
    
    # 【情感词典匹配】遍历情感词典，统计文本中出现的情感词并累加得分
    # 积极词+1.0，消极词-1.0，中性词+0.0
    for sentiment, words in SENTIMENT_DICT.items():
        for word in words:
            if word in text:
                # 根据情感类别计算得分增量
                if sentiment == "积极":
                    sentiment_score += 1.0
                elif sentiment == "消极":
                    sentiment_score -= 1.0
                else:
                    sentiment_score += 0.0
    
    # 【程度副词匹配】检测文本中的程度副词，计算累积修饰因子
    # 正向副词（如"非常"1.5）放大情感，负向副词（如"不"-1）翻转极性
    for adverb, factor in DEGREE_ADVERBS.items():
        if adverb in text:
            degree_factor *= factor
    
    # 应用程度副词的加权影响，得到最终情感得分
    sentiment_score *= degree_factor
    
    # 【CSI满意度指数计算】将情感得分映射为标准化指标
    # 阈值±0.5区分积极/消极/中性，得分越高CSI越高
    if sentiment_score > 0.5:
        polarity = "积极"
        specific_emotion = "满意"
        # 强度映射：基于得分计算1-5级，基准3级+得分增量
        intensity = str(min(5, int(sentiment_score * 2) + 3))
        # CSI映射：基准50分+得分×25，上限100
        csi_score = str(int(min(100, 50 + sentiment_score * 25)))
    elif sentiment_score < -0.5:
        polarity = "消极"
        specific_emotion = "失望"
        # 消极强度：取绝对值计算，确保强度为正数
        intensity = str(min(5, int(abs(sentiment_score) * 2) + 3))
        # CSI映射：基准50分+负向得分×25，下限0
        csi_score = str(int(max(0, 50 + sentiment_score * 25)))
    else:
        # 中性区间（-0.5 ~ 0.5），默认强度3级，CSI 50分
        polarity = "中性"
        specific_emotion = "中性"
        intensity = "3"
        csi_score = "50"
    
    return {
        "polarity": polarity,           # 情感极性
        "intensity": intensity,         # 情感强度（1-5）
        "specific_emotion": specific_emotion,  # 具体情绪
        "csi_score": csi_score          # CSI满意度指数（0-100）
    }

def analyze_sentiment(text: str, preferred: str = "deepseek") -> Dict[str, str]:
    """
    分析单条文本的情感（核心分析函数，支持多策略切换）
    
    根据preferred参数选择分析引擎：
    - "snownlp": 使用SnowNLP进行本地快速分析，基于贝叶斯模型，适合批量处理
    - "deepseek": 使用DeepSeek大模型进行深度分析，基于思维链推理，准确率更高
    - "hybrid": 由analyze_dataframe统一调度，按比例分配SnowNLP和DeepSeek
    
    分析结果包含情感极性、强度、具体情绪、CSI满意度指数等8个维度。
    所有结果均写入缓存，相同文本不重复分析。
    
    Args:
        text: 待分析的评论文本
        preferred: 分析引擎偏好，可选"snownlp"/"deepseek"，默认"deepseek"
        
    Returns:
        Dict[str, str]: 情感分析结果字典，包含以下字段：
            - polarity: 情感极性（"积极"/"消极"/"中性"）
            - intensity: 情感强度（1-5）
            - specific_emotion: 具体情绪（如"满意"、"失望"）
            - aspect: 涉及的方面
            - reason: 情感原因或分析方法说明
            - csi_score: CSI满意度指数（0-100）
            - urgency: 紧急度（0-10）
            - need_improvement: 是否需要整改（"是"/"否"）
            - polarity_label: 标准化情感标签
    """
    # 确保text是字符串
    text = str(text) if text is not None else ""
    # 检查缓存：使用文本前200字符作为缓存键，避免重复分析
    cache_key = text.strip()[:200]
    if cache_key in sentiment_cache:
        return sentiment_cache[cache_key]  # 缓存命中，直接返回历史结果
    
    print(f"🤖 分析情感: {text[:50]}...")  # 输出分析进度，截取前50字符
    
    # 默认返回值：中性情感，强度3级，CSI 50分
    default_result = {
        "polarity": "中性",         # 情感极性
        "intensity": "3",           # 情感强度（1-5）
        "specific_emotion": "中性", # 具体情绪
        "aspect": "其他",           # 涉及方面
        "reason": "无法分析",       # 分析原因
        "csi_score": "50",          # CSI满意度指数
        "urgency": "0",             # 紧急度（0-10）
        "need_improvement": "否",   # 是否需要整改
        "polarity_label": "中性"    # 标准化情感标签
    }
    
    # 【SnowNLP情感分析】优先使用SnowNLP进行本地快速分析
    # SnowNLP基于朴素贝叶斯模型，返回0-1之间的情感概率值
    # 阈值设定：>0.55为积极，<0.45为消极，中间为中性
    # 注：原阈值0.65/0.35过于保守，短文本几乎全被判中性，调整为0.55/0.45更合理
    if HAS_SNOWNLP and preferred != "deepseek":
        try:
            s = SnowNLP(text)
            sentiment_score = s.sentiments
            
            result = default_result.copy()
            
            if sentiment_score > 0.55:
                result["polarity"] = "积极"
                result["specific_emotion"] = "满意"
                result["intensity"] = str(min(5, int((sentiment_score - 0.55) / 0.09) + 3))
                result["csi_score"] = str(int(sentiment_score * 100))
                result["need_improvement"] = "否"
            elif sentiment_score < 0.45:
                result["polarity"] = "消极"
                result["specific_emotion"] = "失望"
                result["intensity"] = str(min(5, int((0.45 - sentiment_score) / 0.09) + 3))
                result["csi_score"] = str(int(sentiment_score * 100))
                result["urgency"] = str(min(10, int((0.45 - sentiment_score) / 0.045) + 2))
                result["need_improvement"] = "是"
            else:
                result["polarity"] = "中性"
                result["specific_emotion"] = "中性"
                result["intensity"] = "3"
                result["csi_score"] = "50"
                result["need_improvement"] = "否"
            
            result["polarity_label"] = result["polarity"]  # 极性标签与极性值一致
            result["reason"] = "SnowNLP快速分析"  # 标注分析方法来源
            
            # 保存到缓存并标记脏数据，等待批量落盘
            sentiment_cache[cache_key] = result
            mark_sentiment_cache_dirty()
            
            return result
        except Exception as e:
            # SnowNLP分析异常时降级到DeepSeek，保证分析流程不中断
            print(f"[WARN] SnowNLP分析失败，尝试使用DeepSeek: {e}")
    
    # 【DeepSeek大模型分析】使用思维链提示词进行深度情感理解
    # 当SnowNLP不可用或用户指定deepseek时启用
    if preferred == "deepseek":
        # 构建思维链提示词，引导模型按5步推理：理解→识别→分析→判断→输出
        prompt = f"""
        你是一个专业的情感分析师，负责分析公共设施相关评论的情感。
        
        请按照以下思维链（Chain-of-Thought）逐步分析：
        
        【思考步骤1：理解评论】
        首先理解这条评论在说什么，提取关键信息。
        
        【思考步骤2：识别实体和方面】
        识别评论中提到的实体（如设施、服务、环境等）和具体方面（如排队时间、服务态度、卫生状况等）。
        
        【思考步骤3：分析情感线索】
        找出评论中的情感词、否定词、程度副词，分析它们对情感的影响。
        
        【思考步骤4：判断整体情感】
        综合以上分析，判断整体情感倾向和强度。
        
        【思考步骤5：给出结构化输出】
        按照以下格式输出分析结果：
        
        情感倾向：积极/消极/中性
        情感强度：1-5（1最弱，5最强）
        具体情绪：如满意、愤怒、失望、开心等
        方面：评论涉及的具体方面，如服务态度、环境、设施等
        情感原因：简要说明情感产生的原因
        CSI满意度指数：0-100（综合满意度）
        紧急度：0-10（问题紧急程度，0为无问题）
        需要整改：是/否
        
        评论内容：{text}
        """
        
        # 构建消息列表，包含系统角色设定和用户分析请求
        messages = [
            {"role": "system", "content": "你是一个专业的情感分析师，擅长通过思维链（Chain-of-Thought）进行深入的情感分析。请先思考，再给出结构化的分析结果。"},
            {"role": "user", "content": prompt}
        ]
        
        # 调用DeepSeek API获取分析结果
        response = call_deepseek_api(messages)
        
        if response and "content" in response:
            content = response["content"]
            # 【结果解析】逐行解析DeepSeek返回的结构化文本
            # 提取情感倾向、强度、具体情绪、方面、原因、CSI、紧急度、整改建议
            result = default_result.copy()  # 基于默认值创建结果副本
            lines = content.split('\n')  # 按换行符分割响应文本
            for line in lines:
                line = line.strip()
                # 逐字段匹配并提取DeepSeek输出的结构化信息
                if "情感倾向：" in line:
                    result["polarity"] = line.split("情感倾向：")[1]  # 提取情感极性
                elif "情感强度：" in line:
                    result["intensity"] = line.split("情感强度：")[1]  # 提取情感强度
                elif "具体情绪：" in line:
                    result["specific_emotion"] = line.split("具体情绪：")[1]  # 提取具体情绪
                elif "方面：" in line:
                    result["aspect"] = line.split("方面：")[1]  # 提取涉及方面
                elif "情感原因：" in line:
                    result["reason"] = line.split("情感原因：")[1]  # 提取情感原因
                elif "CSI满意度指数：" in line:
                    result["csi_score"] = line.split("CSI满意度指数：")[1]  # 提取CSI指数
                elif "紧急度：" in line:
                    result["urgency"] = line.split("紧急度：")[1]  # 提取紧急度
                elif "需要整改：" in line:
                    result["need_improvement"] = line.split("需要整改：")[1]  # 提取整改建议
            
            # 【冲突解决机制】标准化情感倾向标签
            # 将DeepSeek可能返回的多种表述统一映射为"积极"/"消极"/"中性"
            # 未匹配的标签默认归为"中性"，避免标签不一致导致的下游错误
            polarity_map = {
                "积极": "积极",  # 积极映射
                "消极": "消极",  # 消极映射
                "中性": "中性"   # 中性映射
            }
            result["polarity_label"] = polarity_map.get(result.get("polarity"), "中性")  # 默认中性
            
            # 保存DeepSeek分析结果到缓存
            sentiment_cache[cache_key] = result
            mark_sentiment_cache_dirty()
            
            return result
    
    # 所有分析引擎均不可用，返回默认中性结果并缓存
    sentiment_cache[cache_key] = default_result
    mark_sentiment_cache_dirty()
    return default_result

def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    预处理评论数据，过滤无意义评论（增强版）
    
    执行以下清洗步骤：
    1. 列名标准化：将"评论内容"列统一映射为"content"
    2. 文本清洗：去除首尾空白，统一转为字符串类型
    3. 无意义评论过滤：基于正则模式匹配，过滤纯数字、纯语气词、
       纯占位词、纯笑声等无实质内容的评论
    4. 长度过滤：剔除长度小于5的过短评论
    5. 语言检测：确保评论包含至少一个中文或3个以上英文字符
    
    Args:
        df: 原始评论数据DataFrame，需包含content或评论内容列
        
    Returns:
        pd.DataFrame: 清洗后的DataFrame，已重置索引，仅保留有效评论
    """
    # 复制数据以避免修改原数据
    df_processed = df.copy()
    
    # 列名标准化：确保content列存在
    if 'content' not in df_processed.columns:
        # 尝试从中文列名"评论内容"映射
        if '评论内容' in df_processed.columns:
            df_processed['content'] = df_processed['评论内容']
        else:
            # 无有效内容列，填充空字符串
            df_processed['content'] = ''
    
    # 文本清洗：统一转为字符串类型并去除首尾空白
    df_processed['content'] = df_processed['content'].astype(str).apply(lambda x: x.strip() if isinstance(x, str) else str(x))
    
    # 定义无意义评论的正则匹配模式
    # 这些模式覆盖了评论数据中常见的噪声类型
    meaningless_patterns = [
        r'^[\d\s]+$',  # 纯数字或空白
        r'^[^\u4e00-\u9fa5a-zA-Z]+$',  # 无中文和英文（纯符号/表情）
        r'^[哈哈呵呵嘿嘿嘻嘻哈哈]+$',  # 纯笑声（无实质内容）
        r'^[哦哦嗯呢啊啊]+$',  # 纯语气词
        r'^[好的好的好的好的]+$',  # 重复词语
        r'^[顶支持赞]+$',  # 纯支持词（论坛常见）
        r'^[沙发板凳地板]+$',  # 纯占位词（论坛常见）
        r'^[.。…]+$',  # 纯省略号
        r'^mark$|^打卡$|^签到$',  # 打卡标记（无实质评价）
        r'^[a-zA-Z]+$',  # 纯英文（过短，无参考价值）
    ]
    
    # 定义有意义的评论判断函数
    import re
    def is_meaningful(text):
        # 长度过滤：少于5个字符的评论通常无实质内容
        if len(text) < 5:
            return False
        # 正则模式过滤：匹配无意义评论模式
        for pattern in meaningless_patterns:
            if re.match(pattern, text):
                return False
        # 语言检测：至少包含一个中文字符或3个以上英文字符
        if not re.search(r'[\u4e00-\u9fa5]|[a-zA-Z]{3,}', text):
            return False
        return True
    
    # 应用过滤函数，仅保留有意义的评论
    df_processed = df_processed[df_processed['content'].apply(is_meaningful)]
    
    # 二次过滤：移除空内容行
    df_processed = df_processed[df_processed['content'].str.len() > 0]
    
    # 重置索引，避免过滤后索引不连续
    df_processed = df_processed.reset_index(drop=True)
    
    print(f"[OK] 数据预处理完成：过滤后剩余 {len(df_processed)} 条有效评论")
    
    return df_processed

def analyze_dataframe(df: pd.DataFrame, preferred: str = "snownlp", progress_callback: Optional[Callable] = None, deepseek_ratio: float = 0.1) -> pd.DataFrame:
    """
    批量分析DataFrame中所有评论的情感（支持多策略和混合模式）
    
    三种分析模式：
    - "snownlp": 全部使用SnowNLP本地分析，速度快，适合大规模数据
    - "deepseek": 全部使用DeepSeek大模型分析，精度高，但API调用成本大
    - "hybrid": 混合分析策略，按deepseek_ratio比例分配DeepSeek分析量，
      优先对长文本（>30字）使用DeepSeek，短文本使用SnowNLP，
      兼顾分析效率和结果精度
    
    Args:
        df: 待分析的评论DataFrame
        preferred: 分析模式，可选"snownlp"/"deepseek"/"hybrid"，默认"snownlp"
        progress_callback: 进度回调函数，参数为0-1的浮点数表示完成比例
        deepseek_ratio: 混合模式下DeepSeek分析的比例（0.0-1.0），默认0.1
        
    Returns:
        pd.DataFrame: 包含原始列和情感分析结果的新DataFrame，
            新增列包括polarity、intensity、csi_score、urgency等
    """
    # 预处理数据：过滤无意义评论，标准化列名
    df_processed = preprocess_data(df)
    
    # 初始化结果列表和总数
    results = []
    total = len(df_processed)
    
    # 【混合分析策略】初始化混合模式参数
    # 混合模式根据deepseek_ratio比例分配DeepSeek和SnowNLP的分析量
    use_hybrid = preferred == "hybrid"
    deepseek_count = 0  # 已使用DeepSeek分析的计数器
    deepseek_target = int(total * deepseek_ratio) if use_hybrid else 0  # DeepSeek分析目标数量
    
    print(f"[INFO] 分析模式: {preferred}" + (f", DeepSeek分析目标: {deepseek_target}/{total} 条" if use_hybrid else ""))
    
    # 逐行分析每条评论
    for i, row in df_processed.iterrows():
        # 调用进度回调函数，报告当前分析进度
        if progress_callback:
            progress_callback(i / total)
        
        # 获取评论文本，兼容不同的列名
        text = row.get('comment_content', '') or row.get('content', '')
        if not text or text == 'NULL':
            # 空内容或NULL值，直接返回默认中性结果
            result = {
                "polarity": "中性",
                "intensity": "3",
                "specific_emotion": "中性",
                "aspect": "其他",
                "reason": "无内容",
                "csi_score": "50",
                "urgency": "0",
                "need_improvement": "否",
                "polarity_label": "中性",
                "analysis_method": "none",
                "aspects": "[]"
            }
        else:
            # 【混合分析策略调度】根据文本特征和配额决定分析引擎
            current_method = preferred
            if use_hybrid:
                # 混合模式调度策略：
                # 1. 长文本（>30字）优先使用DeepSeek，因为长文本语义更复杂
                # 2. 确保DeepSeek使用量至少达到目标配额的50%，避免分配不均
                # 3. 其余文本使用SnowNLP快速处理，保证整体效率
                text_length = len(text)
                should_use_deepseek = (
                    (text_length > 30 and deepseek_count < deepseek_target) or
                    (deepseek_count < deepseek_target * 0.5)  # 确保至少一半目标量
                )
                if should_use_deepseek:
                    current_method = "deepseek"  # 使用DeepSeek深度分析
                    deepseek_count += 1  # 递增DeepSeek使用计数
                else:
                    current_method = "snownlp"  # 使用SnowNLP快速分析
            
            # 分析整体情感
            result = analyze_sentiment(text, current_method)
            # 记录本次使用的分析方法，用于后续统计和报告
            result["analysis_method"] = current_method
            
            # 【方面级情感分析（ABSA】提取文本涉及的各个方面的情感
            # 返回每个匹配方面的极性、强度和CSI得分
            aspects = extract_aspects(text)
            result["aspects"] = json.dumps(aspects, ensure_ascii=False)  # 序列化为JSON字符串存储
        
        # 将分析结果合并到原始行数据中
        row_dict = row.to_dict()  # 将当前行转为字典
        row_dict.update(result)   # 合并情感分析结果
        results.append(row_dict)  # 添加到结果列表
    
    # 将结果列表转换为DataFrame
    df_analyzed = pd.DataFrame(results)
    
    # 确保数值列的类型正确，将字符串转为数值类型
    # 转换失败的值填充为0，避免后续计算出错
    numeric_columns = ['intensity', 'csi_score', 'urgency']
    for col in numeric_columns:
        if col in df_analyzed.columns:
            df_analyzed[col] = pd.to_numeric(df_analyzed[col], errors='coerce').fillna(0)
    
    # 添加紧急度评分列（与urgency列相同，用于统一命名）
    if 'urgency' in df_analyzed.columns:
        df_analyzed['urgency_score'] = df_analyzed['urgency']
    
    if use_hybrid:
        # 统计混合模式的分析方法分布，输出SnowNLP和DeepSeek各自处理的条数
        method_counts = df_analyzed['analysis_method'].value_counts()
        print(f"[OK] 混合分析完成: SnowNLP {method_counts.get('snownlp', 0)} 条, DeepSeek {method_counts.get('deepseek', 0)} 条")
    
    # 强制刷新缓存，确保所有分析结果已持久化到磁盘
    flush_sentiment_cache(force=True)

    return df_analyzed

def generate_ai_report(df: pd.DataFrame, preferred: str = "deepseek", per_facility_samples: int = 30) -> tuple:
    """
    生成AI分析报告，按设施类型聚合情感分析结果
    
    对已分析的评论数据按设施类型分组，计算各组的基本统计指标
    （评论数、积极/消极/中性比例、平均CSI满意度指数、平均紧急度），
    并生成四个维度的报告数据：
    1. report_df: 设施级汇总报告
    2. aspect_df: 方面级情感分布报告
    3. absa_report_df: 方面级ABSA统计报告（含CSI均值、标准差、极值）
    4. detailed_absa_df: 详细的方面级情感分析明细数据
    
    Args:
        df: 已完成情感分析的评论DataFrame，需包含polarity_label、csi_score等列
        preferred: 分析引擎偏好（保留参数，当前未使用）
        per_facility_samples: 每个设施类型的最大采样数量，默认30
        
    Returns:
        tuple: (report_df, aspect_df, absa_report_df, detailed_absa_df) 四个DataFrame
    """
    print("📝 生成AI分析报告...")
    
    # 按设施类型分组，若缺少facility_type列则统一标记为"未知"
    if 'facility_type' not in df.columns:
        df['facility_type'] = '未知'
    
    # 按设施类型分组聚合
    facility_groups = df.groupby('facility_type')
    
    # 生成报告数据
    report_data = []       # 设施级汇总数据
    aspect_data = []       # 方面级情感分布数据
    absa_data = []         # 方面级ABSA统计数据
    detailed_absa_data = [] # 详细的方面级情感分析明细
    
    for facility, group in facility_groups:
        # 限制每个设施的样本数量，避免大数据集导致处理时间过长
        sample_group = group.sample(min(len(group), per_facility_samples), random_state=42)
        
        # 计算基本统计指标
        total = len(group)
        positive = len(group[group['polarity_label'] == '积极'])
        negative = len(group[group['polarity_label'] == '消极'])
        neutral = len(group[group['polarity_label'] == '中性'])
        
        # 计算平均CSI满意度指数和平均紧急度
        avg_csi = group['csi_score'].mean() if 'csi_score' in group.columns else 50
        avg_urgency = group['urgency_score'].mean() if 'urgency_score' in group.columns else 0
        
        # 生成设施级汇总报告记录
        report_data.append({
            'facility_type': facility,
            'total_comments': total,
            'positive_count': positive,
            'negative_count': negative,
            'neutral_count': neutral,
            'positive_rate': positive / total * 100 if total > 0 else 0,  # 积极率（百分比）
            'negative_rate': negative / total * 100 if total > 0 else 0,  # 消极率（百分比）
            'avg_csi_score': avg_csi,
            'avg_urgency_score': avg_urgency
        })
        
        # 生成方面级情感分布数据
        if 'aspect' in group.columns:
            aspect_counts = group['aspect'].value_counts()
            for aspect, count in aspect_counts.items():
                aspect_group = group[group['aspect'] == aspect]
                # 统计该方面的积极/消极评论数和平均CSI
                aspect_positive = len(aspect_group[aspect_group['polarity_label'] == '积极'])
                aspect_negative = len(aspect_group[aspect_group['polarity_label'] == '消极'])
                aspect_avg_csi = aspect_group['csi_score'].mean() if 'csi_score' in aspect_group.columns else 50
                
                aspect_data.append({
                    'facility_type': facility,
                    'aspect': aspect,
                    'count': count,
                    'positive_count': aspect_positive,
                    'negative_count': aspect_negative,
                    'positive_rate': aspect_positive / count * 100 if count > 0 else 0,  # 方面积极率
                    'negative_rate': aspect_negative / count * 100 if count > 0 else 0,  # 方面消极率
                    'avg_csi_score': aspect_avg_csi
                })
        
        # 生成ABSA（基于方面的情感分析）统计数据
        # 包含每个方面的CSI均值、标准差、最小值和最大值
        if 'aspect' in group.columns and 'csi_score' in group.columns:
            # 按方面分组，计算每个方面的CSI统计量
            absa_group = group.groupby('aspect')
            for aspect, absa_subgroup in absa_group:
                absa_data.append({
                    'facility_type': facility,
                    'aspect': aspect,
                    'count': len(absa_subgroup),
                    'avg_csi_score': absa_subgroup['csi_score'].mean(),  # CSI均值
                    'std_csi_score': absa_subgroup['csi_score'].std() if len(absa_subgroup) > 1 else 0,  # CSI标准差（单条时为0）
                    'min_csi_score': absa_subgroup['csi_score'].min(),  # CSI最小值
                    'max_csi_score': absa_subgroup['csi_score'].max()   # CSI最大值
                })
        
        # 处理详细的方面级情感分析数据（从aspects JSON字段解析）
        # 将每条评论的方面级分析结果展开为独立记录
        if 'aspects' in group.columns:
            for _, row in group.iterrows():
                try:
                    # 解析每条评论的aspects JSON字段
                    aspects = json.loads(row.get('aspects', '[]'))
                    for aspect_info in aspects:
                        # 将每个方面的分析结果展开为独立的明细记录
                        detailed_absa_data.append({
                            'facility_type': facility,
                            'category': aspect_info.get('category', '其他'),
                            'aspect': aspect_info.get('aspect', '整体体验'),
                            'polarity': aspect_info.get('polarity', '中性'),
                            'intensity': int(aspect_info.get('intensity', '3')),
                            'specific_emotion': aspect_info.get('specific_emotion', '中性'),
                            'csi_score': float(aspect_info.get('csi_score', '50'))
                        })
                except Exception as e:
                    # aspects字段解析失败时输出警告，跳过该条记录
                    print(f"[WARN] 解析aspects字段失败: {e}")
    
    # 创建四个维度的报告DataFrame
    report_df = pd.DataFrame(report_data)
    aspect_df = pd.DataFrame(aspect_data)
    absa_report_df = pd.DataFrame(absa_data)
    detailed_absa_df = pd.DataFrame(detailed_absa_data)
    
    return report_df, aspect_df, absa_report_df, detailed_absa_df

if __name__ == "__main__":
    # 模块自测：使用示例文本验证情感分析流程
    text = "广州图书馆的环境很好，书籍很全，服务态度也不错"
    result = analyze_sentiment(text)
    print("分析结果:")
    for key, value in result.items():
        print(f"{key}: {value}")
