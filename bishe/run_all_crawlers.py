

# -*- coding: utf-8 -*-
"""
统一运行四个平台的爬虫 - 获取更多评论数据
"""
import os
import sys
import time

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.crawlers.weibo_spider import WeiboSpider
from src.crawlers.selenium_spiders.zhihu_selenium_spider import ZhihuSpider
from src.crawlers.selenium_spiders.tieba_selenium_spider import TiebaSpider
from src.crawlers.selenium_spiders.hupu_selenium_spider import HupuSpider


def run_weibo_crawler(keyword="上海迪士尼", target_count=50):
    """运行微博爬虫"""
    print("\n" + "=" * 80)
    print("开始运行微博爬虫")
    print("=" * 80)
    
    try:
        official_url = "https://weibo.com/u/5200478600"
        spider = WeiboSpider(headless=False)
        weibo_data = spider.crawl(
            keyword=keyword, 
            target_count=target_count, 
            is_official=True, 
            official_url=official_url
        )
        
        if weibo_data:
            csv_path = spider.save_comments_to_csv(weibo_data, keyword)
            print(f"✅ 微博爬虫完成，获取 {len(weibo_data)} 条数据")
            return csv_path
        else:
            print("❌ 微博爬虫未获取到数据")
            return None
    except Exception as e:
        print(f"❌ 微博爬虫出错: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        if 'spider' in locals():
            spider.close()


def run_zhihu_crawler(keyword="上海迪士尼", target_count=50):
    """运行知乎爬虫"""
    print("\n" + "=" * 80)
    print("开始运行知乎爬虫")
    print("=" * 80)
    
    try:
        spider = ZhihuSpider(headless=False)
        zhihu_data = spider.crawl(keyword=keyword, target_count=target_count)
        
        if zhihu_data:
            csv_path = spider.save_comments_to_csv(zhihu_data, keyword)
            print(f"✅ 知乎爬虫完成，获取 {len(zhihu_data)} 条数据")
            return csv_path
        else:
            print("❌ 知乎爬虫未获取到数据")
            return None
    except Exception as e:
        print(f"❌ 知乎爬虫出错: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        if 'spider' in locals():
            spider.close()


def run_tieba_crawler(keyword="上海迪士尼", target_count=50):
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


def run_hupu_crawler(keyword="上海迪士尼", target_count=50):
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
    print("多平台爬虫统一运行脚本")
    print("=" * 80)
    
    keyword = "上海迪士尼"
    target_post_count = 200  # 每个平台爬取200个帖子，以获取约2000条评论
    
    print(f"\n目标关键词: {keyword}")
    print(f"每个平台目标帖子数: {target_post_count}")
    print(f"预计获取评论数: 每个帖子约10条评论，总计约8000条评论\n")
    
    all_results = {}
    
    # 按顺序运行四个爬虫
    all_results['weibo'] = run_weibo_crawler(keyword, target_post_count)
    time.sleep(3)
    
    all_results['zhihu'] = run_zhihu_crawler(keyword, target_post_count)
    time.sleep(3)
    
    all_results['tieba'] = run_tieba_crawler(keyword, target_post_count)
    time.sleep(3)
    
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
    print("爬虫运行完成！")
    print("=" * 80)

