
# -*- coding: utf-8 -*-
"""
分别运行各个平台的爬虫 - 避免登录问题阻塞整个流程
"""
import os
import sys
import time

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.crawlers.selenium_spiders.tieba_selenium_spider import TiebaSpider
from src.crawlers.selenium_spiders.hupu_selenium_spider import HupuSpider


def run_tieba_crawler(keyword="上海迪士尼", target_count=10):
    """运行贴吧爬虫"""
    print("\n" + "=" * 80)
    print("开始运行贴吧爬虫")
    print("=" * 80)
    
    try:
        spider = TiebaSpider(headless=False)
        tieba_data = spider.crawl(keyword=keyword, target_count=target_count)
        
        if tieba_data:
            csv_path = spider.save_comments_to_csv(tieba_data, keyword)
            print(f"✅ 贴吧爬虫完成，获取 {len(tieba_data)} 条数据")
            return csv_path
        else:
            print("❌ 贴吧爬虫未获取到数据")
            return None
    except Exception as e:
        print(f"❌ 贴吧爬虫出错: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        if 'spider' in locals():
            spider.close()


def run_hupu_crawler(keyword="上海迪士尼", target_count=10):
    """运行虎扑爬虫"""
    print("\n" + "=" * 80)
    print("开始运行虎扑爬虫")
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
    print("分别运行各个平台的爬虫")
    print("=" * 80)
    
    keyword = "上海迪士尼"
    target_post_count = 10
    
    print(f"\n目标关键词: {keyword}")
    print(f"每个平台目标帖子数: {target_post_count}")
    
    all_results = {}
    
    # 1. 先运行贴吧爬虫
    all_results['tieba'] = run_tieba_crawler(keyword, target_post_count)
    time.sleep(3)
    
    # 2. 再运行虎扑爬虫
    all_results['hupu'] = run_hupu_crawler(keyword, target_post_count)
    
    # 总结
    print("\n" + "=" * 80)
    print("爬虫运行总结")
    print("=" * 80)
    
    for platform, result in all_results.items():
        if result:
            print(f"✅ {platform}: {result}")
        else:
            print(f"❌ {platform}: 失败")
    
    print("\n" + "=" * 80)
    print("提示：微博数据已在之前运行中保存到data/latest文件夹")
    print("知乎需要手动重新登录获取新鲜cookie，再单独运行")
    print("=" * 80)

