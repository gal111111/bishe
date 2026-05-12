"""
微博评论爬虫 - 直接访问评论页
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

    with sync_playwright() as p:
        chrome_path = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
        browser = p.chromium.launch(
            headless=False,
            executable_path=chrome_path,
            args=['--disable-blink-features=AutomationControlled']
        )

        # 使用PC端UA
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
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

        # 访问微博
        print(f"\n📝 获取微博列表...")
        page.goto('https://weibo.com', wait_until='domcontentloaded', timeout=60000)
        page.wait_for_timeout(3000)

        # 搜索
        search_url = f'https://s.weibo.com/weibo?q={keyword}'
        print(f"🔍 搜索: {keyword}")
        page.goto(search_url, wait_until='networkidle', timeout=60000)
        page.wait_for_timeout(5000)

        # 滚动加载
        print(f"⬇️  滚动加载...")
        for i in range(10):
            page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            page.wait_for_timeout(1500)

        # 获取微博卡片
        cards = page.query_selector_all('.card-wrap')
        if not cards:
            cards = page.query_selector_all('[action-type="feed_list_item"]')
        if not cards:
            cards = page.query_selector_all('.WB_cardwrap')

        print(f"   找到 {len(cards)} 条微博")

        for idx, card in enumerate(cards[:target_posts]):
            try:
                # 提取微博信息
                author = ''
                author_el = card.query_selector('.name') or card.query_selector('a[usercard]') or card.query_selector('.W_f14')
                if author_el:
                    author = author_el.inner_text().strip()

                content = ''
                content_el = card.query_selector('.txt')
                if not content_el:
                    content_el = card.query_selector('.WB_text')
                if content_el:
                    content = content_el.inner_text().strip()

                time_str = datetime.now().strftime('%Y-%m-%d')
                time_el = card.query_selector('[node-type="feed_list_item_date"]')
                if time_el:
                    time_str = time_el.get_attribute('title') or time_el.inner_text().strip()

                if not content or len(content) < 10:
                    continue

                post_id_for_comments = f"post_{idx}_{datetime.now().strftime('%H%M%S')}"

                posts_data.append({
                    'platform': '微博',
                    'post_id': post_id_for_comments,
                    'author': author,
                    'content': content[:500],
                    'publish_time': time_str,
                    'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
                print(f"\n[{idx+1}/{min(len(cards), target_posts)}] {author}: {content[:30]}...")

                # 点击进入详情页获取评论
                try:
                    # 找到微博内容的链接
                    content_link = card.query_selector('.txt') or card.query_selector('.WB_text')
                    if content_link:
                        content_link.click()
                        page.wait_for_timeout(5000)

                        current_url = page.url
                        print(f"   ➡️  {current_url}")

                        if 'weibo.com' in current_url:
                            # 滚动加载评论
                            print(f"   ⬇️  滚动加载评论...")
                            for i in range(15):
                                page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                                page.wait_for_timeout(1000)

                            # 提取评论
                            comment_containers = page.query_selector_all('.vue-recycle-scroller__item-view')
                            if not comment_containers:
                                comment_containers = page.query_selector_all('.comment_item')
                            if not comment_containers:
                                comment_containers = page.query_selector_all('[class*="comment"] [class*="item"]')
                            if not comment_containers:
                                comment_containers = page.query_selector_all('.list_li')

                            print(f"   💬 找到 {len(comment_containers)} 个评论元素")

                            for c_idx, comment_el in enumerate(comment_containers[:30]):
                                try:
                                    c_text = comment_el.inner_text().strip()
                                    if c_text and len(c_text) > 5:
                                        comments_data.append({
                                            'platform': '微博',
                                            'post_id': post_id_for_comments,
                                            'post_author': author,
                                            'post_content': content[:50],
                                            'comment_author': '',
                                            'comment': c_text[:500],
                                            'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                        })
                                        print(f"      💬 {c_text[:30]}...")
                                except:
                                    continue

                    # 返回
                    page.go_back()
                    page.wait_for_timeout(3000)

                except Exception as e:
                    print(f"   ⚠️ 获取评论失败: {e}")
                    try:
                        page.go_back()
                        page.wait_for_timeout(2000)
                    except:
                        pass

            except Exception as e:
                print(f"⚠️ 处理失败: {e}")
                continue

        # 保存Cookie
        cookies = context.cookies()
        with open(cookie_file, 'w', encoding='utf-8') as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)

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

        print(f"\n📋 评论预览：")
        df_comments = pd.DataFrame(comments_data)
        for i, row in df_comments.head(20).iterrows():
            print(f"  [{i+1}] {row['comment'][:50]}...")

    return pd.DataFrame(posts_data), pd.DataFrame(comments_data)


if __name__ == "__main__":
    posts_df, comments_df = crawl_weibo_with_comments("上海迪士尼", 10)
