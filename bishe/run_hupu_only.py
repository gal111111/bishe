
# -*- coding: utf-8 -*-
"""
单独运行虎扑爬虫 - 获取约100条评论
"""
import os
import sys
import time

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.crawlers.selenium_spiders.hupu_selenium_spider import HupuSpider


def run_hupu():
    """运行虎扑爬虫"""
    print("\n" + "=" * 80)
    print("开始运行虎扑爬虫 - 目标约100条评论")
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
    print("虎扑爬虫单独运行")
    print("=" * 80)
    
    result = run_hupu()
    
    if result:
        print("\n✅ 虎扑爬虫成功完成！")
        print(f"📁 数据文件: {result}")
    else:
        print("\n❌ 虎扑爬虫失败")
    
    print("\n" + "=" * 80)

