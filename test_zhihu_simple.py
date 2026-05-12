
# -*- coding: utf-8 -*-
"""
简单测试知乎爬虫 - 只爬2个帖子
"""
import os
import sys
import time

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.crawlers.selenium_spiders.zhihu_selenium_spider import ZhihuSpider


def run_zhihu():
    """运行知乎爬虫"""
    print("\n" + "=" * 80)
    print("开始测试知乎爬虫 - 目标2个帖子")
    print("=" * 80)
    
    try:
        spider = ZhihuSpider(headless=False)
        zhihu_data = spider.crawl(keyword="上海迪士尼", target_count=2)
        
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


if __name__ == "__main__":
    print("=" * 80)
    print("知乎爬虫简单测试")
    print("=" * 80)
    
    result = run_zhihu()
    
    if result:
        print("\n✅ 知乎爬虫成功完成！")
        print(f"📁 数据文件: {result}")
    else:
        print("\n❌ 知乎爬虫失败")
    
    print("\n" + "=" * 80)
