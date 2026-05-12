"""
调试用 - 查看微博页面结构
"""
import sys
import os
import json
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.config.config_manager import PROJECT_ROOT

def debug_page():
    project_root = str(PROJECT_ROOT)
    cookie_dir = os.path.join(project_root, 'cookies')
    os.makedirs(cookie_dir, exist_ok=True)

    with sync_playwright() as p:
        chrome_path = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
        launch_kwargs = {'headless': False, 'executable_path': chrome_path}
        browser = p.chromium.launch(**launch_kwargs)
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            locale='zh-CN',
        )
        page = context.new_page()
        Stealth().apply_stealth_sync(page)

        # 复用Cookie
        selenium_cookie = os.path.join(project_root, 'data', 'weibo_cookies.json')
        if os.path.exists(selenium_cookie):
            with open(selenium_cookie, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            converted = []
            for c in cookies:
                pc = {'name': c['name'], 'value': c['value'], 'domain': c.get('domain',''), 'path': c.get('path','/')}
                converted.append(pc)
            context.add_cookies(converted)

        print("访问微博搜索...")
        page.goto('https://s.weibo.com/weibo?q=上海迪士尼', wait_until='networkidle', timeout=60000)
        page.wait_for_timeout(5000)

        # 打印页面标题
        print(f"页面标题: {page.title()}")

        # 尝试找常见的容器类
        print("\n尝试查找可能的容器类...")
        possible_selectors = [
            '.card-wrap', '.feed-wrap', '.WB_cardwrap',
            '.m-con-l', '.pl_unlogin_home',
            '.list_li_s', '.s-search-wrap'
        ]
        for sel in possible_selectors:
            elements = page.query_selector_all(sel)
            print(f"  {sel}: {len(elements)}个")

        # 截图
        screenshot = os.path.join(project_root, 'debug_screenshot.png')
        page.screenshot(path=screenshot)
        print(f"\n✅ 截图已保存到: {screenshot}")

        # 下载页面源码
        html = page.content()
        html_path = os.path.join(project_root, 'debug_page.html')
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"✅ 页面源码已保存到: {html_path}")

        input("\n按 Enter 关闭浏览器...")
        browser.close()


if __name__ == "__main__":
    debug_page()
