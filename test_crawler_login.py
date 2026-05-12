# -*- coding: utf-8 -*-
"""
测试爬虫登录状态
"""
import os
import sys
import time

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from src.crawlers.selenium_spiders.zhihu_selenium_spider import ZhihuSpider

def test_zhihu_login():
    """测试知乎登录"""
    print("=" * 80)
    print("🧪 测试知乎爬虫登录状态")
    print("=" * 80)
    
    try:
        # 创建爬虫实例，headless=False以便查看浏览器
        spider = ZhihuSpider(headless=False)
        
        # 测试访问知乎首页
        print("\n🌐 测试访问知乎首页...")
        spider.driver.get("https://www.zhihu.com")
        time.sleep(3)
        
        # 检查登录状态
        current_url = spider.driver.current_url
        page_title = spider.driver.title
        
        print(f"\n📊 登录状态检查:")
        print(f"当前URL: {current_url}")
        print(f"页面标题: {page_title}")
        
        # 检查关键cookie
        current_cookies = spider.driver.get_cookies()
        cookie_names = [c['name'] for c in current_cookies]
        print(f"\n🍪 Cookie检查:")
        print(f"Cookie数量: {len(current_cookies)}")
        
        key_cookies = ['z_c0', 'SESSIONID', 'q_c1']
        for key in key_cookies:
            found = key in cookie_names
            print(f"  {key}: {'✅ 存在' if found else '❌ 缺失'}")
        
        # 检查页面内容
        page_source = spider.driver.page_source
        logged_in_indicators = ['退出登录', '我的主页', '用户中心', '消息通知']
        
        found_indicators = []
        for indicator in logged_in_indicators:
            if indicator in page_source:
                found_indicators.append(indicator)
        
        print(f"\n🔍 页面元素检查:")
        if found_indicators:
            print(f"✅ 找到登录后元素: {found_indicators}")
            print("🎉 登录状态正常！")
        else:
            print("❌ 未找到登录后元素，可能未登录")
        
        # 简单测试爬取功能
        print("\n🐛 测试简单爬取...")
        test_data = spider.crawl("上海迪士尼", target_count=2)
        print(f"测试爬取结果: {len(test_data)} 条数据")
        
        # 保存测试数据
        if test_data:
            csv_path = spider.save_comments_to_csv(test_data, "上海迪士尼测试")
            print(f"测试数据已保存到: {csv_path}")
        
        # 保持浏览器打开一段时间
        print("\n⏰ 浏览器将保持打开10秒，让你查看...")
        time.sleep(10)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'spider' in locals():
            spider.close()
        print("\n" + "=" * 80)
        print("测试完成！")
        print("=" * 80)

if __name__ == "__main__":
    test_zhihu_login()
