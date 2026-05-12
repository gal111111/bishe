"""
微博评论爬虫 - 拦截API请求获取评论
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
    captured_apis = []

    def handle_response(response):
        url = response.url
        if 'comment' in url.lower() or 'comments' in url.lower():
            try:
                data = response.json()
                captured_apis.append({'url': url, 'data': data})
            except:
                pass

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

        # 注册API拦截器
        page.on('response', handle_response)

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
        captured_apis.clear()

        for idx, card in enumerate(cards[:target_posts]):
            try:
                # 提取微博信息
                author = ''
                author_el = card.query_selector('h3')
                if author_el:
                    author = author_el.inner_text().strip()

                # 获取全文
                content = ''
                content_el = card.query_selector('.weibo-text')
                if not content_el:
                    full_text = card.inner_text()
                    lines = full_text.split('\n')
                    content_lines = []
                    for line in lines:
                        line = line.strip()
                        if line and '来自' not in line and '讨论' not in line and '阅读' not in line:
                            if not line.isdigit() or len(line) < 5:
                                if line != author:
                                    content_lines.append(line)
                    content = ' '.join(content_lines[:10])

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

                # 点击卡片进入详情页
                captured_before = len(captured_apis)
                card.click()
                page.wait_for_timeout(5000)

                current_url = page.url
                print(f"   ➡️  {current_url}")

                # 检查是否进入详情页或获取到评论API
                if '/detail/' in current_url:
                    # 滚动触发评论加载
                    for i in range(5):
                        page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                        page.wait_for_timeout(1000)

                # 从拦截的API中提取评论
                comments_from_apis = []
                for api in captured_apis[captured_before:]:
                    try:
                        data = api['data']
                        if isinstance(data, dict):
                            # 尝试多种数据路径
                            for key in ['data', 'comments', 'hot', 'normal']:
                                if key in data:
                                    items = data[key]
                                    if isinstance(items, list):
                                        for item in items:
                                            if isinstance(item, dict):
                                                user = item.get('user', {}) or item
                                                text = item.get('text', '') or item.get('content', '')
                                                if text:
                                                    text = re.sub(r'<[^>]+>', '', str(text))
                                                    comments_from_apis.append({
                                                        'author': user.get('screen_name', ''),
                                                        'text': text
                                                    })
                    except:
                        pass

                if comments_from_apis:
                    print(f"   ✅ 从API获取到 {len(comments_from_apis)} 条评论")
                    for c in comments_from_apis[:10]:
                        comments_data.append({
                            'platform': '微博',
                            'post_id': post_id_for_comments,
                            'post_author': author,
                            'post_content': content[:50],
                            'comment_author': c['author'],
                            'comment': c['text'][:500],
                            'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
                        print(f"      💬 {c['author']}: {c['text'][:30]}...")
                else:
                    # 直接从页面提取评论文本
                    all_text = page.inner_text('body')
                    # 找到微博正文后的内容
                    if content in all_text:
                        after_weibo = all_text.split(content)[-1] if len(all_text.split(content)) > 1 else ''
                        # 提取评论行
                        comment_lines = []
                        for line in after_weibo.split('\n'):
                            line = line.strip()
                            if line and len(line) > 5 and not line.isdigit():
                                if '赞' not in line and '转发' not in line and '评论' not in line:
                                    comment_lines.append(line)

                        if comment_lines:
                            print(f"   📝 从页面提取 {len(comment_lines)} 条评论")
                            for c_text in comment_lines[:10]:
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

                # 返回
                try:
                    page.go_back()
                    page.wait_for_timeout(2000)
                except:
                    pass

            except Exception as e:
                print(f"⚠️ 处理失败: {e}")
                try:
                    page.go_back()
                    page.wait_for_timeout(1000)
                except:
                    pass

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
