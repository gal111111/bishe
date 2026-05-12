"""
调试 - 查看微博搜索页面实际结构
"""
import os
import json
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
from src.config.config_manager import PROJECT_ROOT

project_root = str(PROJECT_ROOT)
cookie_file = os.path.join(project_root, 'cookies', 'weibo_playwright.json')

with sync_playwright() as p:
    chrome_path = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
    browser = p.chromium.launch(headless=False, executable_path=chrome_path)
    context = browser.new_context(
        viewport={'width': 1280, 'height': 800},
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        locale='zh-CN',
    )
    page = context.new_page()
    Stealth().apply_stealth_sync(page)

    # 加载Cookie
    if os.path.exists(cookie_file):
        with open(cookie_file, 'r', encoding='utf-8') as f:
            cookies = json.load(f)
        context.add_cookies(cookies)
        print(f"✓ Cookie已加载: {len(cookies)}个")

    # 访问搜索页
    page.goto('https://s.weibo.com/weibo?q=上海迪士尼', wait_until='networkidle', timeout=60000)
    page.wait_for_timeout(5000)

    title = page.title()
    print(f"页面标题: {title}")

    # 尝试各种选择器
    selectors = [
        '.card-wrap',
        '.card',
        '[action-type="feed_list_item"]',
        '.WB_cardwrap',
        '.m-con-b',
        '.pl_weibo_direct',
        '#pl_feedlist_index',
        '.feed_list',
        '.s-fr',
        'article',
        '.wrap',
        '.searchfeed',
        '.sw_card',
        'div[class*="card"]',
        'div[class*="feed"]',
        'div[class*="item"]',
        'div[class*="list"]',
        'div[class*="weibo"]',
        'div[class*="content"]',
        'div[class*="result"]',
        'li',
        'tbody tr',
    ]

    for sel in selectors:
        try:
            elements = page.query_selector_all(sel)
            if elements:
                print(f"  ✅ {sel}: {len(elements)}个")
        except:
            pass

    # 截图
    screenshot = os.path.join(project_root, 'debug_search.png')
    page.screenshot(path=screenshot, full_page=True)
    print(f"\n截图: {screenshot}")

    # 保存HTML
    html = page.content()
    html_path = os.path.join(project_root, 'debug_search.html')
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"HTML: {html_path}")

    # 打印HTML前3000字符
    print(f"\n页面HTML前3000字符:")
    print(html[:3000])

    browser.close()
