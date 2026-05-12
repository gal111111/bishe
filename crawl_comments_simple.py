"""
微博评论爬虫 - 使用微博搜索API
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
        print(f"✓ 已加载Cookie: {len(cookies)}个")
    else:
        print("❌ 未找到Cookie！")
        return None, None

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://m.weibo.cn/',
        'Accept': 'application/json, text/plain, */*',
    }

    print(f"\n{'='*60}")
    print(f"🎯 微博评论爬虫 - 关键词: {keyword}")
    print(f"{'='*60}")

    posts_data = []
    comments_data = []

    # 微博搜索API - 这个会返回微博内容
    print(f"\n📝 获取微博列表...")
    search_url = f'https://m.weibo.cn/api/container/getIndex?containerid=100103type%3D1%26q%3D{keyword}&page_type=searchall&page=1'

    try:
        response = requests.get(search_url, headers=headers, cookies=cookies, timeout=30)
        data = response.json()

        if data.get('ok') == 1:
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
                reposts_count = blog.get('reposts_count', 0)
                attitudes_count = blog.get('attitudes_count', 0)

                posts_data.append({
                    'platform': '微博',
                    'post_id': post_id,
                    'author': author,
                    'content': content[:500],
                    'publish_time': time_str,
                    'comments_count': comments_count,
                    'reposts_count': reposts_count,
                    'attitudes_count': attitudes_count,
                    'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
                print(f"   ✅ {author}: {content[:30]}... (评论:{comments_count})")

                if len(posts_data) >= target_posts:
                    break
        else:
            print(f"⚠️ API返回失败: {data.get('msg', 'Unknown error')}")

    except Exception as e:
        print(f"❌ 获取微博失败: {e}")
        return None, None

    # 获取评论
    print(f"\n{'='*60}")
    print(f"💬 获取评论...")
    print(f"{'='*60}")

    for idx, post in enumerate(posts_data):
        post_id = post['post_id']
        if not post_id:
            continue

        print(f"\n[{idx+1}/{len(posts_data)}] {post['author']}: {post['content'][:30]}...")

        # 评论API - 方式1
        comments_url = f'https://m.weibo.cn/comments/hot.json?id={post_id}&max_id=0&max_id_type=0'

        try:
            response = requests.get(comments_url, headers=headers, cookies=cookies, timeout=30)
            data = response.json()

            if data.get('ok') == 1:
                comments_list = data.get('data', [])
                print(f"   ✅ 方式1成功！获取到 {len(comments_list)} 条评论")

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
                # 方式2：container API
                comments_url2 = f'https://m.weibo.cn/api/container/getIndex?containerid=230283{post_id}&type=comment&id={post_id}'
                response2 = requests.get(comments_url2, headers=headers, cookies=cookies, timeout=30)
                data2 = response2.json()

                if data2.get('ok') == 1:
                    cards = data2.get('data', {}).get('cards', [])
                    real_comments = [c for c in cards if 'comment' in c]
                    print(f"   ✅ 方式2成功！获取到 {len(real_comments)} 条评论")

                    for card in real_comments:
                        comment = card.get('comment', {})
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

        except Exception as e:
            print(f"   ⚠️ 获取评论失败: {e}")

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
