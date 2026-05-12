# -*- coding: utf-8 -*-
"""
方面级情感分析模块
功能：提取（实体，方面，情感）三元组，实现细粒度情感分析
"""

import re
import pandas as pd
from typing import List, Dict, Tuple, Optional
from loguru import logger
import jieba
from collections import defaultdict

# 实体-方面词典
ENTITY_ASPECT_DICT = {
    "设施": ["排队", "设备", "硬件", "建筑", "场馆", "设施", "游乐设施", "过山车", "城堡", "餐厅", "商店"],
    "服务": ["服务", "态度", "效率", "管理", "人员", "员工", "客服", "工作人员", "导游"],
    "环境": ["环境", "卫生", "安静", "整洁", "噪音", "干净", "脏乱", "清洁"],
    "位置": ["位置", "交通", "便利", "距离", "地铁", "公交", "停车场"],
    "价格": ["价格", "费用", "收费", "门票", "贵", "便宜", "性价比", "物价"],
    "安全": ["安全", "保安", "防护", "隐患", "危险", "保险"],
    "时间": ["时间", "开放", "预约", "排队时间", "营业时间", "等待"],
    "餐饮": ["餐饮", "食物", "好吃", "难吃", "餐厅", "美食", "味道", "菜品"]
}

# 情感词词典
POSITIVE_WORDS = [
    "好", "棒", "优秀", "赞", "喜欢", "满意", "开心", "高兴", "快乐", "愉快",
    "精彩", "出色", "完美", "很棒", "超好", "太赞", "推荐", "值得", "划算",
    "舒适", "方便", "快捷", "热情", "耐心", "专业", "负责", "干净", "整洁"
]

NEGATIVE_WORDS = [
    "差", "坏", "糟糕", "烂", "不好", "失望", "讨厌", "难过", "生气", "愤怒",
    "糟糕", "垃圾", "浪费", "贵", "坑", "骗人", "失望", "后悔", "不值",
    "拥挤", "脏乱", "吵闹", "慢", "低效", "冷漠", "粗鲁", "不专业"
]

# 否定词
NEGATION_WORDS = ["不", "没", "没有", "别", "不要", "非", "无", "未"]

# 程度副词
DEGREE_WORDS = {
    "非常": 1.5, "特别": 1.5, "极其": 1.8, "十分": 1.3, "很": 1.2,
    "比较": 0.8, "有点": 0.6, "稍微": 0.5, "太": 1.5, "超": 1.6
}


class AspectBasedSentimentAnalyzer:
    """
    方面级情感分析器
    功能：提取（实体，方面，情感）三元组
    """
    
    def __init__(self):
        """
        初始化方面级情感分析器
        """
        self.entity_aspect_dict = ENTITY_ASPECT_DICT
        self.positive_words = POSITIVE_WORDS
        self.negative_words = NEGATIVE_WORDS
        self.negation_words = NEGATION_WORDS
        self.degree_words = DEGREE_WORDS
        
        logger.info("[方面级情感分析] 初始化完成")
    
    def extract_entities(self, text: str) -> List[Dict]:
        """
        从文本中提取实体
        
        Args:
            text: 输入文本
            
        Returns:
            实体列表，每个实体包含：text, type, position
        """
        entities = []
        
        for entity_type, aspects in self.entity_aspect_dict.items():
            for aspect in aspects:
                matches = re.finditer(re.escape(aspect), text)
                for match in matches:
                    entities.append({
                        "text": aspect,
                        "type": entity_type,
                        "start": match.start(),
                        "end": match.end()
                    })
        
        # 按位置排序
        entities.sort(key=lambda x: x["start"])
        return entities
    
    def extract_aspects(self, text: str, entity: Dict) -> List[str]:
        """
        提取实体的方面描述
        
        Args:
            text: 输入文本
            entity: 实体信息
            
        Returns:
            方面词列表
        """
        aspects = []
        
        # 在实体周围查找方面描述
        window_size = 20
        start = max(0, entity["start"] - window_size)
        end = min(len(text), entity["end"] + window_size)
        context = text[start:end]
        
        # 查找情感词作为方面描述
        words = jieba.lcut(context)
        for word in words:
            if word in self.positive_words or word in self.negative_words:
                aspects.append(word)
        
        return aspects
    
    def analyze_aspect_sentiment(self, text: str, entity: Dict, aspect: str) -> Dict:
        """
        分析某个方面的情感
        
        Args:
            text: 输入文本
            entity: 实体信息
            aspect: 方面词
            
        Returns:
            情感分析结果，包含：polarity, score, explanation
        """
        # 查找aspect的位置
        aspect_pos = text.find(aspect)
        if aspect_pos == -1:
            return {
                "aspect": aspect,
                "polarity": "中性",
                "score": 0.0,
                "explanation": "未找到方面词"
            }
        
        # 在aspect周围查找情感线索
        window_size = 15
        start = max(0, aspect_pos - window_size)
        end = min(len(text), aspect_pos + window_size)
        context = text[start:end]
        
        sentiment_score = 0.0
        sentiment_words = []
        negation_found = False
        degree_multiplier = 1.0
        
        words = jieba.lcut(context)
        
        for i, word in enumerate(words):
            # 检查否定词
            if word in self.negation_words:
                negation_found = not negation_found
            
            # 检查程度副词
            if word in self.degree_words:
                degree_multiplier = self.degree_words[word]
            
            # 检查情感词
            if word in self.positive_words:
                base_score = 0.8
                if negation_found:
                    base_score = -0.8
                    negation_found = False
                sentiment_score += base_score * degree_multiplier
                sentiment_words.append(word)
                degree_multiplier = 1.0
            
            if word in self.negative_words:
                base_score = -0.8
                if negation_found:
                    base_score = 0.8
                    negation_found = False
                sentiment_score += base_score * degree_multiplier
                sentiment_words.append(word)
                degree_multiplier = 1.0
        
        # 确定极性
        if sentiment_score > 0.2:
            polarity = "积极"
        elif sentiment_score < -0.2:
            polarity = "消极"
        else:
            polarity = "中性"
        
        # 限制分数范围
        sentiment_score = max(-1.0, min(1.0, sentiment_score))
        
        return {
            "aspect": aspect,
            "polarity": polarity,
            "score": sentiment_score,
            "explanation": f"情感词: {', '.join(sentiment_words) if sentiment_words else '无'}",
            "sentiment_words": sentiment_words
        }
    
    def analyze(self, text: str) -> Dict:
        """
        对文本进行方面级情感分析
        
        Args:
            text: 输入文本
            
        Returns:
            分析结果，包含：
            - triples: (实体, 方面, 情感)三元组列表
            - overall_sentiment: 整体情感
            - aspect_sentiments: 各方面情感详情
        """
        if not text or not isinstance(text, str):
            return {
                "triples": [],
                "overall_sentiment": "中性",
                "overall_score": 0.0,
                "aspect_sentiments": []
            }
        
        text = str(text)
        
        # 提取实体
        entities = self.extract_entities(text)
        
        triples = []
        aspect_sentiments = []
        total_score = 0.0
        count = 0
        
        for entity in entities:
            # 提取方面
            aspects = self.extract_aspects(text, entity)
            
            for aspect in aspects:
                # 分析方面情感
                aspect_result = self.analyze_aspect_sentiment(text, entity, aspect)
                
                triples.append({
                    "entity": entity["text"],
                    "entity_type": entity["type"],
                    "aspect": aspect,
                    "polarity": aspect_result["polarity"],
                    "score": aspect_result["score"]
                })
                
                aspect_sentiments.append({
                    "entity": entity["text"],
                    "entity_type": entity["type"],
                    **aspect_result
                })
                
                total_score += aspect_result["score"]
                count += 1
        
        # 计算整体情感
        if count > 0:
            overall_score = total_score / count
        else:
            overall_score = 0.0
        
        if overall_score > 0.2:
            overall_sentiment = "积极"
        elif overall_score < -0.2:
            overall_sentiment = "消极"
        else:
            overall_sentiment = "中性"
        
        return {
            "triples": triples,
            "overall_sentiment": overall_sentiment,
            "overall_score": overall_score,
            "aspect_sentiments": aspect_sentiments,
            "entity_count": len(entities),
            "aspect_count": len(triples)
        }
    
    def analyze_dataframe(self, df: pd.DataFrame, text_column: str = "content") -> pd.DataFrame:
        """
        对DataFrame进行批量方面级情感分析
        
        Args:
            df: 输入DataFrame
            text_column: 文本列名
            
        Returns:
            添加了方面级分析结果的DataFrame
        """
        results = []
        
        for idx, row in df.iterrows():
            text = row[text_column]
            result = self.analyze(text)
            
            # 提取关键信息
            result_row = {
                "absa_triples": str(result["triples"]),
                "absa_overall_sentiment": result["overall_sentiment"],
                "absa_overall_score": result["overall_score"],
                "absa_entity_count": result["entity_count"],
                "absa_aspect_count": result["aspect_count"]
            }
            
            results.append(result_row)
            
            if (idx + 1) % 100 == 0:
                logger.info(f"[方面级情感分析] 已处理 {idx + 1}/{len(df)} 条")
        
        # 合并结果
        result_df = pd.DataFrame(results)
        return pd.concat([df.reset_index(drop=True), result_df], axis=1)
    
    def get_summary(self, df: pd.DataFrame) -> Dict:
        """
        获取方面级分析的摘要统计
        
        Args:
            df: 已分析的DataFrame
            
        Returns:
            摘要统计
        """
        if "absa_triples" not in df.columns:
            return {"error": "需要先进行方面级情感分析"}
        
        # 统计实体类型分布
        entity_type_counts = defaultdict(int)
        aspect_sentiment_counts = defaultdict(lambda: defaultdict(int))
        
        for triples_str in df["absa_triples"]:
            try:
                triples = eval(triples_str)
                for triple in triples:
                    entity_type = triple["entity_type"]
                    entity_type_counts[entity_type] += 1
                    
                    polarity = triple["polarity"]
                    aspect_sentiment_counts[entity_type][polarity] += 1
            except:
                continue
        
        # 计算总体统计
        total_triples = sum(entity_type_counts.values())
        
        return {
            "total_triples": total_triples,
            "entity_type_distribution": dict(entity_type_counts),
            "aspect_sentiment_by_type": {k: dict(v) for k, v in aspect_sentiment_counts.items()},
            "top_entity_types": sorted(entity_type_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        }
