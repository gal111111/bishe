"""
简单的登录脚本 - 直接打开Chrome让你登录
"""
import os
import json
import time
from playwright.sync_api import sync_playwright
from src.config.config_manager import PROJECT_ROOT

project_root = str(PROJECT_ROOT)
cookie_dir = os.path.join(project_root, 'cookies')
os.makedirs(cookie_dir, exist_ok=True)
cookie_file = os.path.join(cookie_dir, 'weibo_playwright.json')

print(f"\n{'='*60}")
print("🔐 微博登录工具")
print(f"{'='*60}")
print("正在打开Chrome浏览器，请扫码登录...")

with sync_playwright() as p:
    chrome_path = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
    browser = p.chromium.launch(
        headless=False,
        executable_path=chrome_path,
        args=['--disable-blink-features=AutomationControlled']
    )
    context = browser.new_context(
        viewport={'width': 1280, 'height': 800},
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    )
    page = context.new_page()
    page.goto('https://weibo.com', wait_until='domcontentloaded', timeout=60000)

    print("🟢 Chrome浏览器已打开")
    print(f"{'='*60}")
    print("等待120秒，请尽快扫码登录！")
    print(f"{'='*60}\n")

    time.sleep(120)

    print("\n保存Cookie...")
    cookies = context.cookies()
    with open(cookie_file, 'w', encoding='utf-8') as f:
        json.dump(cookies, f, ensure_ascii=False, indent=2)

    print(f"✅ Cookie已保存到: {cookie_file}")
    print(f"✅ Cookie数量: {len(cookies)}")

    # 测试一下是否登录成功
    test_cookies = context.cookies()
    has_sub = [c for c in test_cookies if 'SUB' in c.get('name','')]
    has_subp = [c for c in test_cookies if 'SUBP' in c.get('name','')]
    if has_sub or has_subp:
        print(f"✅ 检测到微博关键Cookie，应该登录成功了！")

    print(f"\n现在可以运行爬虫了！")

    browser.close()
