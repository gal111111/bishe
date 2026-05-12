# -*- coding: utf-8 -*-
"""
运行内容版爬虫（小红书、B站、抖音）
"""

import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from src.crawlers.new_platforms.xiaohongshu_content_spider import XiaohongshuSpider
from src.crawlers.new_platforms.bilibili_content_spider import BilibiliContentSpider
from src.crawlers.new_platforms.douyin_content_spider import DouyinContentSpider


def run_content_crawlers(keyword="上海迪士尼"):
    """
    运行所有内容版爬虫
    
    Args:
        keyword: 搜索关键词
    """
    print("\n" + "#"*60)
    print("# 开始运行内容版爬虫（爬取帖子/视频内容）")
    print("#"*60 + "\n")
    
    results = {}
    
    # 1. 小红书
    print("\n" + "="*60)
    print("运行小红书爬虫（内容版）")
    print("="*60)
    try:
        xhs_spider = XiaohongshuSpider(use_edge=True)
        xhs_file = xhs_spider.run(keyword, max_posts=5)
        if xhs_file:
            results['小红书'] = ('✅ 成功', xhs_file)
        else:
            results['小红书'] = ('❌ 失败', None)
    except Exception as e:
        print(f"[错误] 小红书爬虫运行失败: {e}")
        import traceback
        traceback.print_exc()
        results['小红书'] = ('❌ 失败', None)
    
    # 2. B站
    print("\n" + "="*60)
    print("运行B站爬虫（内容版）")
    print("="*60)
    try:
        bilibili_spider = BilibiliContentSpider(use_edge=True)
        bilibili_file = bilibili_spider.run(keyword, max_videos=5)
        if bilibili_file:
            results['B站'] = ('✅ 成功', bilibili_file)
        else:
            results['B站'] = ('❌ 失败', None)
    except Exception as e:
        print(f"[错误] B站爬虫运行失败: {e}")
        import traceback
        traceback.print_exc()
        results['B站'] = ('❌ 失败', None)
    
    # 3. 抖音
    print("\n" + "="*60)
    print("运行抖音爬虫（内容版）")
    print("="*60)
    try:
        douyin_spider = DouyinContentSpider(use_edge=True)
        douyin_file = douyin_spider.run(keyword, max_videos=5)
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
    print("# 爬虫运行结果汇总")
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
    run_content_crawlers(keyword)
