"""
微博评论爬虫 - 使用Playwright访问详情页提取评论
"""
import os
import sys
import json
import re
import pandas as pd
from datetime import datetime
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.config.config_manager import PROJECT_ROOT


def crawl_weibo_with_comments(keyword, target_posts=10):
    project_root = str(PROJECT_ROOT)
    cookie_dir = os.path.join(project_root, 'cookies')
    os.makedirs(cookie_dir, exist_ok=True)
    cookie_file = os.path.join(cookie_dir, 'weibo_playwright.json')

    raw_dir = os.path.join(project_root, 'data', 'raw')
    os.makedirs(raw_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    print(f"\n{'='*60}")
    print(f"🎯 微博评论爬虫 - 关键词: {keyword}")
    print(f"{'='*60}")

    posts_data = []
    comments_data = []

    # 第一步：获取微博列表
    print(f"\n📝 第一步：获取微博列表...")
    weibo_ids = []

    with sync_playwright() as p:
        chrome_path = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
        browser = p.chromium.launch(
            headless=False,
            executable_path=chrome_path,
            args=['--disable-blink-features=AutomationControlled']
        )
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

        # 访问m.weibo.cn
        page.goto('https://m.weibo.cn', wait_until='domcontentloaded', timeout=60000)
        page.wait_for_timeout(3000)

        # 搜索
        search_url = f'https://m.weibo.cn/search?containerid=100103type%3D1%26q%3D{keyword}'
        page.goto(search_url, wait_until='domcontentloaded', timeout=60000)
        page.wait_for_timeout(5000)

        # 滚动加载
        for i in range(10):
            page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            page.wait_for_timeout(1500)

        # 获取微博卡片
        cards = page.query_selector_all('.card9')
        if not cards:
            cards = page.query_selector_all('.card')

        print(f"   找到 {len(cards)} 条微博")

        for idx, card in enumerate(cards[:target_posts]):
            try:
                # 提取微博ID
                post_id = ''
                for sel in ['a[href*="/detail/"]', '.weibo-main a']:
                    link_el = card.query_selector(sel)
                    if link_el:
                        href = link_el.get_attribute('href') or ''
                        match = re.search(r'/detail/(\d+)', href)
                        if match:
                            post_id = match.group(1)
                            break

                # 提取微博信息
                author = ''
                author_el = card.query_selector('.m-text-box .m-text-cut') or card.query_selector('h3.m-text-cut')
                if author_el:
                    author = author_el.inner_text().strip()

                content = ''
                content_el = card.query_selector('.weibo-main') or card.query_selector('.weibo-text') or card.query_selector('.m-text-box')
                if content_el:
                    content = content_el.inner_text().strip()

                time_str = datetime.now().strftime('%Y-%m-%d')
                time_el = card.query_selector('.time')
                if time_el:
                    time_str = time_el.inner_text().strip()

                if not content:
                    continue

                weibo_ids.append(post_id)
                posts_data.append({
                    'platform': '微博',
                    'post_id': post_id,
                    'author': author,
                    'content': content[:500],
                    'publish_time': time_str,
                    'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
                print(f"  [{idx+1}] {author}: {content[:30]}... (ID: {post_id})")

            except Exception as e:
                continue

        # 保存Cookie
        cookies = context.cookies()
        with open(cookie_file, 'w', encoding='utf-8') as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)

        browser.close()

    # 第二步：访问每条微博的详情页获取评论
    print(f"\n{'='*60}")
    print(f"💬 第二步：进入详情页获取评论...")
    print(f"{'='*60}")

    for idx, post in enumerate(posts_data):
        post_id = post['post_id']
        if not post_id:
            continue

        print(f"\n[{idx+1}/{len(posts_data)}] 进入微博详情页...")

        with sync_playwright() as p:
            chrome_path = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
            browser = p.chromium.launch(
                headless=False,
                executable_path=chrome_path,
                args=['--disable-blink-features=AutomationControlled']
            )
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

            # 访问微博详情页
            detail_url = f'https://m.weibo.cn/detail/{post_id}'
            print(f"   ➡️  {detail_url}")
            page.goto(detail_url, wait_until='domcontentloaded', timeout=60000)
            page.wait_for_timeout(5000)

            # 滚动加载评论
            print(f"   ⬇️  滚动加载评论...")
            for i in range(10):
                page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                page.wait_for_timeout(1000)

            # 获取页面HTML，检查评论区域
            page_text = page.inner_text('body')

            # 尝试多种评论选择器
            comment_selectors = [
                '.comment-list .comment-item',
                '.comment-item',
                'div[class*="comment"]',
                '.list .item',
                '.comment',
                '.list-li',
                'div[class*="item"]',
                'li',
            ]

            found_comments = False
            for sel in comment_selectors:
                items = page.query_selector_all(sel)
                if items and len(items) > 1:
                    print(f"   ✅ 用选择器 '{sel}' 找到 {len(items)} 个元素")
                    found_comments = True

                    for item in items[:30]:
                        try:
                            text = item.inner_text().strip()
                            if text and len(text) > 5 and text != post['content'][:50]:
                                # 尝试提取评论作者
                                author_sel = ['.name', '.user-name', 'h4', 'span', '.author']
                                c_author = ''
                                for a_sel in author_sel:
                                    author_el = item.query_selector(a_sel)
                                    if author_el:
                                        c_author = author_el.inner_text().strip()
                                        break

                                if not c_author:
                                    # 如果没找到作者，取第一行作为作者
                                    lines = text.split('\n')
                                    if lines:
                                        c_author = lines[0][:20]

                                # 去除作者名，取评论内容
                                comment_text = text
                                if c_author and c_author in comment_text:
                                    comment_text = comment_text.replace(c_author, '', 1)

                                if len(comment_text) > 3:
                                    comments_data.append({
                                        'platform': '微博',
                                        'post_id': post_id,
                                        'post_author': post['author'],
                                        'post_content': post['content'][:50],
                                        'comment_author': c_author,
                                        'comment': comment_text[:500],
                                        'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                    })
                                    print(f"      💬 {c_author}: {comment_text[:30]}...")
                        except:
                            continue
                    break

            if not found_comments:
                print(f"   ⚠️ 未找到评论区域")

            browser.close()

    # 保存数据
    print(f"\n{'='*60}")
    print(f"📊 爬取完成！")
    print(f"   微博数量: {len(posts_data)}")
    print(f"   评论数量: {len(comments_data)}")

    if posts_data:
        posts_csv = os.path.join(raw_dir, f'weibo_posts_{keyword.replace(" ","_")}_{timestamp}.csv')
        pd.DataFrame(posts_data).to_csv(posts_csv, index=False, encoding='utf-8-sig')
        print(f"✅ 微博数据已保存: {posts_csv}")

    if comments_data:
        comments_csv = os.path.join(raw_dir, f'weibo_comments_{keyword.replace(" ","_")}_{timestamp}.csv')
        pd.DataFrame(comments_data).to_csv(comments_csv, index=False, encoding='utf-8-sig')
        print(f"✅ 评论数据已保存: {comments_csv}")

    return pd.DataFrame(posts_data), pd.DataFrame(comments_data)


if __name__ == "__main__":
    posts_df, comments_df = crawl_weibo_with_comments("上海迪士尼", 10)
