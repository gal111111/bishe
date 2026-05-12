
# -*- coding: utf-8 -*-
import os
import sys
import json
import csv
import pandas as pd
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

def load_platform_data(platform, keyword="上海迪士尼"):
    try:
        latest_data_dir = os.path.join(PROJECT_ROOT, "data", "latest")
        for file_name in os.listdir(latest_data_dir):
            if file_name.startswith("%s_raw_%s" % (platform, keyword)) and file_name.endswith(".csv"):
                file_path = os.path.join(latest_data_dir, file_name)
                print("Loading %s data: %s" % (platform, file_name))
                df = pd.read_csv(file_path, encoding='utf-8-sig')
                print("  Total %d records" % len(df))
                return df
        return pd.DataFrame()
    except Exception as e:
        print("Failed to load %s data: %s" % (platform, e))
        return pd.DataFrame()

def merge_all_platforms(keyword="上海迪士尼"):
    print("=" * 80)
    print("Merging data from multiple platforms")
    print("=" * 80)
    
    platforms = ["weibo", "zhihu", "tieba", "hupu"]
    all_data = []
    
    for platform in platforms:
        df = load_platform_data(platform, keyword)
        if not df.empty:
            if "platform" not in df.columns:
                df["platform"] = platform
            all_data.append(df)
    
    if not all_data:
        print("No data found!")
        return pd.DataFrame()
    
    merged_df = pd.concat(all_data, ignore_index=True)
    print("\nTotal merged data: %d records" % len(merged_df))
    
    merged_data_path = os.path.join(PROJECT_ROOT, "data", "latest", "merged_all_platform.csv")
    os.makedirs(os.path.dirname(merged_data_path), exist_ok=True)
    merged_df.to_csv(merged_data_path, index=False, encoding='utf-8-sig')
    print("Merged data saved: %s" % merged_data_path)
    
    platform_counts = merged_df["platform"].value_counts()
    print("\nPlatform statistics:")
    for platform, count in platform_counts.items():
        print("  %s: %d records" % (platform, count))
    
    return merged_df

def clean_data(df):
    print("\n" + "=" * 80)
    print("Cleaning data")
    print("=" * 80)
    
    cleaned_df = df.copy()
    
    if "content" not in cleaned_df.columns:
        if "comment_content" in cleaned_df.columns:
            cleaned_df["content"] = cleaned_df["comment_content"]
        else:
            cleaned_df["content"] = ""
    
    def clean_content(text):
        if pd.isna(text):
            return ""
        text = str(text)
        text = text.replace('\n', ' ').replace('\r', ' ')
        text = ' '.join(text.split())
        return text
    
    cleaned_df["content_clean"] = cleaned_df["content"].apply(clean_content)
    cleaned_df["content_length"] = cleaned_df["content_clean"].apply(len)
    
    cleaned_df = cleaned_df[cleaned_df["content_length"] >= 10]
    print("\nCleaned data: %d records" % len(cleaned_df))
    print("  Filtered %d invalid records" % (len(df) - len(cleaned_df)))
    
    cleaned_data_path = os.path.join(PROJECT_ROOT, "data", "latest", "cleaned_all_data.csv")
    cleaned_df.to_csv(cleaned_data_path, index=False, encoding='utf-8-sig')
    print("Cleaned data saved: %s" % cleaned_data_path)
    
    return cleaned_df

def analyze_data(df):
    print("\n" + "=" * 80)
    print("Analyzing data")
    print("=" * 80)
    
    try:
        from src.analysis.sentiment_analysis import analyze_dataframe
        analyzed_df = analyze_dataframe(df, preferred="snownlp")
        print("\nSentiment analysis complete: %d records" % len(analyzed_df))
    except Exception as e:
        print("Sentiment analysis failed: %s" % e)
        import traceback
        traceback.print_exc()
        analyzed_df = df
    
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
    
    analysis_result = {
        "sentiment_dist": sentiment_dist,
        "platform_heat": platform_heat,
        "generate_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    analysis_result_path = os.path.join(PROJECT_ROOT, "data", "latest", "analysis_result.json")
    with open(analysis_result_path, "w", encoding="utf-8") as f:
        json.dump(analysis_result, f, ensure_ascii=False, indent=2)
    print("Analysis result saved: %s" % analysis_result_path)
    
    analyzed_comments_path = os.path.join(PROJECT_ROOT, "data", "latest", "analyzed_comments.csv")
    if "polarity_label" in analyzed_df.columns:
        analyzed_df.to_csv(analyzed_comments_path, index=False, encoding='utf-8-sig')
        print("Analyzed comments saved: %s" % analyzed_comments_path)
    
    return analysis_result

def run_full_process(keyword="上海迪士尼"):
    print("=" * 80)
    print("Starting full data processing pipeline (latest data)")
    print("=" * 80)
    
    merged_df = merge_all_platforms(keyword)
    if merged_df.empty:
        print("No data to process")
        return
    
    cleaned_df = clean_data(merged_df)
    if cleaned_df.empty:
        print("No valid data after cleaning")
        return
    
    analysis_result = analyze_data(cleaned_df)
    
    print("\n" + "=" * 80)
    print("Data processing pipeline complete!")
    print("=" * 80)
    
    print("\nAnalysis summary:")
    print("Sentiment distribution:")
    for item in analysis_result.get("sentiment_dist", []):
        print("  %s: %d records (%.2f%%)" % (item['label'], item['count'], item['ratio'] * 100))
    
    print("\nPlatform heat:")
    for item in analysis_result.get("platform_heat", []):
        print("  %s: %d posts, %d comments" % (item['platform'], item['post_total'], item['comment_total']))


def main():
    print("=" * 80)
    print("Latest Data Processing Module")
    print("=" * 80)
    
    run_full_process()


if __name__ == "__main__":
    main()
