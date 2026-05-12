"""
微博登录脚本 - 自动检测登录状态，无需手动输入
"""
import sys
import os
import json
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.config.config_manager import PROJECT_ROOT


def login_weibo_pc():
    project_root = str(PROJECT_ROOT)
    cookie_dir = os.path.join(project_root, 'cookies')
    os.makedirs(cookie_dir, exist_ok=True)
    cookie_file = os.path.join(cookie_dir, 'weibo_playwright.json')

    print(f"\n{'='*60}")
    print(f"🔐 微博PC端登录")
    print(f"{'='*60}")
    print(f"即将打开Chrome浏览器，请在浏览器中登录微博！")
    print(f"脚本会自动检测登录状态，登录成功后自动保存Cookie")
    print(f"{'='*60}\n")

    with sync_playwright() as p:
        chrome_path = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
        browser = p.chromium.launch(
            headless=False,
            executable_path=chrome_path,
            args=['--disable-blink-features=AutomationControlled']
        )
        context = browser.new_context(
            viewport={'width': 1440, 'height': 900},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='zh-CN',
        )
        page = context.new_page()
        Stealth().apply_stealth_sync(page)

        # 加载旧Cookie
        if os.path.exists(cookie_file):
            with open(cookie_file, 'r') as f:
                cookies = json.load(f)
            context.add_cookies(cookies)
            print(f"✓ 已加载旧Cookie: {len(cookies)}个")

        # 访问微博
        page.goto('https://weibo.com', wait_until='domcontentloaded', timeout=60000)
        page.wait_for_timeout(3000)

        # 检查是否已登录
        logged_in = False
        for attempt in range(60):  # 最多等60秒
            title = page.title()
            current_url = page.url

            # 如果页面标题不包含"登录"，说明已登录
            if '登录' not in title and 'newlogin' not in current_url:
                logged_in = True
                break

            print(f"⏳ 等待登录... ({attempt+1}/60) 标题: {title}")
            page.wait_for_timeout(3000)

        if logged_in:
            # 保存Cookie
            cookies = context.cookies()
            with open(cookie_file, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)

            print(f"\n✅ 登录成功！Cookie已保存！")
            print(f"   Cookie数量: {len(cookies)}")
            print(f"   保存路径: {cookie_file}")

            # 验证
            page.goto('https://weibo.com', wait_until='domcontentloaded', timeout=30000)
            page.wait_for_timeout(2000)
            title = page.title()
            print(f"   页面标题: {title}")
        else:
            print(f"\n⚠️ 等待超时，请确认是否已登录")

        browser.close()

    print(f"\n✅ 登录流程完成！")


if __name__ == "__main__":
    login_weibo_pc()
