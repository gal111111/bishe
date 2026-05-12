"""
微博评论爬虫 - Playwright调用评论API
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


def crawl_weibo_comments(keyword, target_posts=10):
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

        # 激活Cookie
        page.goto('https://m.weibo.cn', wait_until='domcontentloaded', timeout=60000)
        page.wait_for_timeout(3000)

        # 获取微博列表（通过API）
        print(f"\n📝 获取微博列表...")

        # 使用evaluate直接调用API
        def get_weibo_list():
            return page.evaluate('''
                async () => {
                    const response = await fetch('https://m.weibo.cn/api/container/getIndex?containerid=100103type%3D1%26q%3D''' + keyword + '''&page_type=searchall&page=1', {
                        headers: {
                            'Accept': 'application/json',
                            'Referer': 'https://m.weibo.cn/'
                        }
                    });
                    return response.json();
                }
            ''')

        try:
            data = get_weibo_list()
            if data and data.get('ok') == 1:
                cards = data.get('data', {}).get('cards', [])
                print(f"   获取到 {len(cards)} 个卡片")

                for card in cards:
                    if 'mblog' not in card:
                        continue

                    blog = card['mblog']
                    post_id = blog.get('id', '')
                    author = blog.get('user', {}).get('screen_name', '')
                    content = blog.get('text', '')
                    content = re.sub(r'<[^>]+>', '', content)
                    time_str = blog.get('created_at', '')
                    comments_count = blog.get('comments_count', 0)

                    posts_data.append({
                        'platform': '微博',
                        'post_id': post_id,
                        'author': author,
                        'content': content[:500],
                        'publish_time': time_str,
                        'comments_count': comments_count,
                        'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
                    print(f"   ✅ {author}: {content[:30]}... (评论:{comments_count})")

                    if len(posts_data) >= target_posts:
                        break
        except Exception as e:
            print(f"❌ 获取微博失败: {e}")

        # 保存Cookie
        cookies = context.cookies()
        with open(cookie_file, 'w', encoding='utf-8') as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)

        browser.close()

    # 获取评论
    print(f"\n{'='*60}")
    print(f"💬 获取评论...")
    print(f"{'='*60}")

    for idx, post in enumerate(posts_data):
        post_id = post['post_id']
        if not post_id or post['comments_count'] == 0:
            continue

        print(f"\n[{idx+1}/{len(posts_data)}] {post['author']}: {post['content'][:30]}...")

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

            if os.path.exists(cookie_file):
                with open(cookie_file, 'r', encoding='utf-8') as f:
                    cookies = json.load(f)
                context.add_cookies(cookies)

            page.goto('https://m.weibo.cn', wait_until='domcontentloaded', timeout=60000)
            page.wait_for_timeout(2000)

            # 调用评论API
            def get_comments():
                return page.evaluate(f'''
                    async () => {{
                        const response = await fetch('https://m.weibo.cn/comments/hot.json?id={post_id}&max_id=0&max_id_type=0', {{
                            headers: {{
                                'Accept': 'application/json',
                                'Referer': 'https://m.weibo.cn/'
                            }}
                        }});
                        return response.json();
                    }}
                ''')

            try:
                data = get_comments()
                if data and data.get('ok') == 1:
                    comments_list = data.get('data', [])
                    print(f"   ✅ 获取到 {len(comments_list)} 条评论")

                    for comment in comments_list:
                        user = comment.get('user', {})
                        text = comment.get('text', '')
                        text = re.sub(r'<[^>]+>', '', text)

                        if text:
                            comments_data.append({
                                'platform': '微博',
                                'post_id': post_id,
                                'post_author': post['author'],
                                'post_content': post['content'][:50],
                                'comment_author': user.get('screen_name', ''),
                                'comment': text[:500],
                                'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            })
                            print(f"      💬 {user.get('screen_name', '')}: {text[:30]}...")
                else:
                    print(f"   ⚠️ API返回失败")
            except Exception as e:
                print(f"   ⚠️ 获取失败: {e}")

            browser.close()

    # 保存
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

        print(f"\n📋 评论预览（前10条）：")
        df_comments = pd.DataFrame(comments_data)
        for i, row in df_comments.head(10).iterrows():
            print(f"  [{i+1}] 【{row['post_author']}】→【{row['comment_author']}】: {row['comment'][:40]}...")

    return pd.DataFrame(posts_data), pd.DataFrame(comments_data)


if __name__ == "__main__":
    posts_df, comments_df = crawl_weibo_comments("上海迪士尼", 10)
