
# -*- coding: utf-8 -*-
"""
单独运行微博爬虫 - 获取约100条评论
"""
import os
import sys
import time

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.crawlers.weibo_spider import WeiboSpider


def run_weibo():
    """运行微博爬虫"""
    print("\n" + "=" * 80)
    print("开始运行微博爬虫 - 目标约1000条评论")
    print("=" * 80)
    
    try:
        official_url = "https://weibo.com/u/5200478600"
        spider = WeiboSpider(headless=False)
        weibo_data = spider.crawl(
            keyword="上海迪士尼",
            target_count=100,
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


if __name__ == "__main__":
    print("=" * 80)
    print("微博爬虫单独运行")
    print("=" * 80)
    
    result = run_weibo()
    
    if result:
        print("\n✅ 微博爬虫成功完成！")
        print(f"📁 数据文件: {result}")
    else:
        print("\n❌ 微博爬虫失败")
    
    print("\n" + "=" * 80)

