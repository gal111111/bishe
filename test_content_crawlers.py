# -*- coding: utf-8 -*-
"""
测试小红书和抖音的内容版爬虫
"""

import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from src.crawlers.new_platforms.xiaohongshu_content_spider import XiaohongshuSpider
from src.crawlers.new_platforms.douyin_content_spider import DouyinContentSpider


def run_test_crawlers(keyword="上海迪士尼"):
    """
    运行测试爬虫
    
    Args:
        keyword: 搜索关键词
    """
    print("\n" + "#"*60)
    print("# 测试内容版爬虫")
    print("#"*60 + "\n")
    
    results = {}
    
    # 1. 小红书
    print("\n" + "="*60)
    print("运行小红书爬虫（内容版）")
    print("="*60)
    try:
        xhs_spider = XiaohongshuSpider(use_edge=True)
        xhs_file = xhs_spider.run(keyword, max_posts=3)
        if xhs_file:
            results['小红书'] = ('✅ 成功', xhs_file)
        else:
            results['小红书'] = ('❌ 失败', None)
    except Exception as e:
        print(f"[错误] 小红书爬虫运行失败: {e}")
        import traceback
        traceback.print_exc()
        results['小红书'] = ('❌ 失败', None)
    
    # 2. 抖音
    print("\n" + "="*60)
    print("运行抖音爬虫（内容版）")
    print("="*60)
    try:
        douyin_spider = DouyinContentSpider(use_edge=True)
        douyin_file = douyin_spider.run(keyword, max_videos=3)
        if douyin_file:
            results['抖音'] = ('✅ 成功', douyin_file)
        else:
            results['抖音'] = ('❌ 失败', None)
    except Exception as e:
        print(f"[错误] 抖音爬虫运行失败: {e}")
        import traceback
        traceback.print_exc()
        results['抖音'] = ('❌ 失败', None)
    
    # 输出结果
    print("\n" + "#"*60)
    print("# 测试结果汇总")
    print("#"*60)
    for platform, (status, filepath) in results.items():
        if filepath:
            print(f"{platform}: {status} -> {filepath}")
        else:
            print(f"{platform}: {status}")


if __name__ == "__main__":
    keyword = "上海迪士尼"
    if len(sys.argv) > 1:
        keyword = sys.argv[1]
    run_test_crawlers(keyword)
