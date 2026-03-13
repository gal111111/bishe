
# -*- coding: utf-8 -*-
import os
import sys
import pandas as pd
import time

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.dirname(PROJECT_ROOT))

from src.analysis.sentiment_analysis import analyze_dataframe, preprocess_data, generate_ai_report
from src.visualization.dashboard import generate_visualizations
from src.analysis.academic_report import AcademicReportGenerator

DATA_DIR = os.path.join(PROJECT_ROOT, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
VIZ_DIR = os.path.join(DATA_DIR, "viz")

os.makedirs(VIZ_DIR, exist_ok=True)

print("=" * 80)
print("上海迪士尼全流程分析 - 基于已爬取数据")
print("=" * 80)

# 阶段1: 加载所有平台的原始数据
print("\n[阶段 1/5] 加载原始数据")
print("=" * 80)

all_data = []
platforms = ["weibo", "zhihu", "tieba", "hupu"]
date_str = "20260228"

for platform in platforms:
    file_name = f"{platform}_raw_上海迪士尼_{date_str}.csv"
    file_path = os.path.join(RAW_DIR, file_name)
    
    if os.path.exists(file_path):
        try:
            df = pd.read_csv(file_path, encoding="utf-8-sig")
            print(f"✅ 加载{platform}数据: {len(df)}条")
            all_data.append(df)
        except Exception as e:
            print(f"❌ 加载{platform}数据失败: {e}")
    else:
        print(f"⚠️  未找到{platform}文件: {file_name}")

if not all_data:
    print("\n❌ 未找到任何数据，退出")
    sys.exit(1)

df_merged = pd.concat(all_data, ignore_index=True)
merged_path = os.path.join(DATA_DIR, "merged_all_platform.csv")
df_merged.to_csv(merged_path, index=False, encoding="utf-8-sig")
print(f"\n✅ 合并数据完成，共{len(df_merged)}条")
print(f"   文件保存: {merged_path}")

# 阶段2: 数据预处理
print("\n[阶段 2/5] 数据预处理")
print("=" * 80)

df_processed = preprocess_data(df_merged)
print(f"✅ 数据预处理完成，有效数据: {len(df_processed)}条")

# 阶段3: AI情感分析
print("\n[阶段 3/5] AI情感分析")
print("=" * 80)

print("⏳ 开始分析... (使用SnowNLP快速分析)")
df_analyzed = analyze_dataframe(df_processed, preferred="snownlp")

analyzed_path = os.path.join(DATA_DIR, "analyzed_comments.csv")
df_analyzed.to_csv(analyzed_path, index=False, encoding="utf-8-sig")
print(f"✅ 情感分析完成")
print(f"   文件保存: {analyzed_path}")

# 显示简单统计
if 'polarity_label' in df_analyzed.columns:
    pos_count = len(df_analyzed[df_analyzed['polarity_label'] == '积极'])
    neu_count = len(df_analyzed[df_analyzed['polarity_label'] == '中性'])
    neg_count = len(df_analyzed[df_analyzed['polarity_label'] == '消极'])
    print(f"\n📊 情感统计:")
    print(f"   积极: {pos_count}条")
    print(f"   中性: {neu_count}条")
    print(f"   消极: {neg_count}条")

# 阶段4: 生成可视化
print("\n[阶段 4/5] 生成可视化")
print("=" * 80)

try:
    rep_df, asp_df, absa_df, detailed_absa_df = generate_ai_report(df_analyzed)
    generate_visualizations(df_analyzed, rep_df, asp_df, VIZ_DIR)
    print(f"✅ 可视化生成完成")
    print(f"   图表保存目录: {VIZ_DIR}")
except Exception as e:
    print(f"⚠️  可视化生成跳过: {e}")

# 阶段5: 生成学术报告
print("\n[阶段 5/5] 生成学术报告")
print("=" * 80)

try:
    report_gen = AcademicReportGenerator(df_analyzed, DATA_DIR)
    report_gen.generate_full_report()
    print(f"✅ 学术报告生成完成")
except Exception as e:
    print(f"⚠️  学术报告生成跳过: {e}")

print("\n" + "=" * 80)
print("🎉 全流程分析完成！")
print("=" * 80)
print(f"\n📁 生成的文件:")
print(f"   - 合并数据: {merged_path}")
print(f"   - 分析结果: {analyzed_path}")
print(f"   - 可视化图表: {VIZ_DIR}/")
print(f"   - 学术报告: {DATA_DIR}/academic_report_*.md")

