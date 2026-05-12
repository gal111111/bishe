


# -*- coding: utf-8 -*-
"""
单独运行虎扑爬虫 - 大规模数据爬取
"""
import os
import sys
import time

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.crawlers.selenium_spiders.hupu_selenium_spider import HupuSpider


def run_hupu_crawler(keyword="上海迪士尼", target_count=100):
    """运行虎扑爬虫"""
    print("\n" + "=" * 80)
    print("开始运行虎扑爬虫 - 大规模数据爬取")
    print("=" * 80)
    
    try:
        spider = HupuSpider(headless=False)
        hupu_data = spider.crawl(keyword=keyword, target_count=target_count)
        
        if hupu_data:
            csv_path = spider.save_comments_to_csv(hupu_data, keyword)
            print(f"✅ 虎扑爬虫完成，获取 {len(hupu_data)} 条数据")
            return csv_path
        else:
            print("❌ 虎扑爬虫未获取到数据")
            return None
    except Exception as e:
        print(f"❌ 虎扑爬虫出错: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        if 'spider' in locals():
            spider.close()


if __name__ == "__main__":
    print("=" * 80)
    print("虎扑爬虫 - 大规模数据爬取")
    print("=" * 80)
    
    keyword = "上海迪士尼"
    target_post_count = 100
    
    print(f"\n目标关键词: {keyword}")
    print(f"目标帖子数: {target_post_count}")
    print(f"预计获取评论数: 每个帖子约25条评论，总计约2500条评论\n")
    
    result = run_hupu_crawler(keyword, target_post_count)
    
    print("\n" + "=" * 80)
    if result:
        print(f"✅ 虎扑爬虫成功！数据已保存到: {result}")
    else:
        print("❌ 虎扑爬虫失败")
    print("=" * 80)

