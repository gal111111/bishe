"""
微博评论爬虫 - 点击卡片进入详情页
"""
import os
import sys
import json
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
        print(f"\n📝 获取微博列表...")
        page.goto('https://m.weibo.cn', wait_until='domcontentloaded', timeout=60000)
        page.wait_for_timeout(3000)

        # 搜索
        search_url = f'https://m.weibo.cn/search?containerid=100103type%3D1%26q%3D{keyword}'
        page.goto(search_url, wait_until='domcontentloaded', timeout=60000)
        page.wait_for_timeout(5000)

        # 滚动加载
        print(f"⬇️  滚动加载...")
        for i in range(10):
            page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            page.wait_for_timeout(1500)

        # 获取微博卡片
        cards = page.query_selector_all('.card-wrap')
        print(f"   找到 {len(cards)} 条微博")

        # 处理每条微博
        for idx, card in enumerate(cards[:target_posts]):
            try:
                # 提取微博信息
                author = ''
                author_el = card.query_selector('h3')
                if author_el:
                    author = author_el.inner_text().strip()

                content = ''
                # 微博内容在.weibo-text或直接取文本
                content_el = card.query_selector('.weibo-text')
                if not content_el:
                    # 直接取整个卡片的文本
                    full_text = card.inner_text()
                    # 去掉作者名和时间
                    lines = full_text.split('\n')
                    content_lines = []
                    skip_author = True
                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue
                        if skip_author and line == author:
                            skip_author = False
                            continue
                        if '来自' in line or '讨论' in line or '阅读' in line or line.isdigit():
                            continue
                        content_lines.append(line)
                    content = ' '.join(content_lines)

                time_str = datetime.now().strftime('%Y-%m-%d')
                time_el = card.query_selector('.time')
                if time_el:
                    time_str = time_el.inner_text().strip()

                if not content or len(content) < 5:
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

                # 点击卡片进入详情页获取评论
                try:
                    card.click()
                    page.wait_for_timeout(5000)

                    current_url = page.url
                    print(f"   ➡️  进入: {current_url}")

                    # 检查是否是详情页
                    if '/detail/' in current_url:
                        # 滚动加载评论
                        print(f"   ⬇️  滚动加载评论...")
                        for i in range(10):
                            page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                            page.wait_for_timeout(1000)

                        # 提取评论
                        # 获取所有可能的评论元素
                        page_text = page.inner_text('body')

                        # 评论一般在微博正文下面，先获取微博正文
                        weibo_text = ''
                        text_els = page.query_selector_all('.weibo-text')
                        if text_els:
                            weibo_text = text_els[0].inner_text()
                            print(f"   📝 微博正文: {weibo_text[:50]}...")

                        # 获取页面所有文本行，分析评论
                        all_text = page.inner_text('body')
                        lines = all_text.split('\n')
                        comment_lines = []
                        in_comments = False

                        for line in lines:
                            line = line.strip()
                            # 检测评论区域开始
                            if '评论' in line or '最新' in line or '热门' in line:
                                in_comments = True
                            if in_comments and line and len(line) > 2:
                                # 过滤掉微博正文
                                if line not in weibo_text and weibo_text not in line:
                                    if not line.isdigit() or len(line) < 5:
                                        comment_lines.append(line)

                        # 提取评论
                        for c_idx, comment in enumerate(comment_lines[:30]):
                            if len(comment) > 3 and comment != author:
                                comments_data.append({
                                    'platform': '微博',
                                    'post_id': post_id_for_comments,
                                    'post_author': author,
                                    'post_content': content[:50],
                                    'comment_author': '',
                                    'comment': comment[:500],
                                    'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                })
                                print(f"      💬 {comment[:30]}...")

                        print(f"   ✅ 获取到 {len(comment_lines)} 条评论")

                    # 返回列表页
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

    return pd.DataFrame(posts_data), pd.DataFrame(comments_data)


if __name__ == "__main__":
    posts_df, comments_df = crawl_weibo_with_comments("上海迪士尼", 10)
