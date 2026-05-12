"""
Playwright登录脚本 - 运行后弹出浏览器，登录后自动保存Cookie
用法：python3 login_playwright.py weibo
"""
import sys
import os
import json
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
from src.config.config_manager import PROJECT_ROOT

_stealth = Stealth()

PLATFORMS = {
    'weibo': 'https://login.sina.com.cn/signup/signin.php',
    'zhihu': 'https://www.zhihu.com/signin',
    'tieba': 'https://passport.baidu.com/v2/?login',
    'douyin': 'https://www.douyin.com',
    'xiaohongshu': 'https://www.xiaohongshu.com',
    'bilibili': 'https://passport.bilibili.com/login'
}

def login(platform: str):
    project_root = str(PROJECT_ROOT)
    cookie_dir = os.path.join(project_root, 'cookies')
    os.makedirs(cookie_dir, exist_ok=True)
    cookie_file = os.path.join(cookie_dir, f'{platform}_playwright.json')

    print(f"\n{'='*60}")
    print(f"🔐 {platform} 登录工具")
    print(f"{'='*60}")
    print(f"即将打开浏览器，请在浏览器中完成登录")
    print(f"登录完成后回到终端按 Enter 键")
    print(f"{'='*60}\n")

    with sync_playwright() as p:
        chrome_path = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
        launch_kwargs = {
            'headless': False,
            'args': [
                '--disable-blink-features=AutomationControlled',
                '--disable-infobars',
                '--no-first-run',
            ]
        }
        if os.path.exists(chrome_path):
            launch_kwargs['executable_path'] = chrome_path
            print(f"✓ 使用系统Chrome")

        browser = p.chromium.launch(**launch_kwargs)
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},
            locale='zh-CN',
            timezone_id='Asia/Shanghai',
        )
        page = context.new_page()
        _stealth.apply_stealth_sync(page)

        # 尝试加载已有Cookie
        if os.path.exists(cookie_file):
            try:
                with open(cookie_file, 'r', encoding='utf-8') as f:
                    cookies = json.load(f)
                context.add_cookies(cookies)
                print(f"✓ 已加载之前的Cookie")
            except:
                pass

        # 也尝试加载Selenium的Cookie
        selenium_cookie = os.path.join(project_root, 'data', f'{platform}_cookies.json')
        if os.path.exists(selenium_cookie):
            try:
                with open(selenium_cookie, 'r', encoding='utf-8') as f:
                    cookies = json.load(f)
                converted = []
                for c in cookies:
                    pc = {
                        'name': c.get('name', ''),
                        'value': c.get('value', ''),
                        'domain': c.get('domain', ''),
                        'path': c.get('path', '/'),
                    }
                    if 'expiry' in c:
                        pc['expires'] = c['expiry']
                    if 'secure' in c:
                        pc['secure'] = c['secure']
                    converted.append(pc)
                if converted:
                    context.add_cookies(converted)
                    print(f"✓ 已复用Selenium的Cookie")
            except:
                pass

        # 打开登录页面
        login_url = PLATFORMS.get(platform, f'https://{platform}.com')
        page.goto(login_url, wait_until='domcontentloaded')

        print(f"\n🔐 请在浏览器中完成 {platform} 登录...")
        input(f"⏸ 登录完成后按 Enter 继续: ")

        # 保存Cookie
        cookies = context.cookies()
        with open(cookie_file, 'w', encoding='utf-8') as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)

        print(f"✅ Cookie已保存到: {cookie_file}")
        print(f"✅ 下次运行无需再登录！")

        browser.close()

    print(f"\n🎉 登录完成！现在可以使用Playwright爬虫了")


if __name__ == "__main__":
    platform = sys.argv[1] if len(sys.argv) > 1 else "weibo"
    login(platform)
