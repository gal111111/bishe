# -*- coding: utf-8 -*-
"""
单独保存抖音Cookie - 长时间等待版
"""

import time
import os
import pickle
from selenium import webdriver

def save_douyin_cookies():
    """
    保存抖音的Cookie - 等待时间更长
    """
    url = "https://www.douyin.com"
    cookie_file = "data/cookies/douyin_cookies.pkl"
    
    os.makedirs("data/cookies", exist_ok=True)
    
    print("\n" + "="*60)
    print("抖音 Cookie 保存工具（长时间等待版）")
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
        
        print(f"\n[INFO] 请在浏览器中登录抖音")
        print("[INFO] 包括输入验证码等操作")
        print("[INFO] 登录成功后，我会等待120秒让您确认")
        print("[INFO] 请确保完全登录后再继续")
        
        # 等待120秒让用户登录
        for i in range(120, 0, -1):
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
    save_douyin_cookies()
