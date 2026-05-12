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
print("即将打开Chrome浏览器")
print("请在浏览器中扫码或输入账号登录")
print(f"{'='*60}\n")

with sync_playwright() as p:
    chrome_path = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
    browser = p.chromium.launch(
        headless=False,
        executable_path=chrome_path,
        args=['--disable-blink-features=AutomationControlled']
    )

    context = browser.new_context(
        viewport={'width': 1280, 'height': 800},
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    )
    page = context.new_page()

    # 先访问微博首页
    page.goto('https://weibo.com', wait_until='domcontentloaded', timeout=60000)

    print("🟢 Chrome浏览器已打开")
    print("请在浏览器中登录微博")
    print("\n登录成功后，回到这里按 Ctrl+C 保存Cookie")

    # 保持浏览器打开，直到用户中断
    try:
        while True:
            time.sleep(2)
            # 检查是否已登录
            try:
                current_title = page.title()
                if '登录' not in current_title and '微博' in current_title:
                    print(f"✅ 检测到已登录（当前页面：{current_title}）")
            except:
                pass
    except KeyboardInterrupt:
        print("\n\n保存Cookie...")

    # 保存Cookie
    cookies = context.cookies()
    with open(cookie_file, 'w', encoding='utf-8') as f:
        json.dump(cookies, f, ensure_ascii=False, indent=2)

    print(f"✅ Cookie已保存到: {cookie_file}")
    print(f"✅ 现在可以运行爬虫了！")

    browser.close()
