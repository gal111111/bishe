# -*- coding: utf-8 -*-
"""
数据处理模块 - 处理爬取的CSV数据
包括数据合并、清洗、格式转换等功能
"""
import os
import sys
import json
import csv
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

class DataProcessor:
    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.raw_data_dir = os.path.join(self.project_root, "data", "raw")
        self.merged_data_path = os.path.join(self.project_root, "data", "merged_all_platform.csv")
        self.cleaned_data_path = os.path.join(self.project_root, "data", "cleaned_all_data.csv")
        self.analysis_result_path = os.path.join(self.project_root, "data", "analysis_result.json")
    
    def load_platform_data(self, platform: str, keyword: str = "上海迪士尼") -> pd.DataFrame:
        """加载单个平台的CSV数据"""
        try:
            # 查找平台的CSV文件
            for file_name in os.listdir(self.raw_data_dir):
                if file_name.startswith(f"{platform}_raw_{keyword}") and file_name.endswith(".csv"):
                    file_path = os.path.join(self.raw_data_dir, file_name)
                    print(f"📂 加载 {platform} 数据: {file_name}")
                    df = pd.read_csv(file_path, encoding='utf-8-sig')
                    print(f"   共 {len(df)} 条数据")
                    return df
            return pd.DataFrame()
        except Exception as e:
            print(f"⚠️  加载 {platform} 数据失败: {e}")
            return pd.DataFrame()
    
    def merge_all_platforms(self, keyword: str = "上海迪士尼") -> pd.DataFrame:
        """合并所有平台的数据"""
        print("=" * 80)
        print("📊 多平台数据合并")
        print("=" * 80)
        
        platforms = ["weibo", "zhihu", "tieba", "hupu"]
        all_data = []
        
        for platform in platforms:
            df = self.load_platform_data(platform, keyword)
            if not df.empty:
                # 确保平台字段存在
                if "platform" not in df.columns:
                    df["platform"] = platform
                all_data.append(df)
        
        if not all_data:
            print("⚠️  没有找到任何数据！")
            return pd.DataFrame()
        
        # 合并所有数据
        merged_df = pd.concat(all_data, ignore_index=True)
        print(f"\n📊 合并后总数据: {len(merged_df)} 条")
        
        # 保存合并数据
        os.makedirs(os.path.dirname(self.merged_data_path), exist_ok=True)
        merged_df.to_csv(self.merged_data_path, index=False, encoding='utf-8-sig')
        print(f"✅ 合并数据已保存: {self.merged_data_path}")
        
        # 统计各平台数据量
        platform_counts = merged_df["platform"].value_counts()
        print(f"\n📋 各平台数据统计:")
        for platform, count in platform_counts.items():
            print(f"  📱 {platform}: {count} 条")
        
        return merged_df
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """清洗数据"""
        print("\n" + "=" * 80)
        print("🧹 数据清洗")
        print("=" * 80)
        
        # 复制数据以避免修改原数据
        cleaned_df = df.copy()
        
        # 确保content列存在
        if "content" not in cleaned_df.columns:
            if "comment_content" in cleaned_df.columns:
                cleaned_df["content"] = cleaned_df["comment_content"]
            else:
                cleaned_df["content"] = ""
        
        # 清洗内容
        def clean_content(text):
            if pd.isna(text):
                return ""
            text = str(text)
            # 去除特殊字符和多余空白
            text = text.replace('\n', ' ').replace('\r', ' ')
            text = ' '.join(text.split())
            return text
        
        cleaned_df["content_clean"] = cleaned_df["content"].apply(clean_content)
        cleaned_df["content_length"] = cleaned_df["content_clean"].apply(len)
        
        # 过滤无效数据
        cleaned_df = cleaned_df[cleaned_df["content_length"] >= 10]
        print(f"\n📋 清洗后数据: {len(cleaned_df)} 条")
        print(f"   过滤掉 {len(df) - len(cleaned_df)} 条无效数据")
        
        # 保存清洗后的数据
        cleaned_df.to_csv(self.cleaned_data_path, index=False, encoding='utf-8-sig')
        print(f"✅ 清洗数据已保存: {self.cleaned_data_path}")
        
        return cleaned_df
    
    def analyze_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """分析数据"""
        print("\n" + "=" * 80)
        print("📈 数据分析")
        print("=" * 80)
        
        # 从情感分析模块导入分析函数
        try:
            from src.analysis.sentiment_analysis import analyze_dataframe
            analyzed_df = analyze_dataframe(df, preferred="snownlp")
            print(f"\n📊 情感分析完成: {len(analyzed_df)} 条数据")
        except Exception as e:
            print(f"⚠️  情感分析失败: {e}")
            analyzed_df = df
        
        # 统计情感分布
        sentiment_dist = []
        if "polarity_label" in analyzed_df.columns:
            sentiment_counts = analyzed_df["polarity_label"].value_counts()
            total = len(analyzed_df)
            for label, count in sentiment_counts.items():
                sentiment_dist.append({
                    "label": label,
                    "count": int(count),
                    "ratio": round(count / total, 4)
                })
        
        # 统计平台热度
        platform_heat = []
        if "platform" in analyzed_df.columns:
            platform_groups = analyzed_df.groupby("platform")
            for platform, group in platform_groups:
                platform_heat.append({
                    "platform": platform,
                    "like_total": int(group.get("like_count", 0).sum()),
                    "comment_total": int(group.get("comment_count", 0).sum()),
                    "post_total": len(group)
                })
        
        # 生成分析结果
        analysis_result = {
            "sentiment_dist": sentiment_dist,
            "platform_heat": platform_heat,
            "generate_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # 保存分析结果
        with open(self.analysis_result_path, "w", encoding="utf-8") as f:
            json.dump(analysis_result, f, ensure_ascii=False, indent=2)
        print(f"✅ 分析结果已保存: {self.analysis_result_path}")
        
        # 保存分析后的评论数据
        analyzed_comments_path = os.path.join(self.project_root, "data", "analyzed_comments.csv")
        if "polarity_label" in analyzed_df.columns:
            analyzed_df.to_csv(analyzed_comments_path, index=False, encoding='utf-8-sig')
            print(f"✅ 分析评论已保存: {analyzed_comments_path}")
        
        return analysis_result
    
    def run_full_process(self, keyword: str = "上海迪士尼"):
        """运行完整的数据处理流程"""
        print("=" * 80)
        print("🚀 开始完整数据处理流程")
        print("=" * 80)
        
        # 1. 合并数据
        merged_df = self.merge_all_platforms(keyword)
        if merged_df.empty:
            print("❌ 没有数据可处理")
            return
        
        # 2. 清洗数据
        cleaned_df = self.clean_data(merged_df)
        if cleaned_df.empty:
            print("❌ 清洗后没有有效数据")
            return
        
        # 3. 分析数据
        analysis_result = self.analyze_data(cleaned_df)
        
        print("\n" + "=" * 80)
        print("🎉 数据处理流程完成！")
        print("=" * 80)
        
        # 打印分析结果
        print("\n📋 分析结果摘要:")
        print("情感分布:")
        for item in analysis_result.get("sentiment_dist", []):
            print(f"  {item['label']}: {item['count']} 条 ({item['ratio']*100:.2f}%)")
        
        print("\n平台热度:")
        for item in analysis_result.get("platform_heat", []):
            print(f"  {item['platform']}: 帖子{item['post_total']}个, 评论{item['comment_total']}条")

def main():
    print("=" * 80)
    print("📊 数据处理模块 - 示例调用")
    print("=" * 80)
    
    processor = DataProcessor()
    processor.run_full_process()

if __name__ == "__main__":
    main()
