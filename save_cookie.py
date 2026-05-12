"""
快速保存Cookie - 从已登录的浏览器中获取Cookie
"""
import os
import json
from playwright.sync_api import sync_playwright
from src.config.config_manager import PROJECT_ROOT

project_root = str(PROJECT_ROOT)
cookie_dir = os.path.join(project_root, 'cookies')
os.makedirs(cookie_dir, exist_ok=True)
cookie_file = os.path.join(cookie_dir, 'weibo_playwright.json')

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

    # 先加载已有的Playwright Cookie（如果刚才登录脚本保存了）
    if os.path.exists(cookie_file):
        with open(cookie_file, 'r', encoding='utf-8') as f:
            cookies = json.load(f)
        context.add_cookies(cookies)
        print(f"加载已有Cookie: {len(cookies)}个")

    # 访问微博，看是否已登录
    page.goto('https://weibo.com', wait_until='domcontentloaded', timeout=60000)
    page.wait_for_timeout(5000)

    title = page.title()
    print(f"页面标题: {title}")

    # 保存Cookie
    cookies = context.cookies()
    with open(cookie_file, 'w', encoding='utf-8') as f:
        json.dump(cookies, f, ensure_ascii=False, indent=2)

    print(f"Cookie已保存: {len(cookies)}个")
    has_sub = [c for c in cookies if 'SUB' in c.get('name', '')]
    if has_sub:
        print("✅ 检测到SUB Cookie，登录成功！")
    else:
        print("❌ 未检测到SUB Cookie，可能需要重新登录")

    browser.close()
