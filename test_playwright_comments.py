"""
Playwright微博爬虫 - 直接访问微博详情页获取评论
"""
import os
import json
import re
import pandas as pd
from datetime import datetime
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
from src.config.config_manager import PROJECT_ROOT


def crawl_weibo_with_comments(keyword, target_count=20):
    project_root = str(PROJECT_ROOT)
    cookie_dir = os.path.join(project_root, 'cookies')
    os.makedirs(cookie_dir, exist_ok=True)
    cookie_file = os.path.join(cookie_dir, 'weibo_playwright.json')

    raw_dir = os.path.join(project_root, 'data', 'raw')
    os.makedirs(raw_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    print(f"\n{'='*60}")
    print(f"🎯 Playwright微博爬虫 - 关键词: {keyword}")
    print(f"   目标：爬取微博内容 + 评论")
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

        # 搜索
        search_url = f'https://m.weibo.cn/search?containerid=100103type%3D1%26q%3D{keyword}'
        print(f"🔍 搜索: {keyword}")
        page.goto(search_url, wait_until='domcontentloaded', timeout=60000)
        page.wait_for_timeout(5000)

        # 滚动加载
        print(f"⬇️  滚动加载更多微博...")
        for i in range(10):
            page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            page.wait_for_timeout(1500)

        # 获取微博卡片
        print(f"📝 获取微博列表...")
        cards = page.query_selector_all('.card9')
        if not cards:
            cards = page.query_selector_all('.card')

        print(f"   找到 {len(cards)} 条微博")

        # 处理每条微博
        for idx, card in enumerate(cards[:target_count]):
            try:
                # 提取微博ID - 从card的href中获取
                post_id = ''
                # 尝试多种方式获取链接
                for sel in ['a[href*="/detail/"]', 'a[class*="link"]', '.weibo-main a']:
                    link_el = card.query_selector(sel)
                    if link_el:
                        href = link_el.get_attribute('href') or ''
                        match = re.search(r'/detail/(\d+)', href)
                        if match:
                            post_id = match.group(1)
                            break

                if not post_id:
                    # 尝试从card本身获取
                    href = card.get_attribute('href') or ''
                    match = re.search(r'/detail/(\d+)', href)
                    if match:
                        post_id = match.group(1)

                # 提取微博基本信息
                author = ''
                author_el = card.query_selector('.m-text-box .m-text-cut')
                if not author_el:
                    author_el = card.query_selector('h3.m-text-cut')
                if author_el:
                    author = author_el.inner_text().strip()

                content = ''
                content_el = card.query_selector('.weibo-main')
                if not content_el:
                    content_el = card.query_selector('.weibo-text')
                if not content_el:
                    content_el = card.query_selector('.m-text-box')
                if content_el:
                    content = content_el.inner_text().strip()

                time_str = datetime.now().strftime('%Y-%m-%d')
                time_el = card.query_selector('.time')
                if time_el:
                    time_str = time_el.inner_text().strip()

                if not content:
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
                print(f"\n[{idx+1}/{min(len(cards), target_count)}] {author or '匿名'}: {content[:30]}...")
                if post_id:
                    print(f"   📌 微博ID: {post_id}")

                    # 点击进入详情页获取评论
                    try:
                        # 找到可点击的链接
                        detail_link = card.query_selector(f'a[href*="/detail/{post_id}"]')
                        if not detail_link:
                            detail_link = card.query_selector('a[href*="/detail/"]')

                        if detail_link:
                            detail_link.click()
                            page.wait_for_timeout(4000)

                            current_url = page.url
                            print(f"   ➡️  进入: {current_url}")

                            # 滚动加载评论
                            print(f"   ⬇️  滚动加载评论...")
                            for i in range(8):
                                page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                                page.wait_for_timeout(1000)

                            # 提取评论
                            # m.weibo.cn 评论选择器
                            comment_items = page.query_selector_all('.comment-item')
                            if not comment_items:
                                comment_items = page.query_selector_all('.c-item')
                            if not comment_items:
                                comment_items = page.query_selector_all('div[class*="comment"]')
                            if not comment_items:
                                comment_items = page.query_selector_all('.list-li')

                            print(f"   💬 找到 {len(comment_items)} 条评论")

                            for c_idx, comment_item in enumerate(comment_items):
                                try:
                                    c_author = ''
                                    c_author_el = comment_item.query_selector('.c-name') or comment_item.query_selector('.user-name')
                                    if not c_author_el:
                                        c_author_el = comment_item.query_selector('h4') or comment_item.query_selector('span')
                                    if c_author_el:
                                        c_author = c_author_el.inner_text().strip()

                                    c_text = ''
                                    c_text_el = comment_item.query_selector('.c-text')
                                    if not c_text_el:
                                        c_text_el = comment_item.query_selector('p')
                                    if not c_text_el:
                                        c_text_el = comment_item.query_selector('div')
                                    if c_text_el:
                                        c_text = c_text_el.inner_text().strip()

                                    if c_text and len(c_text) > 2:
                                        comments_data.append({
                                            'platform': '微博',
                                            'post_id': post_id_for_comments,
                                            'post_author': author,
                                            'post_content': content[:50],
                                            'comment_author': c_author,
                                            'comment': c_text[:500],
                                            'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                        })
                                        print(f"      💬 {c_author or '匿名'}: {c_text[:30]}...")

                                except:
                                    continue

                            # 返回列表页
                            page.go_back()
                            page.wait_for_timeout(2000)

                    except Exception as e:
                        print(f"   ⚠️ 获取评论失败: {e}")
                        try:
                            page.go_back()
                            page.wait_for_timeout(1000)
                        except:
                            pass

            except Exception as e:
                print(f"⚠️ 处理微博失败: {e}")
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

        # 预览评论
        print(f"\n📋 评论预览：")
        df_comments = pd.DataFrame(comments_data)
        for i, row in df_comments.head(20).iterrows():
            print(f"  [{i+1}] 【{row['post_author']}】→【{row['comment_author']}】: {row['comment'][:40]}...")

    return pd.DataFrame(posts_data), pd.DataFrame(comments_data)


if __name__ == "__main__":
    posts_df, comments_df = crawl_weibo_with_comments("上海迪士尼", 10)
