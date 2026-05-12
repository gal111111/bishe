# -*- coding: utf-8 -*-
"""
分析微博爬取数据的情感分析脚本
"""
import os
import sys
import pandas as pd

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.analysis.sentiment_analysis import analyze_dataframe, generate_ai_report

def main():
    # 读取爬取的数据
    csv_path = "src/data/raw/weibo_raw_上海迪士尼_20260418.csv"
    
    if not os.path.exists(csv_path):
        print(f"❌ 文件不存在: {csv_path}")
        return
    
    print(f"📊 读取数据文件: {csv_path}")
    df = pd.read_csv(csv_path)
    print(f"📋 原始数据条数: {len(df)}")
    
    # 分析数据
    print("\n🤖 开始情感分析...")
    df_analyzed = analyze_dataframe(df, preferred="snownlp")
    print(f"✅ 分析完成，有效评论条数: {len(df_analyzed)}")
    
    # 生成AI报告
    print("\n📝 生成分析报告...")
    report_df, aspect_df, absa_report_df, detailed_absa_df = generate_ai_report(df_analyzed)
    
    # 保存分析结果
    output_dir = "data/analysis"
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存分析后的数据
    analyzed_csv = os.path.join(output_dir, "weibo_analyzed_上海迪士尼_20260418.csv")
    df_analyzed.to_csv(analyzed_csv, index=False, encoding='utf-8-sig')
    print(f"✅ 分析数据已保存: {analyzed_csv}")
    
    # 保存报告数据
    report_csv = os.path.join(output_dir, "weibo_report_上海迪士尼_20260418.csv")
    report_df.to_csv(report_csv, index=False, encoding='utf-8-sig')
    print(f"✅ 报告数据已保存: {report_csv}")
    
    # 保存方面数据
    aspect_csv = os.path.join(output_dir, "weibo_aspect_上海迪士尼_20260418.csv")
    aspect_df.to_csv(aspect_csv, index=False, encoding='utf-8-sig')
    print(f"✅ 方面数据已保存: {aspect_csv}")
    
    # 保存ABSA数据
    absa_csv = os.path.join(output_dir, "weibo_absa_上海迪士尼_20260418.csv")
    absa_report_df.to_csv(absa_csv, index=False, encoding='utf-8-sig')
    print(f"✅ ABSA数据已保存: {absa_csv}")
    
    # 保存详细ABSA数据
    detailed_absa_csv = os.path.join(output_dir, "weibo_detailed_absa_上海迪士尼_20260418.csv")
    detailed_absa_df.to_csv(detailed_absa_csv, index=False, encoding='utf-8-sig')
    print(f"✅ 详细ABSA数据已保存: {detailed_absa_csv}")
    
    # 打印分析结果摘要
    print("\n📈 分析结果摘要:")
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
    
    print("\n✅ 分析完成！")

if __name__ == "__main__":
    main()
