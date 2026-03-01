

# -*- coding: utf-8 -*-
"""
统一运行四个平台的爬虫 - 每个平台100条评论
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


def run_weibo():
    """运行微博爬虫"""
    print("\n" + "=" * 80)
    print("开始运行微博爬虫 - 目标100条评论")
    print("=" * 80)
    
    try:
        official_url = "https://weibo.com/u/5200478600"
        spider = WeiboSpider(headless=False)
        weibo_data = spider.crawl(
            keyword="上海迪士尼",
            target_count=30,
            is_official=True,
            official_url=official_url
        )
        
        if weibo_data:
            csv_path = spider.save_comments_to_csv(weibo_data, "上海迪士尼")
            print(f"✅ 微博爬虫完成，获取 {len(weibo_data)} 条评论")
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


def run_zhihu():
    """运行知乎爬虫"""
    print("\n" + "=" * 80)
    print("开始运行知乎爬虫 - 目标100条评论")
    print("=" * 80)
    
    try:
        spider = ZhihuSpider(headless=False)
        zhihu_data = spider.crawl(keyword="上海迪士尼", target_count=40)
        
        if zhihu_data:
            csv_path = spider.save_comments_to_csv(zhihu_data, "上海迪士尼")
            print(f"✅ 知乎爬虫完成，获取 {len(zhihu_data)} 条评论")
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


def run_tieba():
    """运行贴吧爬虫"""
    print("\n" + "=" * 80)
    print("开始运行贴吧爬虫 - 目标100条评论")
    print("=" * 80)
    
    try:
        spider = TiebaSpider(headless=False)
        tieba_data = spider.crawl(keyword="上海迪士尼", target_count=30)
        
        if tieba_data:
            csv_path = spider.save_comments_to_csv(tieba_data, "上海迪士尼")
            print(f"✅ 贴吧爬虫完成，获取 {len(tieba_data)} 条评论")
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


def run_hupu():
    """运行虎扑爬虫"""
    print("\n" + "=" * 80)
    print("开始运行虎扑爬虫 - 目标100条评论")
    print("=" * 80)
    
    try:
        spider = HupuSpider(headless=False)
        hupu_data = spider.crawl(keyword="上海迪士尼", target_count=40)
        
        if hupu_data:
            csv_path = spider.save_comments_to_csv(hupu_data, "上海迪士尼")
            print(f"✅ 虎扑爬虫完成，获取 {len(hupu_data)} 条评论")
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
    print("多平台爬虫统一运行 - 每个平台100条评论")
    print("=" * 80)
    
    all_results = {}
    
    # 按顺序运行四个爬虫
    all_results['weibo'] = run_weibo()
    time.sleep(3)
    
    all_results['zhihu'] = run_zhihu()
    time.sleep(3)
    
    all_results['tieba'] = run_tieba()
    time.sleep(3)
    
    all_results['hupu'] = run_hupu()
    
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

