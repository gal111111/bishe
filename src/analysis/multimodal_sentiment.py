# -*- coding: utf-8 -*-
"""
多模态情感分析模块
综合分析文本、表情符号和图片的情感
"""
import os
import sys
import re
import json
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from src.analysis.sentiment_analysis import analyze_sentiment
except ImportError:
    pass

# 表情符号情感词典
EMOJI_SENTIMENT = {
    "😊": {"sentiment": "positive", "score": 0.8, "emotion": "开心"},
    "😄": {"sentiment": "positive", "score": 0.9, "emotion": "高兴"},
    "🥰": {"sentiment": "positive", "score": 0.95, "emotion": "喜爱"},
    "😍": {"sentiment": "positive", "score": 0.9, "emotion": "喜爱"},
    "👍": {"sentiment": "positive", "score": 0.85, "emotion": "赞同"},
    "👏": {"sentiment": "positive", "score": 0.8, "emotion": "赞赏"},
    "🎉": {"sentiment": "positive", "score": 0.9, "emotion": "庆祝"},
    "❤️": {"sentiment": "positive", "score": 0.95, "emotion": "喜爱"},
    "💕": {"sentiment": "positive", "score": 0.9, "emotion": "喜爱"},
    
    "😢": {"sentiment": "negative", "score": -0.8, "emotion": "悲伤"},
    "😭": {"sentiment": "negative", "score": -0.9, "emotion": "大哭"},
    "😠": {"sentiment": "negative", "score": -0.85, "emotion": "愤怒"},
    "😡": {"sentiment": "negative", "score": -0.9, "emotion": "愤怒"},
    "👎": {"sentiment": "negative", "score": -0.8, "emotion": "不赞同"},
    "💔": {"sentiment": "negative", "score": -0.9, "emotion": "心碎"},
    "😰": {"sentiment": "negative", "score": -0.7, "emotion": "焦虑"},
    "😱": {"sentiment": "negative", "score": -0.85, "emotion": "惊恐"},
    
    "😐": {"sentiment": "neutral", "score": 0.0, "emotion": "中性"},
    "🤔": {"sentiment": "neutral", "score": 0.1, "emotion": "思考"},
    "😶": {"sentiment": "neutral", "score": 0.0, "emotion": "沉默"},
    "🤷": {"sentiment": "neutral", "score": 0.0, "emotion": "无所谓"},
}

# 扩展的表情符号映射
EMOJI_ALIASES = {
    ":)": "😊",
    ":D": "😄",
    ":(": "😢",
    ":'(": "😭",
    ":|": "😐",
    "<3": "❤️",
    "</3": "💔",
    ":thumbsup:": "👍",
    ":thumbsdown:": "👎",
}

class EmojiAnalyzer:
    """表情符号分析器"""
    
    def __init__(self):
        self.emoji_pattern = re.compile(
            "["
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F700-\U0001F77F"  # alchemical symbols
            "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
            "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
            "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
            "\U0001FA00-\U0001FA6F"  # Chess Symbols
            "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
            "\U00002702-\U000027B0"  # Dingbats
            "\U000024C2-\U0001F251" 
            "]+",
            flags=re.UNICODE
        )
    
    def extract_emojis(self, text: str) -> List[Dict[str, Any]]:
        """
        从文本中提取表情符号
        
        参数:
            text: 输入文本
            
        返回:
            表情符号列表
        """
        emojis = []
        
        # 先替换文本表情符号别名
        for alias, emoji in EMOJI_ALIASES.items():
            text = text.replace(alias, emoji)
        
        # 提取Unicode表情符号
        matches = self.emoji_pattern.findall(text)
        
        for match in matches:
            for emoji_char in match:
                if emoji_char in EMOJI_SENTIMENT:
                    emojis.append({
                        "emoji": emoji_char,
                        **EMOJI_SENTIMENT[emoji_char]
                    })
        
        return emojis
    
    def analyze_emoji_sentiment(self, text: str) -> Dict[str, Any]:
        """
        分析表情符号的情感
        
        参数:
            text: 输入文本
            
        返回:
            表情符号情感分析结果
        """
        emojis = self.extract_emojis(text)
        
        if not emojis:
            return {
                "has_emoji": False,
                "emojis": [],
                "dominant_sentiment": "neutral",
                "overall_score": 0.0,
                "dominant_emotion": "中性"
            }
        
        positive_count = sum(1 for e in emojis if e["sentiment"] == "positive")
        negative_count = sum(1 for e in emojis if e["sentiment"] == "negative")
        neutral_count = sum(1 for e in emojis if e["sentiment"] == "neutral")
        
        total_score = sum(e["score"] for e in emojis)
        avg_score = total_score / len(emojis) if emojis else 0.0
        
        # 确定主导情感
        if avg_score > 0.3:
            dominant_sentiment = "positive"
        elif avg_score < -0.3:
            dominant_sentiment = "negative"
        else:
            dominant_sentiment = "neutral"
        
        # 最常见的情绪
        emotion_counts = Counter(e["emotion"] for e in emojis)
        dominant_emotion = emotion_counts.most_common(1)[0][0] if emotion_counts else "中性"
        
        return {
            "has_emoji": True,
            "emojis": emojis,
            "count": len(emojis),
            "positive_count": positive_count,
            "negative_count": negative_count,
            "neutral_count": neutral_count,
            "dominant_sentiment": dominant_sentiment,
            "overall_score": avg_score,
            "dominant_emotion": dominant_emotion
        }

class ImageAnalyzer:
    """图片分析器（简化版，基于图片URL/文件名分析）"""
    
    def __init__(self):
        self.image_keywords = {
            "positive": ["happy", "smile", "love", "beautiful", "great", "amazing", "wonderful", "excellent", "perfect", "awesome", "开心", "快乐", "幸福", "满意", "赞", "好"],
            "negative": ["sad", "angry", "bad", "terrible", "awful", "worst", "hate", "disappointed", "frustrated", "难过", "失望", "生气", "糟糕", "差"],
        }
    
    def analyze_image(self, image_path: Optional[str] = None, 
                     image_url: Optional[str] = None,
                     image_description: Optional[str] = None) -> Dict[str, Any]:
        """
        分析图片情感（简化版）
        
        参数:
            image_path: 图片路径
            image_url: 图片URL
            image_description: 图片描述
            
        返回:
            图片情感分析结果
        """
        analysis_text = ""
        if image_description:
            analysis_text = image_description
        elif image_path:
            analysis_text = os.path.basename(image_path)
        elif image_url:
            analysis_text = image_url
        
        if not analysis_text:
            return {
                "has_image": False,
                "sentiment": "neutral",
                "score": 0.0,
                "emotion": "中性"
            }
        
        # 简单的关键词匹配
        positive_hits = sum(1 for kw in self.image_keywords["positive"] if kw in analysis_text.lower())
        negative_hits = sum(1 for kw in self.image_keywords["negative"] if kw in analysis_text.lower())
        
        score = (positive_hits - negative_hits) * 0.2
        score = max(-1.0, min(1.0, score))
        
        if score > 0.2:
            sentiment = "positive"
            emotion = "积极"
        elif score < -0.2:
            sentiment = "negative"
            emotion = "消极"
        else:
            sentiment = "neutral"
            emotion = "中性"
        
        return {
            "has_image": True,
            "sentiment": sentiment,
            "score": score,
            "emotion": emotion,
            "analysis_text": analysis_text
        }

class MultimodalSentimentAnalyzer:
    """多模态情感分析器"""
    
    def __init__(self):
        self.emoji_analyzer = EmojiAnalyzer()
        self.image_analyzer = ImageAnalyzer()
        
        # 各模态权重
        self.weights = {
            "text": 0.6,
            "emoji": 0.3,
            "image": 0.1
        }
    
    def set_weights(self, text_weight: float = 0.6, emoji_weight: float = 0.3, image_weight: float = 0.1):
        """
        设置各模态权重
        
        参数:
            text_weight: 文本权重
            emoji_weight: 表情符号权重
            image_weight: 图片权重
        """
        total = text_weight + emoji_weight + image_weight
        self.weights = {
            "text": text_weight / total,
            "emoji": emoji_weight / total,
            "image": image_weight / total
        }
    
    def analyze(self, text: str, 
                image_path: Optional[str] = None,
                image_url: Optional[str] = None,
                image_description: Optional[str] = None,
                use_text_analysis: bool = True) -> Dict[str, Any]:
        """
        多模态情感分析
        
        参数:
            text: 文本内容
            image_path: 图片路径
            image_url: 图片URL
            image_description: 图片描述
            use_text_analysis: 是否使用文本情感分析
            
        返回:
            多模态情感分析结果
        """
        # 1. 文本分析
        text_result = {
            "sentiment": "neutral",
            "score": 0.0,
            "polarity": "中性",
            "csi_score": 50
        }
        
        if use_text_analysis:
            try:
                sa_result = analyze_sentiment(text, preferred="snownlp")
                text_result["sentiment"] = "positive" if sa_result.get("polarity") == "积极" else "negative" if sa_result.get("polarity") == "消极" else "neutral"
                text_result["score"] = (float(sa_result.get("csi_score", 50)) - 50) / 50
                text_result["polarity"] = sa_result.get("polarity", "中性")
                text_result["csi_score"] = float(sa_result.get("csi_score", 50))
            except:
                pass
        
        # 2. 表情符号分析
        emoji_result = self.emoji_analyzer.analyze_emoji_sentiment(text)
        
        # 3. 图片分析
        image_result = self.image_analyzer.analyze_image(
            image_path=image_path,
            image_url=image_url,
            image_description=image_description
        )
        
        # 4. 融合各模态
        scores = []
        weights_sum = 0
        
        # 文本分数
        if text_result["score"] != 0:
            scores.append(text_result["score"] * self.weights["text"])
            weights_sum += self.weights["text"]
        
        # 表情符号分数
        if emoji_result["has_emoji"]:
            scores.append(emoji_result["overall_score"] * self.weights["emoji"])
            weights_sum += self.weights["emoji"]
        
        # 图片分数
        if image_result["has_image"]:
            scores.append(image_result["score"] * self.weights["image"])
            weights_sum += self.weights["image"]
        
        # 计算最终分数
        final_score = sum(scores) / weights_sum if weights_sum > 0 else 0
        final_score = max(-1.0, min(1.0, final_score))
        
        # 确定最终情感
        if final_score > 0.1:
            final_sentiment = "positive"
            final_polarity = "积极"
            final_emotion = "满意"
            csi_score = 50 + final_score * 50
        elif final_score < -0.1:
            final_sentiment = "negative"
            final_polarity = "消极"
            final_emotion = "失望"
            csi_score = 50 + final_score * 50
        else:
            final_sentiment = "neutral"
            final_polarity = "中性"
            final_emotion = "中性"
            csi_score = 50
        
        return {
            "final_sentiment": final_sentiment,
            "final_polarity": final_polarity,
            "final_emotion": final_emotion,
            "final_score": final_score,
            "csi_score": int(csi_score),
            "text_analysis": text_result,
            "emoji_analysis": emoji_result,
            "image_analysis": image_result,
            "weights_used": self.weights.copy(),
            "modalities_used": {
                "text": text_result["score"] != 0,
                "emoji": emoji_result["has_emoji"],
                "image": image_result["has_image"]
            }
        }

if __name__ == "__main__":
    print("=" * 80)
    print("测试多模态情感分析模块")
    print("=" * 80)
    
    analyzer = MultimodalSentimentAnalyzer()
    
    # 测试案例
    test_cases = [
        {
            "text": "迪士尼真的太好玩了！😊🎉",
            "description": "纯文本+表情符号"
        },
        {
            "text": "排队排了3小时，太累了 😭",
            "description": "负面文本+表情"
        },
        {
            "text": "一般般吧 😐",
            "description": "中性文本+表情"
        },
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"测试案例 {i}: {test_case['description']}")
        print(f"{'='*80}")
        print(f"输入文本: {test_case['text']}")
        
        result = analyzer.analyze(test_case['text'])
        
        print(f"\n最终情感: {result['final_polarity']}")
        print(f"最终分数: {result['final_score']:.2f}")
        print(f"CSI指数: {result['csi_score']}")
        
        if result['emoji_analysis']['has_emoji']:
            print(f"\n表情符号分析:")
            print(f"  数量: {result['emoji_analysis']['count']}")
            print(f"  主导情感: {result['emoji_analysis']['dominant_sentiment']}")
            print(f"  表情列表: {[e['emoji'] for e in result['emoji_analysis']['emojis']]}")
    
    print("\n" + "=" * 80)
    print("✅ 测试完成！")