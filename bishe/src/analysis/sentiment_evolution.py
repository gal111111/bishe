# -*- coding: utf-8 -*-
"""
情感动态演化分析模块
分析舆情随时间的变化模式和趋势预测
"""
import os
import sys
import json
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict, Counter
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from src.analysis.timeseries_analysis import TimeSeriesAnalyzer
except ImportError:
    pass

class SentimentEvolutionAnalyzer:
    """情感动态演化分析器"""
    
    def __init__(self, output_dir: str = "data/viz"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.time_series_data = []
        self.evolution_patterns = []
    
    def prepare_time_series(self, df: pd.DataFrame, 
                           time_col: str = "create_time",
                           sentiment_col: str = "polarity_label",
                           csi_col: str = "csi_score",
                           content_col: str = "content",
                           time_window: str = "D") -> pd.DataFrame:
        """
        准备时间序列数据
        
        参数:
            df: 数据DataFrame
            time_col: 时间列名
            sentiment_col: 情感列名
            csi_col: CSI分数列名
            content_col: 内容列名
            time_window: 时间窗口 ('H'=小时, 'D'=天, 'W'=周)
            
        返回:
            时间序列DataFrame
        """
        df = df.copy()
        
        # 确保时间列存在
        if time_col not in df.columns:
            df[time_col] = pd.date_range(
                start=datetime.now() - timedelta(days=30),
                periods=len(df),
                freq="H"
            )
        
        # 转换时间列
        df[time_col] = pd.to_datetime(df[time_col], errors='coerce')
        df = df.dropna(subset=[time_col])
        
        # 按时间排序
        df = df.sort_values(time_col)
        
        # 设置时间索引
        df = df.set_index(time_col)
        
        # 重采样
        resampled = df.resample(time_window).agg({
            sentiment_col: lambda x: x.value_counts().to_dict() if len(x) > 0 else {},
            csi_col: ['mean', 'std', 'count'],
            content_col: 'count'
        })
        
        # 展平列名
        resampled.columns = ['_'.join(col).strip() if isinstance(col, tuple) else col for col in resampled.columns.values]
        
        return resampled
    
    def detect_evolution_phases(self, df: pd.DataFrame, 
                               csi_col: str = "csi_score_mean",
                               threshold: float = 5.0) -> List[Dict[str, Any]]:
        """
        检测演化阶段
        
        参数:
            df: 时间序列DataFrame
            csi_col: CSI分数列名
            threshold: 变化阈值
            
        返回:
            演化阶段列表
        """
        phases = []
        
        if len(df) < 2:
            return phases
        
        csi_values = df[csi_col].values
        dates = df.index
        
        # 计算变化率
        changes = np.diff(csi_values)
        
        current_phase = {
            "start_date": dates[0],
            "end_date": dates[0],
            "start_csi": csi_values[0],
            "end_csi": csi_values[0],
            "trend": "stable",
            "magnitude": 0.0
        }
        
        for i in range(1, len(df)):
            change = changes[i-1] if i-1 < len(changes) else 0
            
            if abs(change) > threshold:
                # 阶段结束
                current_phase["end_date"] = dates[i-1]
                current_phase["end_csi"] = csi_values[i-1]
                current_phase["magnitude"] = current_phase["end_csi"] - current_phase["start_csi"]
                
                if current_phase["magnitude"] > threshold:
                    current_phase["trend"] = "improving"
                elif current_phase["magnitude"] < -threshold:
                    current_phase["trend"] = "declining"
                
                phases.append(current_phase)
                
                # 新阶段开始
                current_phase = {
                    "start_date": dates[i],
                    "end_date": dates[i],
                    "start_csi": csi_values[i],
                    "end_csi": csi_values[i],
                    "trend": "stable",
                    "magnitude": 0.0
                }
        
        # 添加最后一个阶段
        current_phase["end_date"] = dates[-1]
        current_phase["end_csi"] = csi_values[-1]
        current_phase["magnitude"] = current_phase["end_csi"] - current_phase["start_csi"]
        
        if current_phase["magnitude"] > threshold:
            current_phase["trend"] = "improving"
        elif current_phase["magnitude"] < -threshold:
            current_phase["trend"] = "declining"
        
        phases.append(current_phase)
        
        return phases
    
    def analyze_sentiment_shift(self, df: pd.DataFrame, 
                               sentiment_col: str = "polarity_label",
                               window_size: int = 7) -> Dict[str, Any]:
        """
        分析情感转移
        
        参数:
            df: 原始数据DataFrame
            sentiment_col: 情感列名
            window_size: 窗口大小
            
        返回:
            情感转移分析结果
        """
        if len(df) < window_size:
            return {"message": "数据量不足"}
        
        sentiments = df[sentiment_col].tolist()
        
        # 构建转移矩阵
        transitions = defaultdict(Counter)
        sentiment_order = ["积极", "中性", "消极"]
        
        for i in range(len(sentiments) - 1):
            current = sentiments[i]
            next_sent = sentiments[i + 1]
            transitions[current][next_sent] += 1
        
        # 归一化转移矩阵
        transition_matrix = {}
        for current in sentiment_order:
            transition_matrix[current] = {}
            total = sum(transitions[current].values())
            for next_sent in sentiment_order:
                transition_matrix[current][next_sent] = transitions[current][next_sent] / total if total > 0 else 0
        
        # 计算窗口内的情感变化
        window_shifts = []
        for i in range(window_size, len(sentiments)):
            window = sentiments[i-window_size:i]
            pos_count = window.count("积极")
            neg_count = window.count("消极")
            neu_count = window.count("中性")
            
            window_shifts.append({
                "position": i,
                "positive_ratio": pos_count / window_size,
                "negative_ratio": neg_count / window_size,
                "neutral_ratio": neu_count / window_size,
                "dominant": max(
                    [("积极", pos_count), ("中性", neu_count), ("消极", neg_count)],
                    key=lambda x: x[1]
                )[0]
            })
        
        return {
            "transition_matrix": transition_matrix,
            "window_shifts": window_shifts,
            "sentiment_order": sentiment_order
        }
    
    def detect_emerging_topics(self, df: pd.DataFrame,
                               content_col: str = "content",
                               time_col: str = "create_time",
                               window_days: int = 7,
                               top_k: int = 10) -> Dict[str, Any]:
        """
        检测新兴话题
        
        参数:
            df: 数据DataFrame
            content_col: 内容列名
            time_col: 时间列名
            window_days: 窗口天数
            top_k: 返回前k个话题
            
        返回:
            新兴话题分析结果
        """
        df = df.copy()
        
        if time_col not in df.columns:
            df[time_col] = pd.date_range(
                start=datetime.now() - timedelta(days=60),
                periods=len(df),
                freq="H"
            )
        
        df[time_col] = pd.to_datetime(df[time_col], errors='coerce')
        df = df.dropna(subset=[time_col])
        
        # 分成两个时间段
        latest_time = df[time_col].max()
        cutoff_time = latest_time - timedelta(days=window_days)
        
        recent_df = df[df[time_col] >= cutoff_time]
        older_df = df[df[time_col] < cutoff_time]
        
        # 简单的关键词提取（基于高频词）
        def extract_keywords(texts):
            words = []
            for text in texts:
                # 简单分词（按空格和标点）
                text = str(text)
                # 提取中文词（2字以上）
                import re
                chinese_words = re.findall(r'[\u4e00-\u9fa5]{2,}', text)
                words.extend(chinese_words)
            return Counter(words)
        
        recent_keywords = extract_keywords(recent_df[content_col].tolist())
        older_keywords = extract_keywords(older_df[content_col].tolist())
        
        # 计算增长率
        emerging_topics = []
        for keyword, recent_count in recent_keywords.most_common(top_k * 2):
            older_count = older_keywords.get(keyword, 0)
            
            if older_count == 0:
                growth_rate = float('inf') if recent_count > 0 else 0
            else:
                growth_rate = (recent_count - older_count) / older_count
            
            emerging_topics.append({
                "keyword": keyword,
                "recent_count": recent_count,
                "older_count": older_count,
                "growth_rate": growth_rate,
                "absolute_growth": recent_count - older_count
            })
        
        # 按增长率排序
        emerging_topics.sort(key=lambda x: x["growth_rate"], reverse=True)
        
        return {
            "emerging_topics": emerging_topics[:top_k],
            "recent_period": {
                "start": cutoff_time.strftime("%Y-%m-%d"),
                "end": latest_time.strftime("%Y-%m-%d"),
                "count": len(recent_df)
            },
            "older_period": {
                "end": cutoff_time.strftime("%Y-%m-%d"),
                "count": len(older_df)
            }
        }
    
    def get_evolution_insights(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        获取演化分析洞察
        
        参数:
            df: 原始数据DataFrame
            
        返回:
            演化洞察字典
        """
        # 1. 准备时间序列
        ts_data = self.prepare_time_series(df)
        
        # 2. 检测演化阶段
        phases = self.detect_evolution_phases(ts_data)
        
        # 3. 分析情感转移
        sentiment_shift = self.analyze_sentiment_shift(df)
        
        # 4. 检测新兴话题
        emerging_topics = self.detect_emerging_topics(df)
        
        return {
            "time_series": ts_data.reset_index().to_dict('records'),
            "evolution_phases": phases,
            "sentiment_shift": sentiment_shift,
            "emerging_topics": emerging_topics
        }
    
    def save_analysis(self, insights: Dict[str, Any], output_path: str):
        """
        保存分析结果
        
        参数:
            insights: 洞察结果
            output_path: 输出文件路径
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(insights, f, ensure_ascii=False, indent=2, default=str)
        print(f"✅ 情感演化分析已保存到: {output_path}")

if __name__ == "__main__":
    print("=" * 80)
    print("测试情感动态演化分析模块")
    print("=" * 80)
    
    # 创建测试数据
    np.random.seed(42)
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    
    test_data = {
        "create_time": dates,
        "content": [f"测试评论 {i}" for i in range(100)],
        "polarity_label": np.random.choice(["积极", "中性", "消极"], size=100, p=[0.4, 0.4, 0.2]),
        "csi_score": np.random.normal(70, 15, 100)
    }
    
    df = pd.DataFrame(test_data)
    
    # 添加一些趋势
    df.loc[50:, "csi_score"] += np.linspace(0, -20, 50)
    df.loc[70:, "polarity_label"] = np.random.choice(["积极", "中性", "消极"], size=30, p=[0.2, 0.4, 0.4])
    
    analyzer = SentimentEvolutionAnalyzer("test_output")
    
    print("\n正在分析情感演化...")
    insights = analyzer.get_evolution_insights(df)
    
    print("\n" + "=" * 80)
    print("演化阶段:")
    print("=" * 80)
    for i, phase in enumerate(insights["evolution_phases"], 1):
        print(f"\n阶段 {i}:")
        print(f"  时间: {phase['start_date'].strftime('%Y-%m-%d')} 至 {phase['end_date'].strftime('%Y-%m-%d')}")
        print(f"  趋势: {phase['trend']}")
        print(f"  CSI变化: {phase['start_csi']:.1f} → {phase['end_csi']:.1f} (变化: {phase['magnitude']:+.1f})")
    
    print("\n" + "=" * 80)
    print("新兴话题:")
    print("=" * 80)
    for topic in insights["emerging_topics"]["emerging_topics"][:5]:
        print(f"  {topic['keyword']}: 增长 {topic['absolute_growth']:+d} (增长率: {topic['growth_rate']:.1%})")
    
    # 保存测试
    os.makedirs("test_output", exist_ok=True)
    analyzer.save_analysis(insights, "test_output/sentiment_evolution.json")
    
    print("\n✅ 测试完成！")