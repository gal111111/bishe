
# -*- coding: utf-8 -*-
"""
新数据爬取脚本
确保爬取新数据且不重复
"""
import os
import sys
import time
import random
import pandas as pd
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from src.modules.platform_crawler import PlatformCrawler
from src.preprocessing.advanced_data_cleaner import AdvancedDataCleaner

def load_existing_data():
    """加载现有数据，用于去重"""
    data_path = os.path.join(PROJECT_ROOT, 'data', 'latest', 'merged_all_platform.csv')
    if os.path.exists(data_path):
        df = pd.read_csv(data_path)
        existing_contents = set(df['content'].astype(str).tolist())
        print(f"✅ 已加载 {len(existing_contents)} 条现有内容用于去重")
        return existing_contents
    return set()

def crawl_new_data():
    """爬取新数据"""
    print("=" * 80)
    print("🕷️  开始爬取新数据")
    print("=" * 80)
    
    # 加载现有数据用于去重
    existing_contents = load_existing_data()
    
    # 搜索词列表
    search_terms = [
        "上海迪士尼 体验",
        "上海迪士尼 服务",
        "上海迪士尼 排队",
        "上海迪士尼 卫生",
        "上海迪士尼 设施",
        "上海迪士尼 餐饮",
        "上海迪士尼 价格",
        "上海迪士尼 交通"
    ]
    
    all_data = []
    
    # 为每个平台创建单独的爬虫实例
    weibo_crawler = PlatformCrawler('weibo')
    zhihu_crawler = PlatformCrawler('zhihu')
    tieba_crawler = PlatformCrawler('tieba')
    hupu_crawler = PlatformCrawler('hupu')
    
    for search_term in search_terms:
        print(f"\n🔍 搜索: {search_term}")
        
        # 爬取微博
        try:
            weibo_data = weibo_crawler.crawl_keyword(search_term)
            all_data.extend(weibo_data)
            print(f"   微博: {len(weibo_data)} 条")
        except Exception as e:
            print(f"   微博爬取失败: {e}")
        
        # 爬取知乎
        try:
            zhihu_data = zhihu_crawler.crawl_keyword(search_term)
            all_data.extend(zhihu_data)
            print(f"   知乎: {len(zhihu_data)} 条")
        except Exception as e:
            print(f"   知乎爬取失败: {e}")
        
        # 爬取贴吧
        try:
            tieba_data = tieba_crawler.crawl_keyword(search_term)
            all_data.extend(tieba_data)
            print(f"   贴吧: {len(tieba_data)} 条")
        except Exception as e:
            print(f"   贴吧爬取失败: {e}")
        
        # 爬取虎扑
        try:
            hupu_data = hupu_crawler.crawl_keyword(search_term)
            all_data.extend(hupu_data)
            print(f"   虎扑: {len(hupu_data)} 条")
        except Exception as e:
            print(f"   虎扑爬取失败: {e}")
        
        # 随机延迟
        time.sleep(random.uniform(2, 5))
    
    # 去重
    print(f"\n🔄 去重处理...")
    unique_data = []
    seen_contents = set()
    
    for item in all_data:
        content = str(item.get('content', '') or item.get('comment_content', ''))
        if content and content not in existing_contents and content not in seen_contents:
            seen_contents.add(content)
            unique_data.append(item)
    
    print(f"✅ 去重后: {len(unique_data)} 条新数据")
    
    if not unique_data:
        print("⚠️  没有发现新数据")
        return None
    
    # 保存新数据
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    new_data_path = os.path.join(PROJECT_ROOT, 'data', 'raw', f'new_data_{timestamp}.csv')
    
    df_new = pd.DataFrame(unique_data)
    df_new.to_csv(new_data_path, index=False, encoding='utf-8-sig')
    print(f"✅ 新数据已保存至: {new_data_path}")
    
    # 合并到主数据
    merge_data(df_new, existing_contents)
    
    return df_new

def merge_data(df_new, existing_contents):
    """合并新数据到主数据"""
    main_data_path = os.path.join(PROJECT_ROOT, 'data', 'latest', 'merged_all_platform.csv')
    
    # 加载主数据
    if os.path.exists(main_data_path):
        df_main = pd.read_csv(main_data_path)
    else:
        df_main = pd.DataFrame()
    
    # 合并数据
    combined_df = pd.concat([df_main, df_new], ignore_index=True)
    
    # 再次去重
    unique_combined = []
    seen = set()
    
    for idx, row in combined_df.iterrows():
        content = str(row.get('content', '') or row.get('comment_content', ''))
        if content and content not in seen:
            seen.add(content)
            unique_combined.append(row)
    
    combined_df = pd.DataFrame(unique_combined)
    
    # 使用高级数据清洗器
    cleaner = AdvancedDataCleaner()
    cleaned_df = cleaner.clean_data_pipeline(combined_df, min_quality_score=40, balance_sentiment=True)
    
    # 保存合并后的数据
    cleaned_df.to_csv(main_data_path, index=False, encoding='utf-8-sig')
    print(f"✅ 主数据已更新: {len(cleaned_df)} 条")

def main():
    """主函数"""
    try:
        df_new = crawl_new_data()
        
        if df_new is not None:
            print("\n" + "=" * 80)
            print("✅ 数据爬取完成！")
            print(f"📊 新增数据: {len(df_new)} 条")
            print("=" * 80)
        else:
            print("\n" + "=" * 80)
            print("⚠️  未获取到新数据")
            print("=" * 80)
            
    except Exception as e:
        print(f"\n❌ 爬取失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

