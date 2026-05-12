# -*- coding: utf-8 -*-
"""
测试新添加的模块
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_absa():
    """测试方面级情感分析模块"""
    print('\n' + '='*60)
    print('测试方面级情感分析（ABSA）模块')
    print('='*60)
    
    from src.analysis.aspect_based_sentiment import AspectBasedSentimentAnalyzer
    
    # 初始化分析器
    analyzer = AspectBasedSentimentAnalyzer()
    print('[OK] 分析器初始化成功')
    
    # 测试用例
    test_cases = [
        '上海迪士尼的服务态度很好，但排队时间太长了',
        '迪士尼的烟花表演非常精彩，值得一看！',
        '园区内的餐饮价格太贵了，而且味道一般',
        '工作人员很热情，设施也很干净',
        '门票价格有点贵，但整体体验还不错'
    ]
    
    print('\n开始分析测试用例:')
    for i, text in enumerate(test_cases, 1):
        print(f'\n--- 测试用例 {i} ---')
        print(f'文本: {text}')
        result = analyzer.analyze(text)
        print(f'三元组数量: {result["aspect_count"]}')
        if result['triples']:
            for triple in result['triples']:
                print(f'  - 实体: {triple["entity"]} | 方面: {triple["aspect"]} | 情感: {triple["polarity"]} ({triple["score"]:.2f})')
        print(f'整体情感: {result["overall_sentiment"]} ({result["overall_score"]:.2f})')
    
    print('\n[SUCCESS] 方面级情感分析模块测试通过!')
    return True


def test_ablation():
    """测试消融实验模块"""
    print('\n' + '='*60)
    print('测试消融实验模块')
    print('='*60)
    
    import pandas as pd
    from src.analysis.ablation_study import AblationStudy
    
    # 创建测试数据
    test_data = {
        "content": [
            "服务态度很好，环境也不错",
            "排队时间太长了，很不满意",
            "设施很齐全，很开心",
            "一般般，没什么特别的",
            "服务太差了，再也不来了",
            "烟花表演很精彩",
            "餐饮价格太贵了",
            "工作人员很热情",
            "门票有点贵",
            "整体体验很好"
        ],
        "polarity_label": ["积极", "消极", "积极", "中性", "消极", "积极", "消极", "积极", "消极", "积极"]
    }
    
    df = pd.DataFrame(test_data)
    print(f'[OK] 创建测试数据: {len(df)} 条')
    
    # 初始化消融实验
    study = AblationStudy(output_dir="data/ablation")
    print('[OK] 消融实验初始化成功')
    
    # 运行实验
    results = study.run_ablation(df)
    print(f'[OK] 实验运行完成: {len(results)} 种方法')
    
    # 生成报告
    report_df = study.generate_report()
    print('\n消融实验结果:')
    print(report_df.to_string(index=False))
    
    print('\n[SUCCESS] 消融实验模块测试通过!')
    return True


def test_xiaohongshu_import():
    """测试小红书爬虫模块导入"""
    print('\n' + '='*60)
    print('测试小红书爬虫模块')
    print('='*60)
    
    try:
        from src.crawlers.selenium_spiders.xiaohongshu_selenium_spider import XiaohongshuSpider
        print('[OK] 小红书爬虫模块导入成功')
        
        # 测试初始化（不启动浏览器）
        spider = XiaohongshuSpider.__new__(XiaohongshuSpider)
        spider.platform = "小红书"
        spider.base_fields = [
            "platform", "post_id", "author", "content", "publish_time",
            "like_count", "comment_count", "share_count", "image_count",
            "image_descriptions", "crawl_time"
        ]
        print(f'[OK] 平台: {spider.platform}')
        print(f'[OK] 字段数: {len(spider.base_fields)}')
        
        print('[SUCCESS] 小红书爬虫模块测试通过!')
        return True
    except Exception as e:
        print(f'[ERROR] 测试失败: {e}')
        return False


def test_bilibili_import():
    """测试B站爬虫模块导入"""
    print('\n' + '='*60)
    print('测试B站爬虫模块')
    print('='*60)
    
    try:
        from src.crawlers.selenium_spiders.bilibili_selenium_spider import BilibiliSpider
        print('[OK] B站爬虫模块导入成功')
        
        # 测试初始化（不启动浏览器）
        spider = BilibiliSpider.__new__(BilibiliSpider)
        spider.platform = "B站"
        spider.base_fields = [
            "platform", "video_id", "author", "title", "content", "publish_time",
            "view_count", "like_count", "coin_count", "favorite_count", 
            "danmaku_count", "comment_count", "crawl_time"
        ]
        print(f'[OK] 平台: {spider.platform}')
        print(f'[OK] 字段数: {len(spider.base_fields)}')
        
        print('[SUCCESS] B站爬虫模块测试通过!')
        return True
    except Exception as e:
        print(f'[ERROR] 测试失败: {e}')
        return False


def test_douyin_import():
    """测试抖音爬虫模块导入"""
    print('\n' + '='*60)
    print('测试抖音爬虫模块')
    print('='*60)
    
    try:
        from src.crawlers.selenium_spiders.douyin_selenium_spider import DouyinSpider
        print('[OK] 抖音爬虫模块导入成功')
        
        # 测试初始化（不启动浏览器）
        spider = DouyinSpider.__new__(DouyinSpider)
        spider.platform = "抖音"
        spider.base_fields = [
            "platform", "video_id", "author", "title", "description", "publish_time",
            "like_count", "comment_count", "share_count", 
            "video_duration", "crawl_time"
        ]
        print(f'[OK] 平台: {spider.platform}')
        print(f'[OK] 字段数: {len(spider.base_fields)}')
        
        print('[SUCCESS] 抖音爬虫模块测试通过!')
        return True
    except Exception as e:
        print(f'[ERROR] 测试失败: {e}')
        return False


def test_docker_files():
    """测试Docker配置文件"""
    print('\n' + '='*60)
    print('测试Docker配置文件')
    print('='*60)
    
    import os
    
    files_to_check = [
        'Dockerfile',
        'docker-compose.yml',
        '.dockerignore',
        'docs/Docker部署指南.md'
    ]
    
    all_exist = True
    for file in files_to_check:
        if os.path.exists(file):
            print(f'[OK] {file} 存在')
        else:
            print(f'[ERROR] {file} 不存在')
            all_exist = False
    
    if all_exist:
        print('[SUCCESS] Docker配置文件测试通过!')
        return True
    else:
        print('[ERROR] 部分文件缺失')
        return False


if __name__ == "__main__":
    print('\n' + '#'*60)
    print('# 开始测试新添加的模块')
    print('#'*60)
    
    results = {}
    
    # 测试方面级情感分析
    try:
        results['ABSA'] = test_absa()
    except Exception as e:
        print(f'[ERROR] ABSA测试失败: {e}')
        results['ABSA'] = False
    
    # 测试消融实验
    try:
        results['Ablation'] = test_ablation()
    except Exception as e:
        print(f'[ERROR] 消融实验测试失败: {e}')
        results['Ablation'] = False
    
    # 测试爬虫模块导入
    results['Xiaohongshu'] = test_xiaohongshu_import()
    results['Bilibili'] = test_bilibili_import()
    results['Douyin'] = test_douyin_import()
    
    # 测试Docker配置
    results['Docker'] = test_docker_files()
    
    # 汇总结果
    print('\n' + '#'*60)
    print('# 测试结果汇总')
    print('#'*60)
    
    for name, passed in results.items():
        status = '✅ 通过' if passed else '❌ 失败'
        print(f'{name}: {status}')
    
    total = len(results)
    passed = sum(results.values())
    print(f'\n总计: {passed}/{total} 通过')
    
    if passed == total:
        print('\n🎉 所有测试通过!')
    else:
        print('\n⚠️ 部分测试失败，请检查错误信息')
