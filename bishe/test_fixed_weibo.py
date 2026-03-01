# -*- coding: utf-8 -*-
"""
测试修复后的微博爬虫
"""
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from src.crawlers.weibo_spider import WeiboSpider


def test_weibo_spider():
    """测试微博爬虫"""
    print("=" * 80)
    print("测试修复后的微博爬虫 - 只爬取3条微博")
    print("=" * 80)
    
    try:
        spider = WeiboSpider(headless=False)
        
        keyword = "上海迪士尼"
        official_url = "https://weibo.com/u/5200478600"
        print(f"\n测试关键词: {keyword}")
        print(f"官方微博: {official_url}")
        print(f"目标微博数: 3条（测试评论爬取完整性）")
        
        weibo_data = spider.crawl(keyword, target_count=3, is_official=True, official_url=official_url)
        
        csv_path = None
        if weibo_data:
            print(f"\n✅ 爬取成功！共获取 {len(weibo_data)} 条数据（每条评论单独一行）")
            
            print("\n=== 数据统计 ===")
            unique_posts = set()
            for row in weibo_data:
                unique_posts.add(row['post_id'])
            print(f"帖子数: {len(unique_posts)}")
            print(f"评论数: {len(weibo_data)}")
            print(f"平均每帖评论数: {len(weibo_data)/len(unique_posts):.1f}")
            
            print("\n=== 爬取的数据预览（前10条） ===")
            for i, data in enumerate(weibo_data[:10]):
                print(f"\n--- 第{i+1}条数据 ---")
                content_preview = data['content'][:60] if len(data['content']) > 60 else data['content']
                print(f"微博内容: {content_preview}...")
                print(f"评论用户: {data['comment_users']}")
                print(f"评论内容: {data['comment_content']}")
            
            csv_path = spider.save_comments_to_csv(weibo_data, keyword)
            if csv_path:
                print("\n" + "=" * 80)
                print("📁 数据已成功保存！")
                print(f"📂 文件路径: {csv_path}")
                print("=" * 80)
        else:
            print("未获取到数据")
        
        print("\n⏰ 浏览器窗口将保持打开10秒，让你查看...")
        import time
        time.sleep(10)
        print("⏰ 10秒到了，准备关闭浏览器...")
            
    finally:
        if 'spider' in locals():
            spider.close()
        
        print("\n" + "=" * 80)
        print("微博爬虫测试完成！")
        print("=" * 80)


if __name__ == "__main__":
    test_weibo_spider()
