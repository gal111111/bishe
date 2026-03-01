
# -*- coding: utf-8 -*-
"""
可解释性模块
包含SHAP值分析和推理链可视化
"""
import os
import sys
import json
import re
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

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

class SHAPFallbackAnalyzer:
    """简化的SHAP回退分析器（基于词频和情感词典）"""
    
    def __init__(self):
        self.positive_words = EMOTION_EXPRESSIONS["积极"]
        self.negative_words = EMOTION_EXPRESSIONS["消极"]
        self.negation_words = ["不", "没", "无", "非", "别", "勿", "未", "不要"]
    
    def _tokenize(self, text):
        """简单分词"""
        return list(text)
    
    def analyze(self, text, polarity):
        """分析词贡献度"""
        words = self._tokenize(text)
        contributions = []
        
        for i, word in enumerate(words):
            contribution = 0.0
            word_polarity = "中性"
            
            is_negated = False
            for j in range(max(0, i - 3), i):
                if words[j] in self.negation_words:
                    is_negated = True
                    break
            
            if word in self.positive_words:
                if is_negated:
                    contribution = -0.8
                    word_polarity = "消极"
                else:
                    contribution = 0.8
                    word_polarity = "积极"
            elif word in self.negative_words:
                if is_negated:
                    contribution = 0.6
                    word_polarity = "积极"
                else:
                    contribution = -0.8
                    word_polarity = "消极"
            elif len(word) &gt; 1:
                contribution = 0.1 * (1 if polarity == "积极" else -1)
            
            if abs(contribution) &gt; 0.05:
                contributions.append({
                    "word": word,
                    "contribution": contribution,
                    "polarity": word_polarity,
                    "position": i
                })
        
        contributions.sort(key=lambda x: abs(x["contribution"]), reverse=True)
        return contributions

class ReasoningChainVisualizer:
    """推理链可视化器"""
    
    def __init__(self):
        pass
    
    def parse_reasoning_chain(self, reasoning_chain):
        """解析推理链"""
        steps = []
        
        for i, content in enumerate(reasoning_chain):
            agent = "未知"
            action = "分析"
            
            if "生成器" in content:
                agent = "推理增强生成器"
                action = "生成分析"
            elif "鉴别器" in content:
                agent = "解释派生鉴别器"
                action = "评估批评"
            elif "协商" in content:
                agent = "协商模块"
                action = "多轮协商"
            
            steps.append({
                "step_number": i + 1,
                "agent": agent,
                "action": action,
                "content": content[:200],
                "timestamp": ""
            })
        
        return steps

class ExplainabilityReportGenerator:
    """可解释性报告生成器"""
    
    def __init__(self):
        self.shap_analyzer = SHAPFallbackAnalyzer()
        self.reasoning_visualizer = ReasoningChainVisualizer()
    
    def generate_word_contribution_report(self, text, analysis_result):
        """生成词贡献报告"""
        polarity = analysis_result.get("polarity", "中性")
        contributions = self.shap_analyzer.analyze(text, polarity)
        
        total_positive = sum(c["contribution"] for c in contributions if c["contribution"] &gt; 0)
        total_negative = sum(c["contribution"] for c in contributions if c["contribution"] &lt; 0)
        
        return {
            "text": text,
            "polarity": polarity,
            "word_contributions": contributions,
            "summary": {
                "total_positive_contribution": total_positive,
                "total_negative_contribution": total_negative,
                "net_contribution": total_positive + total_negative,
                "key_positive_words": [c["word"] for c in contributions if c["contribution"] &gt; 0.5][:5],
                "key_negative_words": [c["word"] for c in contributions if c["contribution"] &lt; -0.5][:5]
            }
        }
    
    def generate_reasoning_report(self, advanced_data):
        """生成推理链报告"""
        reasoning_chain = advanced_data.get("reasoning_chain", [])
        
        if not reasoning_chain:
            return {"has_reasoning": False}
        
        steps = self.reasoning_visualizer.parse_reasoning_chain(reasoning_chain)
        
        return {
            "has_reasoning": True,
            "steps": steps,
            "metadata": {
                "total_rounds": advanced_data.get("negotiation_rounds", 0),
                "consensus_reached": advanced_data.get("consensus_reached", False),
                "confidence": advanced_data.get("confidence", 0.0)
            }
        }
    
    def generate_aspect_opinion_report(self, advanced_data):
        """生成方面-意见对报告"""
        aspect_pairs = advanced_data.get("aspect_opinion_pairs", [])
        
        if not aspect_pairs:
            return {"has_aspect_pairs": False}
        
        category_counts = {}
        polarity_counts = {}
        
        for pair in aspect_pairs:
            category = pair.get("category", "其他")
            polarity = pair.get("polarity", "中性")
            category_counts[category] = category_counts.get(category, 0) + 1
            polarity_counts[polarity] = polarity_counts.get(polarity, 0) + 1
        
        dominant_category = max(category_counts.items(), key=lambda x: x[1])[0] if category_counts else None
        
        return {
            "has_aspect_pairs": True,
            "aspect_pairs": aspect_pairs,
            "category_distribution": category_counts,
            "polarity_distribution": polarity_counts,
            "dominant_category": dominant_category
        }
    
    def generate_comprehensive_report(self, text, analysis_result):
        """生成综合可解释性报告"""
        report = "# 情感分析可解释性报告\n\n"
        
        report += "## 1. 基础分析结果\n\n"
        report += f"- **原始文本**: {text}\n"
        report += f"- **情感倾向**: {analysis_result.get('polarity', '未知')}\n"
        report += f"- **CSI分数**: {analysis_result.get('csi_score', 'N/A')}\n"
        report += f"- **主要方面**: {analysis_result.get('aspect', '未知')}\n"
        report += f"- **具体情绪**: {analysis_result.get('specific_emotion', '未知')}\n\n"
        
        advanced = analysis_result.get("advanced", {})
        
        if advanced:
            word_report = self.generate_word_contribution_report(text, analysis_result)
            if word_report["word_contributions"]:
                report += "## 2. 词贡献度分析\n\n"
                report += "### 2.1 关键贡献词\n\n"
                
                positive_words = [w for w in word_report["word_contributions"] if w["contribution"] &gt; 0]
                negative_words = [w for w in word_report["word_contributions"] if w["contribution"] &lt; 0]
                
                if positive_words:
                    report += "**积极贡献词**:\n"
                    for w in positive_words[:5]:
                        report += f"- {w['word']}: {w['contribution']:.2f}\n"
                    report += "\n"
                
                if negative_words:
                    report += "**消极贡献词**:\n"
                    for w in negative_words[:5]:
                        report += f"- {w['word']}: {w['contribution']:.2f}\n"
                    report += "\n"
                
                summary = word_report["summary"]
                report += "### 2.2 贡献摘要\n\n"
                report += f"- 总积极贡献: {summary['total_positive_contribution']:.2f}\n"
                report += f"- 总消极贡献: {summary['total_negative_contribution']:.2f}\n"
                report += f"- 净贡献: {summary['net_contribution']:.2f}\n\n"
            
            reasoning_report = self.generate_reasoning_report(advanced)
            if reasoning_report.get("has_reasoning"):
                report += "## 3. 推理链分析\n\n"
                report += f"- **协商轮数**: {reasoning_report['metadata']['total_rounds']}\n"
                report += f"- **是否达成共识**: {'是' if reasoning_report['metadata']['consensus_reached'] else '否'}\n"
                report += f"- **最终置信度**: {reasoning_report['metadata']['confidence']:.2f}\n\n"
                
                report += "### 3.1 推理步骤\n\n"
                for step in reasoning_report["steps"]:
                    report += f"**步骤 {step['step_number']}**: {step['agent']} - {step['action']}\n"
                    report += f"&gt; {step['content']}\n\n"
            
            aspect_report = self.generate_aspect_opinion_report(advanced)
            if aspect_report.get("has_aspect_pairs"):
                report += "## 4. 方面-意见对分析\n\n"
                report += "### 4.1 方面分布\n\n"
                for category, count in aspect_report["category_distribution"].items():
                    report += f"- {category}: {count}次\n"
                report += "\n"
                
                report += "### 4.2 极性分布\n\n"
                for polarity, count in aspect_report["polarity_distribution"].items():
                    report += f"- {polarity}: {count}次\n"
                report += "\n"
                
                report += "### 4.3 详细方面-意见对\n\n"
                for pair in aspect_report["aspect_pairs"]:
                    report += f"- **方面**: {pair['aspect']} ({pair['category']})\n"
                    report += f"  - **意见**: {pair['opinion']}\n"
                    report += f"  - **极性**: {pair['polarity']}\n"
                    report += f"  - **置信度**: {pair.get('confidence', 0):.2f}\n\n"
        
        report += "---\n\n"
        report += "*本报告基于简化的可解释性分析方法。*\n"
        
        return report

if __name__ == "__main__":
    print("=" * 80)
    print("测试可解释性模块")
    print("=" * 80)
    
    generator = ExplainabilityReportGenerator()
    
    test_text = "广州图书馆的环境很好，书籍很全，但是服务态度有点差"
    test_analysis = {
        "polarity": "中性",
        "csi_score": "65",
        "aspect": "环境",
        "specific_emotion": "满意",
        "advanced": {
            "negotiation_rounds": 2,
            "consensus_reached": True,
            "confidence": 0.85,
            "reasoning_chain": [
                "生成器A分析: 发现正面和负面情绪",
                "鉴别器意见: 同意，但需要更仔细分析",
                "第2轮协商: 达成最终共识"
            ],
            "aspect_opinion_pairs": [
                {"aspect": "环境", "category": "环境", "opinion": "很好", "polarity": "积极", "confidence": 0.9},
                {"aspect": "书籍", "category": "藏书", "opinion": "很全", "polarity": "积极", "confidence": 0.85},
                {"aspect": "服务态度", "category": "服务", "opinion": "有点差", "polarity": "消极", "confidence": 0.88}
            ]
        }
    }
    
    print(f"\n测试文本: {test_text}")
    print(f"\n生成报告...")
    
    report = generator.generate_comprehensive_report(test_text, test_analysis)
    
    print(f"\n{'='*80}")
    print("可解释性报告:")
    print(f"{'='*80}")
    print(report)
