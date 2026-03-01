# -*- coding: utf-8 -*-
"""
保存所有平台的Cookie - 逐个登录
"""

import time
import os
import pickle
from selenium import webdriver

def save_cookies_for_platform(platform_name, url):
    """
    保存指定平台的Cookie
    
    Args:
        platform_name: 平台名称
        url: 平台URL
    """
    cookie_file = f"data/cookies/{platform_name}_cookies.pkl"
    
    os.makedirs("data/cookies", exist_ok=True)
    
    print("\n" + "="*60)
    print(f"{platform_name} Cookie 保存工具")
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
        
        print(f"\n[INFO] 请在浏览器中登录{platform_name}")
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
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 保存Cookie失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        print(f"\n[INFO] 关闭{platform_name}浏览器...")
        time.sleep(2)
        try:
            driver.quit()
        except:
            pass


if __name__ == "__main__":
    print("\n" + "#"*60)
    print("# 多平台Cookie保存工具")
    print("#"*60)
    
    platforms = [
        ("bilibili", "https://www.bilibili.com"),
        ("douyin", "https://www.douyin.com")
    ]
    
    for name, url in platforms:
        success = save_cookies_for_platform(name, url)
        if success:
            print(f"\n[INFO] {name} Cookie保存成功！")
        else:
            print(f"\n[WARN] {name} Cookie保存失败！")
        
        time.sleep(2)
    
    print("\n" + "#"*60)
    print("# 所有平台Cookie保存完成！")
    print("#"*60)
