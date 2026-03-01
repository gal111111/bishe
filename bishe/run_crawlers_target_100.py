

# -*- coding: utf-8 -*-
"""
智能爬虫脚本 - 确保每个平台获取100条评论
"""
import os
import sys
import time
import pandas as pd

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.crawlers.weibo_spider import WeiboSpider
from src.crawlers.selenium_spiders.zhihu_selenium_spider import ZhihuSpider
from src.crawlers.selenium_spiders.tieba_selenium_spider import TiebaSpider
from src.crawlers.selenium_spiders.hupu_selenium_spider import HupuSpider


def get_comment_count(csv_path):
    """获取CSV文件中的评论数量"""
    if not os.path.exists(csv_path):
        return 0
    try:
        df = pd.read_csv(csv_path, encoding='utf-8-sig')
        return len(df)
    except:
        return 0


def run_weibo_until_target(keyword="上海迪士尼", target_comments=100):
    """运行微博爬虫直到达到目标评论数"""
    print("\n" + "=" * 80)
    print(f"微博爬虫 - 目标: {target_comments}条评论")
    print("=" * 80)
    
    current_count = 0
    post_count = 20  # 从20个帖子开始
    
    while current_count &lt; target_comments:
        print(f"\n当前评论数: {current_count}/{target_comments}")
        print(f"尝试爬取 {post_count} 个帖子...")
        
        try:
            official_url = "https://weibo.com/u/5200478600"
            spider = WeiboSpider(headless=False)
            weibo_data = spider.crawl(
                keyword=keyword, 
                target_count=post_count, 
                is_official=True, 
                official_url=official_url
            )
            
            if weibo_data:
                csv_path = spider.save_comments_to_csv(weibo_data, keyword)
                current_count = get_comment_count(csv_path)
                print(f"✅ 当前获得 {current_count} 条评论")
                
                if current_count &gt;= target_comments:
                    print(f"🎉 微博达到目标: {current_count}条评论")
                    return csv_path
            else:
                print("❌ 未获取到数据")
            
        except Exception as e:
            print(f"❌ 微博爬虫出错: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if 'spider' in locals():
                spider.close()
        
        # 增加帖子数量继续尝试
        post_count += 10
        if post_count &gt; 100:
            print("⚠️  已达到最大尝试次数，停止")
            break
        
        time.sleep(3)
    
    return csv_path if 'csv_path' in locals() else None


def run_zhihu_until_target(keyword="上海迪士尼", target_comments=100):
    """运行知乎爬虫直到达到目标评论数"""
    print("\n" + "=" * 80)
    print(f"知乎爬虫 - 目标: {target_comments}条评论")
    print("=" * 80)
    
    current_count = 0
    post_count = 30  # 从30个帖子开始
    
    while current_count &lt; target_comments:
        print(f"\n当前评论数: {current_count}/{target_comments}")
        print(f"尝试爬取 {post_count} 个帖子...")
        
        try:
            spider = ZhihuSpider(headless=False)
            zhihu_data = spider.crawl(keyword=keyword, target_count=post_count)
            
            if zhihu_data:
                csv_path = spider.save_comments_to_csv(zhihu_data, keyword)
                current_count = get_comment_count(csv_path)
                print(f"✅ 当前获得 {current_count} 条评论")
                
                if current_count &gt;= target_comments:
                    print(f"🎉 知乎达到目标: {current_count}条评论")
                    return csv_path
            else:
                print("❌ 未获取到数据")
            
        except Exception as e:
            print(f"❌ 知乎爬虫出错: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if 'spider' in locals():
                spider.close()
        
        # 增加帖子数量继续尝试
        post_count += 15
        if post_count &gt; 150:
            print("⚠️  已达到最大尝试次数，停止")
            break
        
        time.sleep(3)
    
    return csv_path if 'csv_path' in locals() else None


def run_tieba_until_target(keyword="上海迪士尼", target_comments=100):
    """运行贴吧爬虫直到达到目标评论数"""
    print("\n" + "=" * 80)
    print(f"贴吧爬虫 - 目标: {target_comments}条评论")
    print("=" * 80)
    
    current_count = 0
    post_count = 20  # 从20个帖子开始
    
    while current_count &lt; target_comments:
        print(f"\n当前评论数: {current_count}/{target_comments}")
        print(f"尝试爬取 {post_count} 个帖子...")
        
        try:
            spider = TiebaSpider(headless=False)
            tieba_data = spider.crawl(keyword=keyword, target_count=post_count)
            
            if tieba_data:
                csv_path = spider.save_comments_to_csv(tieba_data, keyword)
                current_count = get_comment_count(csv_path)
                print(f"✅ 当前获得 {current_count} 条评论")
                
                if current_count &gt;= target_comments:
                    print(f"🎉 贴吧达到目标: {current_count}条评论")
                    return csv_path
            else:
                print("❌ 未获取到数据")
            
        except Exception as e:
            print(f"❌ 贴吧爬虫出错: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if 'spider' in locals():
                spider.close()
        
        # 增加帖子数量继续尝试
        post_count += 10
        if post_count &gt; 100:
            print("⚠️  已达到最大尝试次数，停止")
            break
        
        time.sleep(3)
    
    return csv_path if 'csv_path' in locals() else None


def run_hupu_until_target(keyword="上海迪士尼", target_comments=100):
    """运行虎扑爬虫直到达到目标评论数"""
    print("\n" + "=" * 80)
    print(f"虎扑爬虫 - 目标: {target_comments}条评论")
    print("=" * 80)
    
    current_count = 0
    post_count = 30  # 从30个帖子开始
    
    while current_count &lt; target_comments:
        print(f"\n当前评论数: {current_count}/{target_comments}")
        print(f"尝试爬取 {post_count} 个帖子...")
        
        try:
            spider = HupuSpider(headless=False)
            hupu_data = spider.crawl(keyword=keyword, target_count=post_count)
            
            if hupu_data:
                csv_path = spider.save_comments_to_csv(hupu_data, keyword)
                current_count = get_comment_count(csv_path)
                print(f"✅ 当前获得 {current_count} 条评论")
                
                if current_count &gt;= target_comments:
                    print(f"🎉 虎扑达到目标: {current_count}条评论")
                    return csv_path
            else:
                print("❌ 未获取到数据")
            
        except Exception as e:
            print(f"❌ 虎扑爬虫出错: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if 'spider' in locals():
                spider.close()
        
        # 增加帖子数量继续尝试
        post_count += 15
        if post_count &gt; 150:
            print("⚠️  已达到最大尝试次数，停止")
            break
        
        time.sleep(3)
    
    return csv_path if 'csv_path' in locals() else None


if __name__ == "__main__":
    print("=" * 80)
    print("智能爬虫 - 目标: 每个平台100条评论")
    print("=" * 80)
    
    keyword = "上海迪士尼"
    target_comments = 100
    
    all_results = {}
    
    # 按顺序运行四个爬虫
    all_results['weibo'] = run_weibo_until_target(keyword, target_comments)
    time.sleep(3)
    
    all_results['zhihu'] = run_zhihu_until_target(keyword, target_comments)
    time.sleep(3)
    
    all_results['tieba'] = run_tieba_until_target(keyword, target_comments)
    time.sleep(3)
    
    all_results['hupu'] = run_hupu_until_target(keyword, target_comments)
    
    # 总结
    print("\n" + "=" * 80)
    print("爬虫运行总结")
    print("=" * 80)
    
    for platform, result in all_results.items():
        if result:
            count = get_comment_count(result)
            print(f"✅ {platform}: {count}条评论 - {result}")
        else:
            print(f"❌ {platform}: 失败")
    
    print("\n" + "=" * 80)
    print("爬虫运行完成！")
    print("=" * 80)

