# -*- coding: utf-8 -*-
"""
运行增强版爬虫 - 爬取评论
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime

def run_xiaohongshu():
    """运行小红书爬虫"""
    print('\n' + '='*60)
    print('运行小红书爬虫（评论增强版）')
    print('='*60)
    
    from src.crawlers.selenium_spiders.xiaohongshu_selenium_spider import XiaohongshuSpider
    
    spider = XiaohongshuSpider(use_edge=True)
    output_file = spider.run("上海迪士尼", max_posts=5, max_comments_per_post=20)
    
    return output_file


def run_bilibili():
    """运行B站爬虫"""
    print('\n' + '='*60)
    print('运行B站爬虫（评论增强版）')
    print('='*60)
    
    from src.crawlers.selenium_spiders.bilibili_selenium_spider import BilibiliSpider
    
    spider = BilibiliSpider(use_edge=True)
    output_file = spider.run("上海迪士尼", max_videos=5, max_comments_per_video=20)
    
    return output_file


def run_douyin():
    """运行抖音爬虫"""
    print('\n' + '='*60)
    print('运行抖音爬虫（评论增强版）')
    print('='*60)
    
    from src.crawlers.selenium_spiders.douyin_selenium_spider import DouyinSpider
    
    spider = DouyinSpider(use_edge=True)
    output_file = spider.run("上海迪士尼", max_videos=5, max_comments_per_video=20)
    
    return output_file


if __name__ == "__main__":
    print('\n' + '#'*60)
    print('# 开始运行增强版爬虫（爬取评论）')
    print('#'*60)
    
    results = {}
    
    # 运行小红书爬虫
    try:
        results['小红书'] = run_xiaohongshu()
    except Exception as e:
        print(f'[ERROR] 小红书爬虫运行失败: {e}')
        results['小红书'] = None
    
    # 运行B站爬虫
    try:
        results['B站'] = run_bilibili()
    except Exception as e:
        print(f'[ERROR] B站爬虫运行失败: {e}')
        results['B站'] = None
    
    # 运行抖音爬虫
    try:
        results['抖音'] = run_douyin()
    except Exception as e:
        print(f'[ERROR] 抖音爬虫运行失败: {e}')
        results['抖音'] = None
    
    # 汇总结果
    print('\n' + '#'*60)
    print('# 爬虫运行结果汇总')
    print('#'*60)
    
    for name, output_file in results.items():
        if output_file:
            print(f'{name}: ✅ 成功 -> {output_file}')
        else:
            print(f'{name}: ❌ 失败')
