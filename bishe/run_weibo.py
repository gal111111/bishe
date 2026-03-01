

# -*- coding: utf-8 -*-
"""
只运行微博爬虫
"""
import os
import sys
import time

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.crawlers.weibo_spider import WeiboSpider


if __name__ == "__main__":
    print("=" * 80)
    print("微博爬虫 - 目标100条评论")
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
            print(f"\n✅ 微博爬虫完成！")
            print(f"📊 共获取 {len(weibo_data)} 条评论")
            print(f"📁 文件: {csv_path}")
        else:
            print("\n❌ 微博爬虫未获取到数据")
            
    except Exception as e:
        print(f"\n❌ 微博爬虫出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'spider' in locals():
            spider.close()
    
    print("\n" + "=" * 80)
    print("微博爬虫运行完成！")
    print("=" * 80)

