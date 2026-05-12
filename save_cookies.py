# -*- coding: utf-8 -*-
"""
手动登录并保存Cookie
运行此脚本后，请在浏览器中手动登录，登录完成后按回车键保存cookie
"""

import time
import os
import json
import pickle
from selenium import webdriver
from selenium.webdriver.common.by import By

def save_cookies_login(platform="xiaohongshu"):
    """
    打开浏览器让用户手动登录，然后保存cookie
    
    Args:
        platform: 平台名称 (xiaohongshu, bilibili, douyin)
    """
    # 平台URL映射
    platform_urls = {
        "xiaohongshu": "https://www.xiaohongshu.com",
        "bilibili": "https://www.bilibili.com",
        "douyin": "https://www.douyin.com"
    }
    
    if platform not in platform_urls:
        print(f"[ERROR] 不支持的平台: {platform}")
        return None
    
    url = platform_urls[platform]
    cookie_file = f"data/cookies/{platform}_cookies.pkl"
    
    # 确保目录存在
    os.makedirs("data/cookies", exist_ok=True)
    
    print("\n" + "="*60)
    print(f"手动登录保存Cookie - {platform}")
    print("="*60)
    
    # 启动浏览器
    options = webdriver.EdgeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--start-maximized")
    
    driver = webdriver.Edge(options=options)
    
    try:
        # 访问平台
        print(f"\n[INFO] 正在打开 {url}")
        driver.get(url)
        
        print("\n" + "-"*60)
        print("请在浏览器中完成以下操作：")
        print("1. 点击登录按钮")
        print("2. 扫码或输入账号密码登录")
        print("3. 确保登录成功后，回到此窗口")
        print("-"*60)
        
        # 等待用户登录
        input("\n登录完成后，请按回车键保存Cookie...")
        
        # 获取cookies
        cookies = driver.get_cookies()
        
        # 保存cookies
        with open(cookie_file, 'wb') as f:
            pickle.dump(cookies, f)
        
        print(f"\n[SUCCESS] Cookie已保存到: {cookie_file}")
        print(f"[INFO] 共保存 {len(cookies)} 个Cookie")
        
        # 验证cookie是否有效
        print("\n[INFO] 验证Cookie有效性...")
        driver.delete_all_cookies()
        
        # 重新加载cookie
        for cookie in cookies:
            driver.add_cookie(cookie)
        
        # 刷新页面验证
        driver.refresh()
        time.sleep(3)
        
        print("[SUCCESS] Cookie验证成功！")
        
        return cookie_file
        
    except Exception as e:
        print(f"[ERROR] 保存Cookie失败: {e}")
        return None
    finally:
        print("\n[INFO] 5秒后关闭浏览器...")
        time.sleep(5)
        driver.quit()


def load_cookies(driver, platform="xiaohongshu"):
    """
    加载已保存的cookie到浏览器
    
    Args:
        driver: Selenium WebDriver
        platform: 平台名称
    """
    cookie_file = f"data/cookies/{platform}_cookies.pkl"
    
    if not os.path.exists(cookie_file):
        print(f"[WARN] Cookie文件不存在: {cookie_file}")
        return False
    
    try:
        with open(cookie_file, 'rb') as f:
            cookies = pickle.load(f)
        
        for cookie in cookies:
            # 移除可能导致问题的字段
            if 'expiry' in cookie:
                cookie['expiry'] = int(cookie['expiry'])
            try:
                driver.add_cookie(cookie)
            except Exception as e:
                print(f"[WARN] 添加Cookie失败: {e}")
        
        print(f"[SUCCESS] 已加载 {len(cookies)} 个Cookie")
        return True
        
    except Exception as e:
        print(f"[ERROR] 加载Cookie失败: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "#"*60)
    print("# Cookie保存工具")
    print("#"*60)
    
    print("\n请选择要登录的平台：")
    print("1. 小红书 (xiaohongshu)")
    print("2. B站 (bilibili)")
    print("3. 抖音 (douyin)")
    print("4. 全部登录")
    
    choice = input("\n请输入选项 (1/2/3/4): ").strip()
    
    platforms = {
        "1": ["xiaohongshu"],
        "2": ["bilibili"],
        "3": ["douyin"],
        "4": ["xiaohongshu", "bilibili", "douyin"]
    }
    
    selected = platforms.get(choice, ["xiaohongshu"])
    
    for platform in selected:
        save_cookies_login(platform)
        print("\n")
    
    print("\n" + "#"*60)
    print("# 所有Cookie保存完成！")
    print("# 现在可以运行爬虫了")
    print("#"*60)
