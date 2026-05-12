
# -*- coding: utf-8 -*-
"""
简单测试贴吧爬虫 - 只爬2个帖子
"""
import os
import sys
import time

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.crawlers.selenium_spiders.tieba_selenium_spider import TiebaSpider


def run_tieba():
    """运行贴吧爬虫"""
    print("\n" + "=" * 80)
    print("开始测试贴吧爬虫 - 目标2个帖子")
    print("=" * 80)
    
    try:
        spider = TiebaSpider(headless=False)
        tieba_data = spider.crawl(keyword="上海迪士尼", target_count=2)
        
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


if __name__ == "__main__":
    print("=" * 80)
    print("贴吧爬虫简单测试")
    print("=" * 80)
    
    result = run_tieba()
    
    if result:
        print("\n✅ 贴吧爬虫成功完成！")
        print(f"📁 数据文件: {result}")
    else:
        print("\n❌ 贴吧爬虫失败")
    
    print("\n" + "=" * 80)
