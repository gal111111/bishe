"""
微博评论爬虫 - 通过Playwright访问详情页获取评论
"""
import sys
import os
import json
import re
import pandas as pd
from datetime import datetime
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.config.config_manager import PROJECT_ROOT


def crawl_weibo_comments(keyword, target_posts=5):
    project_root = str(PROJECT_ROOT)
    cookie_dir = os.path.join(project_root, 'cookies')
    cookie_file = os.path.join(cookie_dir, 'weibo_playwright.json')
    raw_dir = os.path.join(project_root, 'data', 'raw')
    os.makedirs(raw_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    print(f"\n{'='*60}")
    print(f"🎯 微博评论爬虫 - 关键词: {keyword}")
    print(f"{'='*60}")

    # 第一步：获取微博列表和ID
    print(f"\n📝 获取微博列表...")
    import requests

    with open(cookie_file, 'r') as f:
        cookies_list = json.load(f)
        cookies = {}
        for c in cookies_list:
            cookies[c['name']] = c['value']

    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15',
        'Referer': 'https://m.weibo.cn/',
        'Accept': 'application/json, text/plain, */*',
    }

    posts_data = []
    page = 1
    while len(posts_data) < target_posts and page <= 3:
        search_url = f'https://m.weibo.cn/api/container/getIndex?containerid=100103type%3D1%26q%3D{keyword}&page_type=searchall&page={page}'
        try:
            response = requests.get(search_url, headers=headers, cookies=cookies, timeout=30)
            data = response.json()
            if data.get('ok') == 1:
                for card in data.get('data', {}).get('cards', []):
                    if 'mblog' not in card:
                        continue
                    blog = card['mblog']
                    post_id = blog.get('id', '')
                    author = blog.get('user', {}).get('screen_name', '')
                    content = re.sub(r'<[^>]+>', '', blog.get('text', ''))
                    comments_count = blog.get('comments_count', 0)
                    if post_id and comments_count > 0:
                        posts_data.append({
                            'post_id': post_id,
                            'author': author,
                            'content': content,
                            'comments_count': comments_count
                        })
                        print(f"  ✅ {author}: {content[:30]}... (💬{comments_count})")
            page += 1
        except:
            break

    # 第二步：用Playwright访问详情页获取评论
    print(f"\n{'='*60}")
    print(f"💬 进入详情页获取评论...")
    print(f"{'='*60}")

    all_comments = []

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
        with open(cookie_file, 'r') as f:
            cookies_list = json.load(f)
        context.add_cookies(cookies_list)

        # 先访问m.weibo.cn激活Cookie
        page.goto('https://m.weibo.cn', wait_until='domcontentloaded', timeout=60000)
        page.wait_for_timeout(3000)

        for idx, post in enumerate(posts_data[:target_posts]):
            post_id = post['post_id']
            detail_url = f'https://m.weibo.cn/detail/{post_id}'

            print(f"\n[{idx+1}/{len(posts_data[:target_posts])}] {post['author']}: {post['content'][:30]}...")
            print(f"   ➡️  {detail_url}")

            try:
                page.goto(detail_url, wait_until='domcontentloaded', timeout=30000)
                page.wait_for_timeout(5000)

                # 滚动加载评论
                for i in range(10):
                    page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                    page.wait_for_timeout(1000)

                # 获取页面文本
                page_text = page.inner_text('body')

                # 获取微博正文
                weibo_text = ''
                weibo_el = page.query_selector('.weibo-text') or page.query_selector('.detail-content')
                if weibo_el:
                    weibo_text = weibo_el.inner_text().strip()

                # 提取评论 - 从页面文本中分析
                # 评论通常在正文后面
                lines = page_text.split('\n')
                comment_section = False
                comment_count = 0

                for line in lines:
                    line = line.strip()
                    if not line or len(line) < 3:
                        continue

                    # 检测评论区域开始
                    if '评论' in line and len(line) < 10:
                        comment_section = True
                        continue

                    if comment_section:
                        # 过滤掉非评论内容
                        if any(skip in line for skip in ['赞', '回复', '举报', '删除', '来自', '更多', '收起', '展开', '分享', '相关', '推荐', '关注']):
                            continue
                        if line.isdigit():
                            continue
                        if line == weibo_text or weibo_text[:30] in line:
                            continue
                        if len(line) > 200:
                            continue

                        all_comments.append({
                            'platform': '微博',
                            'post_id': post_id,
                            'post_author': post['author'],
                            'post_content': post['content'][:50],
                            'comment': line[:500],
                            'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
                        comment_count += 1
                        print(f"      💬 {line[:30]}...")

                print(f"   ✅ 获取到 {comment_count} 条评论")

            except Exception as e:
                print(f"   ⚠️ 失败: {e}")

        browser.close()

    # 保存
    print(f"\n{'='*60}")
    print(f"📊 爬取完成！")
    print(f"   微博数量: {len(posts_data)}")
    print(f"   评论数量: {len(all_comments)}")

    if all_comments:
        comments_csv = os.path.join(raw_dir, f'weibo_comments_{keyword.replace(" ","_")}_{timestamp}.csv')
        df = pd.DataFrame(all_comments)
        df.to_csv(comments_csv, index=False, encoding='utf-8-sig')
        print(f"✅ 评论数据已保存: {comments_csv}")

        print(f"\n📋 评论预览（前15条）：")
        for i, row in df.head(15).iterrows():
            print(f"  [{i+1}] 【{row['post_author']}】→ {row['comment'][:40]}...")

    return pd.DataFrame(all_comments)


if __name__ == "__main__":
    crawl_weibo_comments("上海迪士尼", 5)
