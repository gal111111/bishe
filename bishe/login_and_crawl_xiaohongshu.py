# -*- coding: utf-8 -*-
"""
简单的登录+爬虫脚本
1. 打开浏览器让用户扫码登录
2. 自动保存Cookie
3. 运行爬虫爬取评论
"""

import time
import os
import pickle
import sys
from selenium import webdriver

def save_cookies_and_crawl():
    url = "https://www.xiaohongshu.com"
    cookie_file = "data/cookies/xiaohongshu_cookies.pkl"
    
    os.makedirs("data/cookies", exist_ok=True)
    
    print("\n" + "="*60)
    print("小红书登录+爬虫工具")
    print("="*60)
    
    options = webdriver.EdgeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--start-maximized")
    
    driver = webdriver.Edge(options=options)
    
    try:
        print(f"\n[INFO] 正在打开 {url}")
        driver.get(url)
        
        print("\n[INFO] 请在浏览器中扫码登录小红书")
        print("[INFO] 登录成功后，我会等待30秒让您确认")
        
        # 等待30秒让用户登录
        for i in range(30, 0, -1):
            print(f"\r[INFO] 等待登录... {i}秒", end="")
            time.sleep(1)
        
        print(f"\n\n[INFO] 正在保存Cookie...")
        
        # 获取并保存cookies
        cookies = driver.get_cookies()
        with open(cookie_file, 'wb') as f:
            pickle.dump(cookies, f)
        
        print(f"[SUCCESS] Cookie已保存到: {cookie_file}")
        print(f"[INFO] 共保存 {len(cookies)} 个Cookie")
        
        # 关闭浏览器
        print("\n[INFO] 关闭浏览器...")
        driver.quit()
        
        # 现在运行爬虫
        print("\n" + "="*60)
        print("开始运行小红书爬虫")
        print("="*60)
        
        from src.crawlers.selenium_spiders.xiaohongshu_selenium_spider import XiaohongshuSpider
        
        spider = XiaohongshuSpider(use_edge=True)
        spider.run("上海迪士尼", max_posts=5, max_comments_per_post=20)
        
    except Exception as e:
        print(f"[ERROR] 出错了: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            driver.quit()
        except:
            pass


if __name__ == "__main__":
    save_cookies_and_crawl()
