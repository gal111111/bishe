"""
Playwright微博爬虫 - 使用移动端m.weibo.cn
移动端更友好，搜索不需要额外登录
"""
import os
import json
import pandas as pd
from datetime import datetime
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
from src.config.config_manager import PROJECT_ROOT

def crawl_weibo(keyword, target_count=20):
    project_root = str(PROJECT_ROOT)
    cookie_dir = os.path.join(project_root, 'cookies')
    os.makedirs(cookie_dir, exist_ok=True)
    cookie_file = os.path.join(cookie_dir, 'weibo_playwright.json')

    raw_dir = os.path.join(project_root, 'data', 'raw')
    os.makedirs(raw_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = os.path.join(raw_dir, f'weibo_playwright_{keyword.replace(" ","_")}_{timestamp}.csv')

    print(f"\n{'='*60}")
    print(f"🎯 Playwright微博爬虫 - 关键词: {keyword}")
    print(f"{'='*60}")

    data_list = []

    with sync_playwright() as p:
        chrome_path = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
        browser = p.chromium.launch(
            headless=False,
            executable_path=chrome_path,
            args=['--disable-blink-features=AutomationControlled']
        )

        # 使用移动端UA和视口
        context = browser.new_context(
            viewport={'width': 375, 'height': 812},
            user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
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

        # 先访问m.weibo.cn激活Cookie
        print(f"➡️  访问m.weibo.cn...")
        page.goto('https://m.weibo.cn', wait_until='domcontentloaded', timeout=60000)
        page.wait_for_timeout(3000)

        title = page.title()
        print(f"   页面标题: {title}")

        # 搜索
        search_url = f'https://m.weibo.cn/search?containerid=100103type%3D1%26q%3D{keyword}'
        print(f"🔍 搜索: {keyword}")
        page.goto(search_url, wait_until='domcontentloaded', timeout=60000)
        page.wait_for_timeout(5000)

        print(f"   搜索页标题: {page.title()}")
        print(f"   当前URL: {page.url}")

        # 滚动加载
        print(f"⬇️  滚动加载...")
        for i in range(10):
            page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            page.wait_for_timeout(1500)

        # 提取数据
        print(f"📝 提取微博内容...")

        # m.weibo.cn 的卡片选择器
        cards = page.query_selector_all('.card.m-panel.card9.weibo-member')
        if not cards:
            cards = page.query_selector_all('.card9')
        if not cards:
            cards = page.query_selector_all('.card')
        if not cards:
            cards = page.query_selector_all('div[class*="card"]')

        print(f"   找到 {len(cards)} 条微博卡片")

        for idx, card in enumerate(cards[:target_count]):
            try:
                # 作者
                author = ''
                author_el = card.query_selector('.m-text-box .m-text-cut')
                if not author_el:
                    author_el = card.query_selector('h3.m-text-cut')
                if not author_el:
                    author_el = card.query_selector('.m-text-cut a')
                if author_el:
                    author = author_el.inner_text().strip()

                # 内容
                content = ''
                content_el = card.query_selector('.weibo-main')
                if not content_el:
                    content_el = card.query_selector('.weibo-text')
                if not content_el:
                    content_el = card.query_selector('.m-text-box')
                if content_el:
                    content = content_el.inner_text().strip()

                # 时间
                time_str = datetime.now().strftime('%Y-%m-%d')
                time_el = card.query_selector('.time')
                if not time_el:
                    time_el = card.query_selector('.m-diy-btn.m-font-time')
                if time_el:
                    time_str = time_el.inner_text().strip()

                if content:
                    data = {
                        'platform': '微博',
                        'title': content[:30] + '...' if len(content) > 30 else content,
                        'content': content[:500],
                        'publish_time': time_str,
                        'author': author,
                        'like_count': 0,
                        'comment_count': 0,
                        'repost_count': 0,
                        'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    data_list.append(data)
                    print(f"  [{len(data_list)}] {author or '匿名'}: {content[:40]}...")

            except:
                continue

        # 保存Cookie
        cookies = context.cookies()
        with open(cookie_file, 'w', encoding='utf-8') as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)

        browser.close()

    print(f"\n{'='*60}")
    if data_list:
        df = pd.DataFrame(data_list)
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"✅ 成功爬取 {len(data_list)} 条微博")
        print(f"✅ 已保存到: {csv_path}")
        return df
    else:
        print(f"❌ 未爬取到数据")
        return None


if __name__ == "__main__":
    crawl_weibo("上海迪士尼", 20)
