# -*- coding: utf-8 -*-
"""
简单的Cookie保存脚本 - 不需要输入
打开浏览器后，用户扫码登录，脚本自动保存Cookie
"""

import time
import os
import pickle
import sys
from selenium import webdriver

def save_cookies_auto():
    url = "https://www.xiaohongshu.com"
    cookie_file = "data/cookies/xiaohongshu_cookies.pkl"
    
    os.makedirs("data/cookies", exist_ok=True)
    
    print("\n" + "="*60)
    print("小红书Cookie保存工具")
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
        print("[INFO] 登录成功后脚本会自动等待30秒，然后保存Cookie")
        
        # 等待30秒让用户登录
        for i in range(30, 0, -1):
            print(f"\r[INFO] 等待登录... {i}秒", end="")
            time.sleep(1)
        
        print(f"\n\n[INFO] 正在获取Cookie...")
        
        # 获取cookies
        cookies = driver.get_cookies()
        
        # 保存cookies
        with open(cookie_file, 'wb') as f:
            pickle.dump(cookies, f)
        
        print(f"[SUCCESS] Cookie已保存到: {cookie_file}")
        print(f"[INFO] 共保存 {len(cookies)} 个Cookie")
        
        return cookie_file
        
    except Exception as e:
        print(f"[ERROR] 保存Cookie失败: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        print("\n[INFO] 5秒后关闭浏览器...")
        time.sleep(5)
        try:
            driver.quit()
        except:
            pass


if __name__ == "__main__":
    save_cookies_auto()
