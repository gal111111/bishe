# -*- coding: utf-8 -*-
"""
分析所有平台爬取的数据，生成综合分析报告
"""
import os
import sys
import pandas as pd

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.analysis.sentiment_analysis import analyze_dataframe, generate_ai_report

def analyze_platform_data(platform_name, file_path):
    """分析单个平台的数据"""
    print(f"\n{'='*60}")
    print(f"📊 分析 {platform_name} 数据")
    print(f"{'='*60}")
    
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return None, None
    
    print(f"读取数据文件: {file_path}")
    df = pd.read_csv(file_path)
    print(f"原始数据条数: {len(df)}")
    
    # 分析数据
    print("开始情感分析...")
    df_analyzed = analyze_dataframe(df, preferred="snownlp")
    print(f"分析完成，有效评论条数: {len(df_analyzed)}")
    
    # 生成AI报告
    print("生成分析报告...")
    report_df, aspect_df, absa_report_df, detailed_absa_df = generate_ai_report(df_analyzed)
    
    # 保存分析结果
    output_dir = "data/analysis"
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存分析后的数据
    analyzed_csv = os.path.join(output_dir, f"{platform_name}_analyzed_上海迪士尼_20260418.csv")
    df_analyzed.to_csv(analyzed_csv, index=False, encoding='utf-8-sig')
    print(f"分析数据已保存: {analyzed_csv}")
    
    # 保存报告数据
    report_csv = os.path.join(output_dir, f"{platform_name}_report_上海迪士尼_20260418.csv")
    report_df.to_csv(report_csv, index=False, encoding='utf-8-sig')
    print(f"报告数据已保存: {report_csv}")
    
    # 打印分析结果摘要
    print("\n分析结果摘要:")
    print(f"总评论数: {len(df_analyzed)}")
    
    if 'polarity_label' in df_analyzed.columns:
        polarity_counts = df_analyzed['polarity_label'].value_counts()
        print("\n情感分布:")
        for polarity, count in polarity_counts.items():
            percentage = (count / len(df_analyzed)) * 100
            print(f"{polarity}: {count} ({percentage:.1f}%)")
    
    if 'csi_score' in df_analyzed.columns:
        avg_csi = df_analyzed['csi_score'].mean()
        print(f"\n平均CSI满意度指数: {avg_csi:.1f}")
    
    return df_analyzed, report_df

def main():
    """主函数"""
    print("🔍 开始综合数据分析")
    print("="*80)
    
    # 分析微博数据
    weibo_file = "src/data/raw/weibo_raw_上海迪士尼_20260418.csv"
    weibo_analyzed, weibo_report = analyze_platform_data("weibo", weibo_file)
    
    # 分析贴吧数据
    tieba_file = "data/latest/tieba_raw_上海迪士尼_20260418.csv"
    tieba_analyzed, tieba_report = analyze_platform_data("tieba", tieba_file)
    
    # 生成综合报告
    print("\n" + "="*80)
    print("📋 综合分析报告")
    print("="*80)
    
    # 计算综合指标
    all_analyzed = []
    if weibo_analyzed is not None:
        all_analyzed.append(weibo_analyzed)
    if tieba_analyzed is not None:
        all_analyzed.append(tieba_analyzed)
    
    if all_analyzed:
        combined_df = pd.concat(all_analyzed, ignore_index=True)
        print(f"\n综合数据:")
        print(f"总评论数: {len(combined_df)}")
        
        if 'polarity_label' in combined_df.columns:
            polarity_counts = combined_df['polarity_label'].value_counts()
            print("\n综合情感分布:")
            for polarity, count in polarity_counts.items():
                percentage = (count / len(combined_df)) * 100
                print(f"{polarity}: {count} ({percentage:.1f}%)")
        
        if 'csi_score' in combined_df.columns:
            avg_csi = combined_df['csi_score'].mean()
            print(f"\n综合平均CSI满意度指数: {avg_csi:.1f}")
        
        # 保存综合分析结果
        combined_csv = os.path.join("data/analysis", "combined_analyzed_上海迪士尼_20260418.csv")
        combined_df.to_csv(combined_csv, index=False, encoding='utf-8-sig')
        print(f"\n综合分析数据已保存: {combined_csv}")
    
    print("\n" + "="*80)
    print("✅ 分析完成！")
    print("="*80)

if __name__ == "__main__":
    main()
