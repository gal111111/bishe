"""
微博评论爬虫 - 使用requests直接调用微博API
"""
import os
import sys
import json
import re
import pandas as pd
import requests
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.config.config_manager import PROJECT_ROOT


def get_mid_from_page(page_content):
    """从页面内容中提取微博mid"""
    match = re.search(r'"mblogid":"([^"]+)"', page_content)
    if match:
        return match.group(1)
    match = re.search(r'id\s*[=:]\s*["\']?(\d+)', page_content)
    if match:
        return match.group(1)
    return None


def crawl_weibo_comments(keyword, target_posts=10):
    project_root = str(PROJECT_ROOT)
    raw_dir = os.path.join(project_root, 'data', 'raw')
    os.makedirs(raw_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 加载Cookie
    cookie_file = os.path.join(project_root, 'cookies', 'weibo_playwright.json')
    if not os.path.exists(cookie_file):
        cookie_file = os.path.join(project_root, 'data', 'weibo_cookies.json')

    cookies = {}
    if os.path.exists(cookie_file):
        with open(cookie_file, 'r') as f:
            cookies_list = json.load(f)
            for c in cookies_list:
                cookies[c['name']] = c['value']
    else:
        print("❌ 未找到Cookie文件！")
        return None, None

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://m.weibo.cn/',
        'Accept': 'application/json, text/plain, */*',
        'MWeibo-Pwa': '1',
        'X-Requested-With': 'XMLHttpRequest'
    }

    print(f"\n{'='*60}")
    print(f"🎯 微博评论爬虫 - 关键词: {keyword}")
    print(f"{'='*60}")

    posts_data = []
    comments_data = []

    # 获取搜索页面，获取微博ID列表
    print(f"\n📝 获取微博列表...")
    search_url = f'https://m.weibo.cn/api/container/getIndex?containerid=100103type%3D1%26q%3D{keyword}&page_type=searchall'

    try:
        response = requests.get(search_url, headers=headers, cookies=cookies, timeout=30)
        data = response.json()

        if data.get('ok') == 1:
            cards = data.get('data', {}).get('cards', [])
            for card in cards:
                if 'mblog' in card:
                    blog = card['mblog']
                    post_id = blog.get('id', '')
                    author = blog.get('user', {}).get('screen_name', '')
                    content = blog.get('text', '')
                    content = re.sub(r'<[^>]+>', '', content)  # 去除HTML

                    time_str = blog.get('created_at', '')

                    posts_data.append({
                        'platform': '微博',
                        'post_id': post_id,
                        'author': author,
                        'content': content[:500],
                        'publish_time': time_str,
                        'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
                    print(f"  ✅ 微博: {author}: {content[:30]}... (ID: {post_id})")

                    if len(posts_data) >= target_posts:
                        break
        else:
            print(f"⚠️ API返回失败: {data}")

    except Exception as e:
        print(f"❌ 获取微博列表失败: {e}")
        return None, None

    # 获取每条微博的评论
    print(f"\n{'='*60}")
    print(f"💬 获取评论...")
    print(f"{'='*60}")

    for idx, post in enumerate(posts_data):
        post_id = post['post_id']
        if not post_id:
            continue

        print(f"\n[{idx+1}/{len(posts_data)}] 获取评论: {post['content'][:30]}...")

        # 调用评论API
        comments_url = f'https://m.weibo.cn/api/container/getIndex?containerid=230283{post_id}&type=comment&id={post_id}&page=1'

        try:
            response = requests.get(comments_url, headers=headers, cookies=cookies, timeout=30)
            data = response.json()

            if data.get('ok') == 1:
                cards = data.get('data', {}).get('cards', [])
                comment_count = 0
                for card in cards:
                    if 'mblog' in card:
                        continue  # 跳过微博本身

                    comment = card.get('comment', {})

                    comment_author = comment.get('user', {}).get('screen_name', '')
                    comment_text = comment.get('text', '')
                    comment_text = re.sub(r'<[^>]+>', '', comment_text)

                    if comment_text:
                        comments_data.append({
                            'platform': '微博',
                            'post_id': post_id,
                            'post_author': post['author'],
                            'post_content': post['content'][:50],
                            'comment_author': comment_author,
                            'comment': comment_text[:500],
                            'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
                        comment_count += 1
                        print(f"  💬 [{comment_count}] {comment_author}: {comment_text[:30]}...")

                print(f"  ✅ 共 {comment_count} 条评论")

        except Exception as e:
            print(f"  ⚠️ 获取评论失败: {e}")

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
            print(f"  [{i+1}] 【{row['post_author']}】→【{row['comment_author']}】: {row['comment'][:40]}...")

    return pd.DataFrame(posts_data), pd.DataFrame(comments_data)


if __name__ == "__main__":
    posts_df, comments_df = crawl_weibo_comments("上海迪士尼", 10)
