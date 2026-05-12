# -*- coding: utf-8 -*-
"""
高级数据清洗模块
提供更严格的数据质量过滤和情感平衡调整
"""
import os
import sys
import re
import json
import pandas as pd
from typing import List, Dict, Any, Set, Tuple
from collections import Counter

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class AdvancedDataCleaner:
    """高级数据清洗器"""
    
    def __init__(self):
        # 内容长度阈值
        self.min_content_length = 15
        self.ideal_min_length = 30
        self.max_content_length = 500
        
        # 官方账号关键词
        self.official_keywords = [
            "度假区", "官方", "旗舰店", "公众号", "小程序",
            "旅游局", "文旅", "管委会", "管理处"
        ]
        
        # 营销内容关键词
        self.marketing_keywords = [
            "盛大启幕", "庆典", "生日", "十周年",
            "惊喜", "奇妙", "魔法", "神奇",
            "邀请", "等你来", "赶快", "快来"
        ]
        
        # 无意义内容模式
        self.meaningless_patterns = [
            r"^[\s\d\W]+$",  # 纯符号数字
            r"^[哈哈呵呵嘿嘿嘻嘻]+$",  # 纯笑声
            r"^[嗯嗯啊啊哦哦]+$",  # 纯语气词
            r"^[好的好的好的]+$",  # 重复词
            r"^[顶支持赞]+$",  # 纯支持词
            r"^[沙发板凳地板]+$",  # 纯占位词
            r"^[.。…]+$",  # 纯省略号
        ]
        
        # 简单评价词
        self.simple_words = [
            "好", "不错", "一般", "还行", "可以",
            "棒", "赞", "喜欢", "爱", "可爱",
            "期待", "想去", "想去了", "下次去"
        ]
        
        # 情感平衡目标
        self.target_positive_ratio = 0.5
        self.target_neutral_ratio = 0.3
        self.target_negative_ratio = 0.2
    
    def calculate_content_quality_score(self, content: str) -> Dict[str, Any]:
        """
        计算内容质量分数
        
        Returns:
            {
                "score": 0-100,
                "length_ok": bool,
                "has_detail": bool,
                "not_marketing": bool,
                "not_official": bool,
                "not_simple": bool,
                "not_repeated": bool
            }
        """
        score = 0
        content = content.strip()
        length = len(content)
        
        result = {
            "score": 0,
            "length_ok": False,
            "has_detail": False,
            "not_marketing": True,
            "not_official": True,
            "not_simple": True,
            "not_repeated": True
        }
        
        # 1. 长度检查
        if length >= self.min_content_length:
            result["length_ok"] = True
            score += 20
            if length >= self.ideal_min_length:
                score += 10
        
        # 2. 细节检查（包含标点符号或多个词语）
        if any(p in content for p in "，。！？,.!?") or len(content.split()) >= 3:
            result["has_detail"] = True
            score += 20
        
        # 3. 营销内容检查
        for keyword in self.marketing_keywords:
            if keyword in content:
                result["not_marketing"] = False
                score -= 20
                break
        
        # 4. 官方账号检查
        for keyword in self.official_keywords:
            if keyword in content:
                result["not_official"] = False
                score -= 10
                break
        
        # 5. 简单评价检查
        is_simple = len(content) < 20 and any(word == content or word + "!" == content or word + "。" == content 
                                              for word in self.simple_words)
        if is_simple:
            result["not_simple"] = False
            score -= 15
        
        # 6. 重复词检查
        if self._has_repeated_words(content):
            result["not_repeated"] = False
            score -= 15
        
        # 7. 无意义内容检查
        if self._is_meaningless(content):
            score = 0
        
        result["score"] = max(0, min(100, score))
        return result
    
    def _has_repeated_words(self, content: str) -> bool:
        """检查是否有重复词模式"""
        if len(content) < 5:
            return False
        
        # 检查连续重复字符
        for i in range(len(content) - 2):
            if content[i] == content[i+1] == content[i+2]:
                return True
        
        return False
    
    def _is_meaningless(self, content: str) -> bool:
        """检查是否为无意义内容"""
        for pattern in self.meaningless_patterns:
            if re.match(pattern, content):
                return True
        
        # 检查长度太短
        if len(content.strip()) < 3:
            return True
        
        return False
    
    def filter_low_quality_data(self, df: pd.DataFrame, 
                                 min_quality_score: int = 40) -> pd.DataFrame:
        """
        过滤低质量数据
        
        Args:
            df: 原始DataFrame
            min_quality_score: 最小质量分数
            
        Returns:
            过滤后的DataFrame
        """
        print(f"\n🔍 开始过滤低质量数据...")
        print(f"   原始数据: {len(df)} 条")
        
        if len(df) == 0:
            return df
        
        # 计算每条数据的质量分数
        quality_scores = []
        filtered_indices = []
        
        for idx, row in df.iterrows():
            content = str(row.get("content", "") or row.get("comment_content", ""))
            quality = self.calculate_content_quality_score(content)
            quality_scores.append(quality)
            
            if quality["score"] >= min_quality_score:
                filtered_indices.append(idx)
        
        # 创建质量分数列
        df = df.copy()
        df["quality_score"] = [q["score"] for q in quality_scores]
        df["is_quality_ok"] = [q["score"] >= min_quality_score for q in quality_scores]
        
        # 过滤数据
        filtered_df = df.loc[filtered_indices].copy()
        
        print(f"   质量分数 >= {min_quality_score}: {len(filtered_df)} 条")
        print(f"   过滤掉: {len(df) - len(filtered_df)} 条")
        
        return filtered_df
    
    def balance_sentiment_distribution(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        平衡情感分布
        
        确保正面、中性、负面评论都有合理的比例
        """
        print(f"\n⚖️  平衡情感分布...")
        
        if len(df) == 0:
            return df
        
        if "polarity_label" not in df.columns:
            print("   警告: 没有polarity_label列，跳过平衡")
            return df
        
        # 统计当前分布
        sentiment_counts = df["polarity_label"].value_counts()
        total = len(df)
        
        print(f"   当前分布:")
        for sentiment, count in sentiment_counts.items():
            print(f"     {sentiment}: {count} ({count/total*100:.1f}%)")
        
        # 计算目标数量
        target_counts = {
            "积极": int(total * self.target_positive_ratio),
            "中性": int(total * self.target_neutral_ratio),
            "消极": int(total * self.target_negative_ratio)
        }
        
        # 调整目标数量以匹配总数
        total_target = sum(target_counts.values())
        if total_target != total:
            diff = total - total_target
            target_counts["积极"] += diff
        
        # 采样
        balanced_dfs = []
        
        for sentiment in ["积极", "中性", "消极"]:
            sentiment_df = df[df["polarity_label"] == sentiment]
            target_count = target_counts.get(sentiment, 0)
            
            if len(sentiment_df) > target_count:
                # 数据太多，随机采样
                # 优先保留质量高的
                if "quality_score" in sentiment_df.columns:
                    sentiment_df = sentiment_df.sort_values("quality_score", ascending=False)
                sampled = sentiment_df.head(target_count)
            else:
                # 数据不够，用全部
                sampled = sentiment_df
            
            balanced_dfs.append(sampled)
        
        balanced_df = pd.concat(balanced_dfs, ignore_index=True)
        
        # 重新统计
        new_counts = balanced_df["polarity_label"].value_counts()
        print(f"   平衡后分布:")
        for sentiment, count in new_counts.items():
            print(f"     {sentiment}: {count} ({count/len(balanced_df)*100:.1f}%)")
        
        return balanced_df
    
    def deduplicate_advanced(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        高级去重（放宽条件，保留更多数据）
        """
        print(f"\n🔄 高级去重...")
        print(f"   去重前: {len(df)} 条")
        
        if len(df) == 0:
            return df
        
        # 首先基于内容完全去重
        content_col = "content" if "content" in df.columns else "comment_content"
        
        # 标准化内容（更宽松的标准化）
        df = df.copy()
        
        # 只去掉完全相同的内容，不去除语义相似的
        deduplicated = df.drop_duplicates(subset=[content_col], keep="first")
        
        print(f"   去重后: {len(deduplicated)} 条")
        print(f"   去除: {len(df) - len(deduplicated)} 条")
        
        return deduplicated
    
    def _normalize_content(self, content: str) -> str:
        """标准化内容用于去重"""
        content = str(content).lower()
        
        # 移除标点符号
        content = re.sub(r'[^\w\s]', '', content)
        
        # 移除多余空白
        content = re.sub(r'\s+', ' ', content).strip()
        
        return content
    
    def clean_data_pipeline(self, df: pd.DataFrame, 
                           min_quality_score: int = 40,
                           balance_sentiment: bool = True) -> pd.DataFrame:
        """
        完整的数据清洗管道
        
        Args:
            df: 原始DataFrame
            min_quality_score: 最小质量分数
            balance_sentiment: 是否平衡情感分布
            
        Returns:
            清洗后的DataFrame
        """
        print("=" * 80)
        print("🧹 高级数据清洗管道")
        print("=" * 80)
        
        if len(df) == 0:
            print("⚠️  没有数据需要清洗！")
            return df
        
        print(f"📊 输入数据: {len(df)} 条")
        
        # 1. 高级去重
        df = self.deduplicate_advanced(df)
        
        # 2. 过滤低质量数据
        df = self.filter_low_quality_data(df, min_quality_score)
        
        # 3. 平衡情感分布（如果有情感标签）
        if balance_sentiment and "polarity_label" in df.columns:
            df = self.balance_sentiment_distribution(df)
        
        print(f"\n✅ 清洗完成: {len(df)} 条高质量数据")
        print("=" * 80)
        
        return df
    
    def generate_quality_report(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        生成数据质量报告
        """
        report = {
            "total_records": len(df),
            "content_length_stats": {},
            "quality_score_stats": {},
            "sentiment_distribution": {}
        }
        
        if len(df) == 0:
            return report
        
        # 内容长度统计
        content_col = "content" if "content" in df.columns else "comment_content"
        lengths = df[content_col].astype(str).apply(len)
        report["content_length_stats"] = {
            "mean": float(lengths.mean()),
            "median": float(lengths.median()),
            "min": int(lengths.min()),
            "max": int(lengths.max()),
            "std": float(lengths.std()) if len(lengths) > 1 else 0
        }
        
        # 质量分数统计
        if "quality_score" in df.columns:
            scores = df["quality_score"]
            report["quality_score_stats"] = {
                "mean": float(scores.mean()),
                "median": float(scores.median()),
                "min": int(scores.min()),
                "max": int(scores.max())
            }
        
        # 情感分布
        if "polarity_label" in df.columns:
            report["sentiment_distribution"] = df["polarity_label"].value_counts().to_dict()
        
        return report


def main():
    """示例使用"""
    print("=" * 80)
    print("🧹 高级数据清洗器 - 示例")
    print("=" * 80)
    
    # 创建一些示例数据
    sample_data = [
        {"content": "好", "platform": "weibo"},
        {"content": "上海迪士尼排队太久了，排了3个小时才玩到一个项目，服务态度也不好，建议大家避开高峰期去。", "platform": "zhihu"},
        {"content": "可爱", "platform": "weibo"},
        {"content": "上海迪士尼10岁生日庆典盛大启幕，快来体验！", "platform": "weibo"},
        {"content": "设施维护不错，卫生状况也很好，员工态度热情，值得推荐。", "platform": "tieba"},
        {"content": "好的好的好的", "platform": "hupu"},
        {"content": "餐饮价格有点贵，但是味道还可以，环境也不错。", "platform": "zhihu"},
    ]
    
    df = pd.DataFrame(sample_data)
    print(f"\n📊 示例数据: {len(df)} 条")
    
    cleaner = AdvancedDataCleaner()
    
    # 测试质量评分
    print("\n🔍 质量评分测试:")
    for idx, row in df.iterrows():
        content = row["content"]
        quality = cleaner.calculate_content_quality_score(content)
        print(f"[{idx+1}] {content[:30]}...")
        print(f"    分数: {quality['score']}")
        print(f"    通过: {quality['score'] >= 40}")
    
    # 测试完整管道
    cleaned_df = cleaner.clean_data_pipeline(df, min_quality_score=40)
    
    print(f"\n✅ 清洗后数据: {len(cleaned_df)} 条")
    print("\n📋 清洗后内容:")
    for idx, row in cleaned_df.iterrows():
        print(f"[{idx+1}] {row['content']}")


if __name__ == "__main__":
    main()
