# -*- coding: utf-8 -*-
"""
快速登录小红书并保存Cookie
"""

import time
import os
import pickle
from selenium import webdriver

def save_xiaohongshu_cookies():
    """
    打开小红书让用户扫码登录，然后保存cookie
    """
    url = "https://www.xiaohongshu.com"
    cookie_file = "data/cookies/xiaohongshu_cookies.pkl"
    
    # 确保目录存在
    os.makedirs("data/cookies", exist_ok=True)
    
    print("\n" + "="*60)
    print("小红书 Cookie 保存工具")
    print("="*60)
    
    # 启动浏览器
    options = webdriver.EdgeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--start-maximized")
    
    driver = webdriver.Edge(options=options)
    
    try:
        print(f"\n[INFO] 正在打开 {url}")
        driver.get(url)
        
        print("\n" + "-"*60)
        print("请在浏览器中扫码登录小红书")
        print("登录成功后，回到此窗口按回车键")
        print("-"*60)
        
        # 等待用户登录
        input("\n按回车键保存Cookie...")
        
        # 获取cookies
        cookies = driver.get_cookies()
        
        # 保存cookies
        with open(cookie_file, 'wb') as f:
            pickle.dump(cookies, f)
        
        print(f"\n[SUCCESS] Cookie已保存到: {cookie_file}")
        print(f"[INFO] 共保存 {len(cookies)} 个Cookie")
        
        return cookie_file
        
    except Exception as e:
        print(f"[ERROR] 保存Cookie失败: {e}")
        return None
    finally:
        print("\n[INFO] 5秒后关闭浏览器...")
        time.sleep(5)
        driver.quit()


if __name__ == "__main__":
    save_xiaohongshu_cookies()
