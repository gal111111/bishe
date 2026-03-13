# -*- coding: utf-8 -*-
"""
情感分析模块
使用DeepSeek-V3大模型进行情感分析
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
    # 如果deepseek_client不存在，创建一个简化版本
    class DeepSeekClient:
        def __init__(self):
            pass
        
        def chat_completion(self, messages, model="deepseek-chat", temperature=0.3, max_tokens=1000):
            # 模拟情感分析结果
            return {"choices": [{"message": {"content": "这是一个积极的评论。\n\n情感倾向: 积极\n情感强度: 4\n具体情绪: 满意\n方面: 服务态度\n情感原因: 服务人员态度友好\nCSI满意度指数: 85\n紧急度: 0\n需要整改: 否"}}]}

# 尝试导入SnowNLP
try:
    from snownlp import SnowNLP
    HAS_SNOWNLP = True
except ImportError:
    HAS_SNOWNLP = False
    print("[WARN] 未安装SnowNLP，将使用DeepSeek API")

# 迪士尼领域方面类别
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
SENTIMENT_DICT = {
    "积极": ["好", "棒", "优秀", "满意", "喜欢", "赞", "推荐", "舒服", "方便", "干净", "快速", "热情", "专业", "贴心", "周到", "准时", "丰富", "精彩", "值得"],
    "消极": ["差", "糟糕", "失望", "不满", "讨厌", "坑", "贵", "慢", "脏", "乱", "吵", "拥挤", "冷漠", "不专业", "敷衍", "迟到", "单调", "无聊", "不值"],
    "中性": ["一般", "普通", "还行", "马马虎虎", "凑合", "中规中矩"]
}

# 程度副词词典
DEGREE_ADVERBS = {
    "非常": 1.5, "特别": 1.4, "很": 1.3, "相当": 1.2, "十分": 1.2, "极其": 1.6, "超级": 1.5,
    "比较": 0.8, "有点": 0.6, "稍微": 0.5, "略微": 0.4,
    "不": -1, "没": -1, "无": -1, "非": -1, "未": -1
}

# 初始化DeepSeek客户端
try:
    deepseek_client = DeepSeekClient()
except Exception as e:
    print(f"[WARN] 初始化DeepSeek客户端失败: {e}")
    deepseek_client = None

# 缓存文件路径
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "cache")
SENTIMENT_CACHE_FILE = os.path.join(CACHE_DIR, "sentiment_cache.json")
SUGGESTION_CACHE_FILE = os.path.join(CACHE_DIR, "suggestion_cache.json")

# 确保缓存目录存在
os.makedirs(CACHE_DIR, exist_ok=True)

# 加载缓存
def load_cache(cache_file):
    """加载缓存"""
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[WARN] 加载缓存失败: {e}")
    return {}

# 保存缓存
def save_cache(cache_file, cache):
    """保存缓存"""
    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[WARN] 保存缓存失败: {e}")

# 加载缓存
sentiment_cache = load_cache(SENTIMENT_CACHE_FILE)
suggestion_cache = load_cache(SUGGESTION_CACHE_FILE)
print(f"[OK] 缓存已加载: 情感分析 {len(sentiment_cache)} 条, 建议 {len(suggestion_cache)} 条")

def call_deepseek_api(messages: List[Dict[str, str]], model: str = None, temperature: float = 0.3, max_tokens: int = 1000) -> Optional[Dict[str, str]]:
    """调用DeepSeek API"""
    if not deepseek_client:
        print("[WARN] DeepSeek客户端未初始化，使用模拟数据")
        
        # 分析请求内容，返回合适的模拟数据
        user_content = ""
        system_content = ""
        for msg in messages:
            if msg.get("role") == "user":
                user_content = msg.get("content", "")
            elif msg.get("role") == "system":
                system_content = msg.get("content", "")
        
        # 检查是否是搜索词优化请求
        if "搜索策略优化专家" in system_content or "生成优化的搜索词" in user_content or "优化搜索词" in user_content or "搜索词" in user_content:
            # 从用户内容中提取关键词
            keyword = "广州图书馆"
            if "广州图书馆" in user_content:
                keyword = "广州图书馆"
            elif "国家博物馆" in user_content:
                keyword = "国家博物馆"
            
            # 根据关键词生成相关搜索词
            search_terms_map = {
                "广州图书馆": [
                    "广州图书馆怎么样",
                    "广州图书馆体验",
                    "广州图书馆服务",
                    "广州图书馆环境",
                    "广州图书馆藏书",
                    "广州图书馆自习",
                    "广州图书馆开放时间",
                    "广州图书馆预约",
                    "广州图书馆设施",
                    "广州图书馆评价"
                ],
                "国家博物馆": [
                    "国家博物馆怎么样",
                    "国家博物馆体验",
                    "国家博物馆服务",
                    "国家博物馆环境",
                    "国家博物馆展览",
                    "国家博物馆门票",
                    "国家博物馆开放时间",
                    "国家博物馆预约",
                    "国家博物馆设施",
                    "国家博物馆评价"
                ],
                "default": [
                    f"{keyword}怎么样",
                    f"{keyword}体验",
                    f"{keyword}服务",
                    f"{keyword}环境",
                    f"{keyword}设施",
                    f"{keyword}评价",
                    f"{keyword}开放时间",
                    f"{keyword}预约",
                    f"{keyword}用户体验",
                    f"{keyword}满意度"
                ]
            }
            
            search_terms = search_terms_map.get(keyword, search_terms_map["default"])
            return {"content": "\n".join(search_terms)}
        else:
            # 模拟情感分析结果
            return {"content": "这是一个积极的评论。\n\n情感倾向：积极\n情感强度：4\n具体情绪：满意\n方面：服务态度\n情感原因：服务人员态度友好\nCSI满意度指数：85\n紧急度：0\n需要整改：否"}
    
    try:
        # 构建请求
        response = deepseek_client.chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        if response and "choices" in response and len(response["choices"]) > 0:
            content = response["choices"][0]["message"]["content"]
            return {"content": content}
        else:
            print("[WARN] DeepSeek API返回格式错误")
            return None
    except Exception as e:
        print(f"[WARN] 调用DeepSeek API失败: {e}")
        return None

def extract_aspects(text: str) -> List[Dict[str, str]]:
    """
    从文本中提取方面及其情感
    
    Args:
        text: 待分析的文本
        
    Returns:
        方面及其情感的列表
    """
    aspects = []
    
    # 确保text是字符串
    text = str(text) if text is not None else ""
    
    # 遍历所有方面类别
    for aspect_category, sub_aspects in DISNEY_ASPECTS.items():
        # 检查是否包含该方面的关键词
        for sub_aspect in sub_aspects:
            if sub_aspect in text:
                # 提取该方面的情感
                aspect_sentiment = analyze_aspect_sentiment(text, sub_aspect)
                aspects.append({
                    "category": aspect_category,
                    "aspect": sub_aspect,
                    "polarity": aspect_sentiment["polarity"],
                    "intensity": aspect_sentiment["intensity"],
                    "specific_emotion": aspect_sentiment["specific_emotion"],
                    "csi_score": aspect_sentiment["csi_score"]
                })
    
    # 如果没有提取到任何方面，添加一个默认方面
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
    分析特定方面的情感
    
    Args:
        text: 待分析的文本
        aspect: 要分析的方面
        
    Returns:
        情感分析结果
    """
    # 默认返回值
    default_result = {
        "polarity": "中性",
        "intensity": "3",
        "specific_emotion": "中性",
        "csi_score": "50"
    }
    
    # 计算情感得分
    sentiment_score = 0.0
    degree_factor = 1.0
    
    # 检查情感词
    for sentiment, words in SENTIMENT_DICT.items():
        for word in words:
            if word in text:
                # 计算情感得分
                if sentiment == "积极":
                    sentiment_score += 1.0
                elif sentiment == "消极":
                    sentiment_score -= 1.0
                else:
                    sentiment_score += 0.0
    
    # 检查程度副词
    for adverb, factor in DEGREE_ADVERBS.items():
        if adverb in text:
            degree_factor *= factor
    
    # 应用程度副词的影响
    sentiment_score *= degree_factor
    
    # 确定情感倾向
    if sentiment_score > 0.5:
        polarity = "积极"
        specific_emotion = "满意"
        intensity = str(min(5, int(sentiment_score * 2) + 3))
        csi_score = str(int(min(100, 50 + sentiment_score * 25)))
    elif sentiment_score < -0.5:
        polarity = "消极"
        specific_emotion = "失望"
        intensity = str(min(5, int(abs(sentiment_score) * 2) + 3))
        csi_score = str(int(max(0, 50 + sentiment_score * 25)))
    else:
        polarity = "中性"
        specific_emotion = "中性"
        intensity = "3"
        csi_score = "50"
    
    return {
        "polarity": polarity,
        "intensity": intensity,
        "specific_emotion": specific_emotion,
        "csi_score": csi_score
    }

def analyze_sentiment(text: str, preferred: str = "deepseek") -> Dict[str, str]:
    """分析单条文本的情感"""
    # 确保text是字符串
    text = str(text) if text is not None else ""
    # 检查缓存
    cache_key = text.strip()[:200]
    if cache_key in sentiment_cache:
        return sentiment_cache[cache_key]
    
    print(f"🤖 分析情感: {text[:50]}...")
    
    # 默认返回值
    default_result = {
        "polarity": "中性",
        "intensity": "3",
        "specific_emotion": "中性",
        "aspect": "其他",
        "reason": "无法分析",
        "csi_score": "50",
        "urgency": "0",
        "need_improvement": "否",
        "polarity_label": "中性"
    }
    
    # 优先使用SnowNLP进行快速分析
    if HAS_SNOWNLP and preferred != "deepseek":
        try:
            s = SnowNLP(text)
            sentiment_score = s.sentiments
            
            result = default_result.copy()
            
            # 根据SnowNLP分数确定情感
            if sentiment_score > 0.65:
                result["polarity"] = "积极"
                result["specific_emotion"] = "满意"
                result["intensity"] = str(min(5, int((sentiment_score - 0.65) / 0.07) + 3))
                result["csi_score"] = str(int(sentiment_score * 100))
                result["need_improvement"] = "否"
            elif sentiment_score < 0.35:
                result["polarity"] = "消极"
                result["specific_emotion"] = "失望"
                result["intensity"] = str(min(5, int((0.35 - sentiment_score) / 0.07) + 3))
                result["csi_score"] = str(int(sentiment_score * 100))
                result["urgency"] = str(min(10, int((0.35 - sentiment_score) / 0.035) + 2))
                result["need_improvement"] = "是"
            else:
                result["polarity"] = "中性"
                result["specific_emotion"] = "中性"
                result["intensity"] = "3"
                result["csi_score"] = "50"
                result["need_improvement"] = "否"
            
            result["polarity_label"] = result["polarity"]
            result["reason"] = "SnowNLP快速分析"
            
            # 保存到缓存
            sentiment_cache[cache_key] = result
            save_cache(SENTIMENT_CACHE_FILE, sentiment_cache)
            
            return result
        except Exception as e:
            print(f"[WARN] SnowNLP分析失败，尝试使用DeepSeek: {e}")
    
    # 使用DeepSeek进行分析（备选方案）
    if preferred == "deepseek":
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
        
        messages = [
            {"role": "system", "content": "你是一个专业的情感分析师，擅长通过思维链（Chain-of-Thought）进行深入的情感分析。请先思考，再给出结构化的分析结果。"},
            {"role": "user", "content": prompt}
        ]
        
        response = call_deepseek_api(messages)
        
        if response and "content" in response:
            content = response["content"]
            # 解析结果
            result = default_result.copy()
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if "情感倾向：" in line:
                    result["polarity"] = line.split("情感倾向：")[1]
                elif "情感强度：" in line:
                    result["intensity"] = line.split("情感强度：")[1]
                elif "具体情绪：" in line:
                    result["specific_emotion"] = line.split("具体情绪：")[1]
                elif "方面：" in line:
                    result["aspect"] = line.split("方面：")[1]
                elif "情感原因：" in line:
                    result["reason"] = line.split("情感原因：")[1]
                elif "CSI满意度指数：" in line:
                    result["csi_score"] = line.split("CSI满意度指数：")[1]
                elif "紧急度：" in line:
                    result["urgency"] = line.split("紧急度：")[1]
                elif "需要整改：" in line:
                    result["need_improvement"] = line.split("需要整改：")[1]
            
            # 标准化情感倾向标签
            polarity_map = {
                "积极": "积极",
                "消极": "消极",
                "中性": "中性"
            }
            result["polarity_label"] = polarity_map.get(result.get("polarity"), "中性")
            
            # 保存到缓存
            sentiment_cache[cache_key] = result
            save_cache(SENTIMENT_CACHE_FILE, sentiment_cache)
            
            return result
    
    # 默认返回
    sentiment_cache[cache_key] = default_result
    save_cache(SENTIMENT_CACHE_FILE, sentiment_cache)
    return default_result

def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """预处理数据 - 增强版，过滤无意义评论"""
    # 复制数据以避免修改原数据
    df_processed = df.copy()
    
    # 确保content列存在
    if 'content' not in df_processed.columns:
        if '评论内容' in df_processed.columns:
            df_processed['content'] = df_processed['评论内容']
        else:
            df_processed['content'] = ''
    
    # 清洗content列
    df_processed['content'] = df_processed['content'].astype(str).apply(lambda x: x.strip())
    
    # 定义无意义评论模式
    meaningless_patterns = [
        r'^[\d\s]+$',  # 纯数字或空白
        r'^[^\u4e00-\u9fa5a-zA-Z]+$',  # 无中文和英文
        r'^[哈哈呵呵嘿嘿嘻嘻哈哈]+$',  # 纯笑声
        r'^[哦哦嗯呢啊啊]+$',  # 纯语气词
        r'^[好的好的好的好的]+$',  # 重复词语
        r'^[顶支持赞]+$',  # 纯支持词
        r'^[沙发板凳地板]+$',  # 纯占位词
        r'^[.。…]+$',  # 纯省略号
        r'^mark$|^打卡$|^签到$',  # 打卡标记
        r'^[a-zA-Z]+$',  # 纯英文（太短）
    ]
    
    # 过滤无意义评论
    import re
    def is_meaningful(text):
        if len(text) < 5:  # 太短的评论
            return False
        for pattern in meaningless_patterns:
            if re.match(pattern, text):
                return False
        # 检查是否包含至少一个中文或英文单词
        if not re.search(r'[\u4e00-\u9fa5]|[a-zA-Z]{3,}', text):
            return False
        return True
    
    df_processed = df_processed[df_processed['content'].apply(is_meaningful)]
    
    # 过滤空内容
    df_processed = df_processed[df_processed['content'].str.len() > 0]
    
    # 重置索引
    df_processed = df_processed.reset_index(drop=True)
    
    print(f"[OK] 数据预处理完成：过滤后剩余 {len(df_processed)} 条有效评论")
    
    return df_processed

def analyze_dataframe(df: pd.DataFrame, preferred: str = "snownlp", progress_callback: Optional[Callable] = None, deepseek_ratio: float = 0.1) -> pd.DataFrame:
    """
    分析DataFrame中的所有文本
    
    参数:
        preferred: 分析方式 - "snownlp", "deepseek", 或 "hybrid"（混合模式）
        deepseek_ratio: 混合模式下使用DeepSeek分析的比例（0.0-1.0）
    """
    # 预处理数据
    df_processed = preprocess_data(df)
    
    # 分析情感
    results = []
    total = len(df_processed)
    
    # 混合模式策略
    use_hybrid = preferred == "hybrid"
    deepseek_count = 0
    deepseek_target = int(total * deepseek_ratio) if use_hybrid else 0
    
    print(f"[INFO] 分析模式: {preferred}" + (f", DeepSeek分析目标: {deepseek_target}/{total} 条" if use_hybrid else ""))
    
    for i, row in df_processed.iterrows():
        if progress_callback:
            progress_callback(i / total)
        
        text = row.get('comment_content', '') or row.get('content', '')
        if not text or text == 'NULL':
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
            # 决定使用哪种分析方式
            current_method = preferred
            if use_hybrid:
                # 混合模式策略：
                # 1. 优先对长文本使用DeepSeek
                # 2. 确保达到目标比例
                text_length = len(text)
                should_use_deepseek = (
                    (text_length > 30 and deepseek_count < deepseek_target) or
                    (deepseek_count < deepseek_target * 0.5)  # 确保至少一半目标量
                )
                if should_use_deepseek:
                    current_method = "deepseek"
                    deepseek_count += 1
                else:
                    current_method = "snownlp"
            
            # 分析整体情感
            result = analyze_sentiment(text, current_method)
            result["analysis_method"] = current_method
            
            # 提取方面级情感
            aspects = extract_aspects(text)
            result["aspects"] = json.dumps(aspects, ensure_ascii=False)
        
        # 将结果添加到行中
        row_dict = row.to_dict()
        row_dict.update(result)
        results.append(row_dict)
    
    # 创建新的DataFrame
    df_analyzed = pd.DataFrame(results)
    
    # 确保数值列的类型正确
    numeric_columns = ['intensity', 'csi_score', 'urgency']
    for col in numeric_columns:
        if col in df_analyzed.columns:
            df_analyzed[col] = pd.to_numeric(df_analyzed[col], errors='coerce').fillna(0)
    
    # 添加紧急度评分列
    if 'urgency' in df_analyzed.columns:
        df_analyzed['urgency_score'] = df_analyzed['urgency']
    
    if use_hybrid:
        method_counts = df_analyzed['analysis_method'].value_counts()
        print(f"[OK] 混合分析完成: SnowNLP {method_counts.get('snownlp', 0)} 条, DeepSeek {method_counts.get('deepseek', 0)} 条")
    
    return df_analyzed

def generate_ai_report(df: pd.DataFrame, preferred: str = "deepseek", per_facility_samples: int = 30) -> tuple:
    """生成AI分析报告"""
    print("📝 生成AI分析报告...")
    
    # 按设施类型分组
    if 'facility_type' not in df.columns:
        df['facility_type'] = '未知'
    
    facility_groups = df.groupby('facility_type')
    
    # 生成报告数据
    report_data = []
    aspect_data = []
    absa_data = []
    detailed_absa_data = []
    
    for facility, group in facility_groups:
        # 限制每个设施的样本数量
        sample_group = group.sample(min(len(group), per_facility_samples), random_state=42)
        
        # 计算基本统计
        total = len(group)
        positive = len(group[group['polarity_label'] == '积极'])
        negative = len(group[group['polarity_label'] == '消极'])
        neutral = len(group[group['polarity_label'] == '中性'])
        
        avg_csi = group['csi_score'].mean() if 'csi_score' in group.columns else 50
        avg_urgency = group['urgency_score'].mean() if 'urgency_score' in group.columns else 0
        
        # 生成报告
        report_data.append({
            'facility_type': facility,
            'total_comments': total,
            'positive_count': positive,
            'negative_count': negative,
            'neutral_count': neutral,
            'positive_rate': positive / total * 100 if total > 0 else 0,
            'negative_rate': negative / total * 100 if total > 0 else 0,
            'avg_csi_score': avg_csi,
            'avg_urgency_score': avg_urgency
        })
        
        # 生成方面数据
        if 'aspect' in group.columns:
            aspect_counts = group['aspect'].value_counts()
            for aspect, count in aspect_counts.items():
                aspect_group = group[group['aspect'] == aspect]
                aspect_positive = len(aspect_group[aspect_group['polarity_label'] == '积极'])
                aspect_negative = len(aspect_group[aspect_group['polarity_label'] == '消极'])
                aspect_avg_csi = aspect_group['csi_score'].mean() if 'csi_score' in aspect_group.columns else 50
                
                aspect_data.append({
                    'facility_type': facility,
                    'aspect': aspect,
                    'count': count,
                    'positive_count': aspect_positive,
                    'negative_count': aspect_negative,
                    'positive_rate': aspect_positive / count * 100 if count > 0 else 0,
                    'negative_rate': aspect_negative / count * 100 if count > 0 else 0,
                    'avg_csi_score': aspect_avg_csi
                })
        
        # 生成ABSA数据
        if 'aspect' in group.columns and 'csi_score' in group.columns:
            absa_group = group.groupby('aspect')
            for aspect, absa_subgroup in absa_group:
                absa_data.append({
                    'facility_type': facility,
                    'aspect': aspect,
                    'count': len(absa_subgroup),
                    'avg_csi_score': absa_subgroup['csi_score'].mean(),
                    'std_csi_score': absa_subgroup['csi_score'].std() if len(absa_subgroup) > 1 else 0,
                    'min_csi_score': absa_subgroup['csi_score'].min(),
                    'max_csi_score': absa_subgroup['csi_score'].max()
                })
        
        # 处理详细的方面级情感分析数据
        if 'aspects' in group.columns:
            for _, row in group.iterrows():
                try:
                    aspects = json.loads(row.get('aspects', '[]'))
                    for aspect_info in aspects:
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
                    print(f"[WARN] 解析aspects字段失败: {e}")
    
    # 创建DataFrame
    report_df = pd.DataFrame(report_data)
    aspect_df = pd.DataFrame(aspect_data)
    absa_report_df = pd.DataFrame(absa_data)
    detailed_absa_df = pd.DataFrame(detailed_absa_data)
    
    return report_df, aspect_df, absa_report_df, detailed_absa_df

if __name__ == "__main__":
    # 测试
    text = "广州图书馆的环境很好，书籍很全，服务态度也不错"
    result = analyze_sentiment(text)
    print("分析结果:")
    for key, value in result.items():
        print(f"{key}: {value}")
