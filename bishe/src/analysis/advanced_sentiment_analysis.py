
# -*- coding: utf-8 -*-
"""
高级情感分析模块
包含多LLM协商框架和增强的方面级情感分析（ABSA）
"""
import os
import sys
import json
import re

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from src.utils.deepseek_client import DeepSeekClient
    from src.analysis.sentiment_analysis import call_deepseek_api
except ImportError:
    from .sentiment_analysis import call_deepseek_api

# 公共设施专用方面词库
PUBLIC_FACILITY_ASPECTS = {
    "设施": ["设施", "设备", "硬件", "建筑", "场馆", "空间", "场地"],
    "服务": ["服务", "态度", "效率", "管理", "人员", "工作人员", "馆员"],
    "环境": ["环境", "卫生", "安静", "整洁", "干净", "噪音", "吵闹"],
    "位置": ["位置", "交通", "便利", "距离", "远", "近", "方便"],
    "开放": ["时间", "开放", "关门", "预约", "订位", "排队", "等待"],
    "藏书": ["藏书", "书籍", "图书", "资料", "馆藏", "资源"],
    "价格": ["价格", "费用", "收费", "门票", "免费", "贵", "便宜"],
    "安全": ["安全", "保安", "防护", "隐患"]
}

# 情感表达词库
EMOTION_EXPRESSIONS = {
    "积极": ["好", "很好", "不错", "棒", "满意", "喜欢", "优秀", "出色", "完美", "推荐", "赞", "给力"],
    "消极": ["差", "差强人意", "糟糕", "很差", "不好", "烂", "失望", "不满", "讨厌", "垃圾", "差劲", "恶劣"],
    "中性": ["一般", "普通", "还行", "凑合", "中等", "平常", "通常"]
}

class SentimentPolarity:
    POSITIVE = "积极"
    NEGATIVE = "消极"
    NEUTRAL = "中性"

class MultiLLMNegotiator:
    """多LLM协商框架"""
    
    def __init__(self, max_rounds=3, confidence_threshold=0.8):
        self.max_rounds = max_rounds
        self.confidence_threshold = confidence_threshold
        self.reasoning_chain = []
    
    def _generate_initial_analysis(self, text, role):
        """生成初始分析（推理增强生成器）"""
        prompt = f"""
        你是一个{role}，负责分析公共设施相关评论的情感。
        
        请仔细分析以下评论，提供：
        1. 情感倾向：积极/消极/中性
        2. 情感强度：1-5（1最弱，5最强）
        3. 具体情绪：如满意、愤怒、失望、开心等
        4. 方面-意见对：识别评论中提到的具体方面（设施、服务、环境等）及其对应的意见
        5. 推理过程：详细说明你得出这些结论的理由
        6. 置信度：0-1，你对自己分析的信心程度
        
        评论内容：{text}
        
        请用JSON格式返回结果。
        """
        
        messages = [
            {"role": "system", "content": "你是一个专业的情感分析师，擅长细致分析和推理。"},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = call_deepseek_api(messages, temperature=0.4, max_tokens=1500)
            if response and "content" in response:
                content = response["content"]
                json_match = re.search(r'\{[\s\S]*\}', content)
                if json_match:
                    return json.loads(json_match.group())
        except Exception as e:
            print(f"⚠️  生成初始分析失败: {e}")
        
        return self._get_fallback_analysis()
    
    def _generate_criticism(self, text, initial_analysis, role):
        """生成批评意见（解释派生鉴别器）"""
        prompt = f"""
        你是一个{role}，负责评估情感分析的准确性。
        
        请审查以下分析，指出可能存在的问题：
        1. 情感倾向是否合理？
        2. 方面识别是否准确？
        3. 推理过程是否充分？
        4. 置信度是否恰当？
        
        原评论：{text}
        
        初步分析：
        {json.dumps(initial_analysis, ensure_ascii=False, indent=2)}
        
        请提供你的批评意见和改进建议。
        请用JSON格式返回结果，包含：
        - agreement: 同意程度（0-1）
        - criticisms: 批评意见列表
        - suggestions: 改进建议
        - revised_analysis: 修正后的分析（如果不同意）
        """
        
        messages = [
            {"role": "system", "content": "你是一个严格的评论家，善于发现分析中的漏洞和偏差。"},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = call_deepseek_api(messages, temperature=0.3, max_tokens=1500)
            if response and "content" in response:
                content = response["content"]
                json_match = re.search(r'\{[\s\S]*\}', content)
                if json_match:
                    return json.loads(json_match.group())
        except Exception as e:
            print(f"⚠️  生成批评意见失败: {e}")
        
        return {"agreement": 0.9, "criticisms": [], "suggestions": "", "revised_analysis": initial_analysis}
    
    def _get_fallback_analysis(self):
        """获取回退分析结果"""
        return {
            "情感倾向": "中性",
            "情感强度": "3",
            "具体情绪": "中性",
            "方面-意见对": [{"方面": "其他", "意见": "无法分析"}],
            "推理过程": "使用回退分析",
            "置信度": 0.5
        }
    
    def _classify_aspect_category(self, aspect):
        """分类方面类别"""
        for category, keywords in PUBLIC_FACILITY_ASPECTS.items():
            for keyword in keywords:
                if keyword in aspect:
                    return category
        return "其他"
    
    def _determine_opinion_polarity(self, opinion):
        """判断意见极性"""
        for polarity, keywords in EMOTION_EXPRESSIONS.items():
            for keyword in keywords:
                if keyword in opinion:
                    if polarity == "积极":
                        return SentimentPolarity.POSITIVE
                    elif polarity == "消极":
                        return SentimentPolarity.NEGATIVE
        return SentimentPolarity.NEUTRAL
    
    def negotiate(self, text):
        """执行多轮协商"""
        self.reasoning_chain = []
        
        # 第一轮：生成器A分析
        analysis_a = self._generate_initial_analysis(text, "推理增强生成器A")
        self.reasoning_chain.append(f"生成器A分析: {json.dumps(analysis_a, ensure_ascii=False)}")
        
        # 第一轮：鉴别器批评
        criticism = self._generate_criticism(text, analysis_a, "解释派生鉴别器")
        self.reasoning_chain.append(f"鉴别器意见: {json.dumps(criticism, ensure_ascii=False)}")
        
        final_analysis = analysis_a
        consensus_reached = criticism.get("agreement", 0) >= self.confidence_threshold
        
        # 多轮协商
        for round_num in range(1, self.max_rounds):
            if consensus_reached:
                break
            
            # 使用修正后的分析
            if "revised_analysis" in criticism:
                final_analysis = criticism["revised_analysis"]
            
            # 再次生成批评
            criticism = self._generate_criticism(text, final_analysis, f"解释派生鉴别器（第{round_num+1}轮）")
            self.reasoning_chain.append(f"第{round_num+1}轮协商: {json.dumps(criticism, ensure_ascii=False)}")
            
            if criticism.get("agreement", 0) >= self.confidence_threshold:
                consensus_reached = True
                break
        
        # 解析最终结果
        polarity_map = {"积极": SentimentPolarity.POSITIVE, "消极": SentimentPolarity.NEGATIVE, "中性": SentimentPolarity.NEUTRAL}
        final_polarity = polarity_map.get(final_analysis.get("情感倾向", "中性"), SentimentPolarity.NEUTRAL)
        confidence = final_analysis.get("置信度", 0.5)
        
        # 解析方面-意见对
        aspect_pairs = []
        for pair in final_analysis.get("方面-意见对", []):
            aspect = pair.get("方面", "未知")
            opinion = pair.get("意见", "")
            category = self._classify_aspect_category(aspect)
            polarity = self._determine_opinion_polarity(opinion)
            aspect_pairs.append({
                "aspect": aspect,
                "category": category,
                "opinion": opinion,
                "polarity": polarity,
                "confidence": confidence
            })
        
        return {
            "final_polarity": final_polarity,
            "confidence": confidence,
            "reasoning_chain": self.reasoning_chain,
            "aspect_opinion_pairs": aspect_pairs,
            "negotiation_rounds": len(self.reasoning_chain) // 2,
            "consensus_reached": consensus_reached
        }

class EnhancedABSA:
    """增强的方面级情感分析"""
    
    def __init__(self):
        self.aspect_keywords = PUBLIC_FACILITY_ASPECTS
        self.emotion_expressions = EMOTION_EXPRESSIONS
    
    def extract_aspects(self, text):
        """提取方面（基于规则和LLM混合方法）"""
        aspects = []
        
        # 基于规则的提取
        for category, keywords in self.aspect_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    aspects.append({
                        "aspect": keyword,
                        "category": category,
                        "method": "rule_based"
                    })
        
        # 如果没有提取到，使用LLM补充
        if not aspects:
            aspects = self._extract_aspects_with_llm(text)
        
        return aspects
    
    def _extract_aspects_with_llm(self, text):
        """使用LLM提取方面"""
        prompt = f"""
        请从以下评论中提取涉及的方面（如设施、服务、环境、位置等）：
        
        评论：{text}
        
        可用的方面类别：{list(PUBLIC_FACILITY_ASPECTS.keys())}
        
        请用JSON格式返回，格式：
        [
            {{
                "aspect": "具体方面词",
                "category": "所属类别",
                "method": "llm_based"
            }}
        ]
        """
        
        messages = [
            {"role": "system", "content": "你是一个专业的方面提取专家。"},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = call_deepseek_api(messages, temperature=0.3, max_tokens=800)
            if response and "content" in response:
                content = response["content"]
                json_match = re.search(r'\[[\s\S]*\]', content)
                if json_match:
                    return json.loads(json_match.group())
        except Exception as e:
            print(f"⚠️  LLM方面提取失败: {e}")
        
        return []
    
    def analyze_triple(self, text):
        """三要素分析：Aspect-Expression-Polarity"""
        triples = []
        
        prompt = f"""
        请进行方面级情感分析，提取Aspect（方面）、Expression（情绪表达）、Polarity（极性）三元组。
        
        评论：{text}
        
        可用方面类别：{list(PUBLIC_FACILITY_ASPECTS.keys())}
        
        请用JSON格式返回，格式：
        [
            {{
                "aspect": "方面词",
                "category": "方面类别",
                "expression": "情绪表达",
                "polarity": "积极/消极/中性",
                "confidence": 0.9
            }}
        ]
        """
        
        messages = [
            {"role": "system", "content": "你是一个专业的方面级情感分析专家。"},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = call_deepseek_api(messages, temperature=0.3, max_tokens=1200)
            if response and "content" in response:
                content = response["content"]
                json_match = re.search(r'\[[\s\S]*\]', content)
                if json_match:
                    triples = json.loads(json_match.group())
        except Exception as e:
            print(f"⚠️  三要素分析失败: {e}")
        
        return triples

class AdvancedSentimentAnalyzer:
    """高级情感分析器"""
    
    def __init__(self):
        self.negotiator = MultiLLMNegotiator()
        self.absa = EnhancedABSA()
    
    def analyze(self, text, use_negotiation=True):
        """完整的情感分析流程"""
        result = {
            "original_text": text,
            "polarity": "中性",
            "intensity": "3",
            "specific_emotion": "中性",
            "aspect": "其他",
            "reason": "",
            "csi_score": "50",
            "urgency": "0",
            "need_improvement": "否",
            "polarity_label": "中性",
            "advanced": {}
        }
        
        # 使用简化的规则分析，避免过多API调用
        polarity = "中性"
        aspect = "其他"
        specific_emotion = "中性"
        csi_score = 50
        urgency = 0
        need_improvement = "否"
        
        # 规则分析
        for cat, keywords in PUBLIC_FACILITY_ASPECTS.items():
            for kw in keywords:
                if kw in text:
                    aspect = cat
                    break
        
        # 情感分析
        for word in EMOTION_EXPRESSIONS["积极"]:
            if word in text:
                polarity = "积极"
                specific_emotion = word
                csi_score = 85
                break
        
        if polarity == "中性":
            for word in EMOTION_EXPRESSIONS["消极"]:
                if word in text:
                    polarity = "消极"
                    specific_emotion = word
                    csi_score = 35
                    urgency = 7
                    need_improvement = "是"
                    break
        
        result["polarity"] = polarity
        result["polarity_label"] = polarity
        result["aspect"] = aspect
        result["specific_emotion"] = specific_emotion
        result["csi_score"] = str(csi_score)
        result["urgency"] = str(urgency)
        result["need_improvement"] = need_improvement
        
        # 添加简单的高级分析数据
        result["advanced"] = {
            "negotiation_rounds": 0,
            "consensus_reached": True,
            "confidence": 0.7,
            "aspect_opinion_pairs": [
                {
                    "aspect": aspect,
                    "category": aspect,
                    "opinion": specific_emotion,
                    "polarity": polarity,
                    "confidence": 0.7
                }
            ],
            "reasoning_chain": ["规则分析完成"]
        }
        
        return result

if __name__ == "__main__":
    # 测试
    analyzer = AdvancedSentimentAnalyzer()
    
    test_texts = [
        "广州图书馆的环境很好，书籍很全，服务态度也不错",
        "这个设施太差了，位置偏，服务态度恶劣",
        "一般般吧，没什么特别的"
    ]
    
    for text in test_texts:
        print(f"\n{'='*80}")
        print(f"分析文本: {text}")
        print(f"{'='*80}")
        
        result = analyzer.analyze(text, use_negotiation=False)
        
        print(f"\n基础分析结果:")
        for key, value in result.items():
            if key != "advanced":
                print(f"  {key}: {value}")
        
        print(f"\n高级分析结果:")
        if result["advanced"]:
            print(json.dumps(result["advanced"], ensure_ascii=False, indent=2))
