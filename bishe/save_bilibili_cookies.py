# -*- coding: utf-8 -*-
"""
单独保存B站Cookie
"""

import time
import os
import pickle
from selenium import webdriver

def save_bilibili_cookies():
    """
    保存B站的Cookie
    """
    url = "https://www.bilibili.com"
    cookie_file = "data/cookies/bilibili_cookies.pkl"
    
    os.makedirs("data/cookies", exist_ok=True)
    
    print("\n" + "="*60)
    print("B站 Cookie 保存工具")
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
        
        print(f"\n[INFO] 请在浏览器中登录B站")
        print("[INFO] 登录成功后，我会等待60秒让您确认")
        
        # 等待60秒让用户登录
        for i in range(60, 0, -1):
            print(f"\r[INFO] 等待登录... {i}秒", end="")
            time.sleep(1)
        
        print(f"\n\n[INFO] 正在保存Cookie...")
        
        # 获取并保存cookies
        cookies = driver.get_cookies()
        with open(cookie_file, 'wb') as f:
            pickle.dump(cookies, f)
        
        print(f"[SUCCESS] Cookie已保存到: {cookie_file}")
        print(f"[INFO] 共保存 {len(cookies)} 个Cookie")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 保存Cookie失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        print(f"\n[INFO] 关闭浏览器...")
        time.sleep(2)
        try:
            driver.quit()
        except:
            pass


if __name__ == "__main__":
    save_bilibili_cookies()
