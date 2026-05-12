"""
调试微博详情页
"""
import os
import sys
import json
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.config.config_manager import PROJECT_ROOT

project_root = str(PROJECT_ROOT)
cookie_file = os.path.join(project_root, 'cookies', 'weibo_playwright.json')

with sync_playwright() as p:
    chrome_path = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
    browser = p.chromium.launch(headless=False, executable_path=chrome_path)
    context = browser.new_context(
        viewport={'width': 375, 'height': 812},
        user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15',
    )
    page = context.new_page()
    Stealth().apply_stealth_sync(page)

    if os.path.exists(cookie_file):
        with open(cookie_file, 'r') as f:
            cookies = json.load(f)
        context.add_cookies(cookies)

    page.goto('https://m.weibo.cn', wait_until='domcontentloaded', timeout=60000)
    page.wait_for_timeout(3000)

    # 搜索
    page.goto('https://m.weibo.cn/search?containerid=100103type%3D1%26q%3D上海迪士尼', wait_until='domcontentloaded', timeout=60000)
    page.wait_for_timeout(5000)

    for i in range(5):
        page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        page.wait_for_timeout(1000)

    # 找一个card
    cards = page.query_selector_all('.card9') or page.query_selector_all('.card')
    print(f"找到 {len(cards)} 个卡片")

    if cards:
        card = cards[1]  # 取第二条（有内容的）
        print(f"\n卡片信息:")
        print(f"  HTML: {card.inner_html()[:500]}")
        print(f"  Text: {card.inner_text()[:200]}")

        # 尝试获取链接
        links = card.query_selector_all('a')
        print(f"\n链接数量: {len(links)}")
        for i, link in enumerate(links[:5]):
            href = link.get_attribute('href') or ''
            text = link.inner_text()[:30]
            print(f"  [{i}] href={href} text={text}")

    browser.close()
