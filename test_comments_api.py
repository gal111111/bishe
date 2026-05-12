"""
测试评论API - 用新Cookie获取评论
"""
import sys
import os
import json
import re
import requests

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.config.config_manager import PROJECT_ROOT

project_root = str(PROJECT_ROOT)
cookie_file = os.path.join(project_root, 'cookies', 'weibo_playwright.json')

with open(cookie_file, 'r') as f:
    cookies_list = json.load(f)
    cookies = {}
    for c in cookies_list:
        cookies[c['name']] = c['value']

print(f"Cookie数量: {len(cookies)}")
print(f"Cookie名称: {list(cookies.keys())[:10]}")

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://m.weibo.cn/',
    'Accept': 'application/json, text/plain, */*',
}

# 先获取微博列表
search_url = 'https://m.weibo.cn/api/container/getIndex?containerid=100103type%3D1%26q%3D上海迪士尼&page_type=searchall&page=1'
response = requests.get(search_url, headers=headers, cookies=cookies, timeout=30)
data = response.json()

posts = []
if data.get('ok') == 1:
    for card in data.get('data', {}).get('cards', []):
        if 'mblog' in card:
            blog = card['mblog']
            post_id = blog.get('id', '')
            author = blog.get('user', {}).get('screen_name', '')
            content = re.sub(r'<[^>]+>', '', blog.get('text', ''))
            comments_count = blog.get('comments_count', 0)
            if post_id and comments_count > 0:
                posts.append({
                    'post_id': post_id,
                    'author': author,
                    'content': content[:50],
                    'comments_count': comments_count
                })

print(f"\n获取到 {len(posts)} 条有评论的微博")

# 测试评论API
if posts:
    test_post = posts[0]
    post_id = test_post['post_id']
    print(f"\n测试微博: {test_post['author']} - {test_post['content']}... (评论:{test_post['comments_count']})")
    print(f"微博ID: {post_id}")

    # 方式1：hot.json
    comments_url = f'https://m.weibo.cn/comments/hot.json?id={post_id}&max_id=0&max_id_type=0'
    print(f"\n方式1: {comments_url}")
    response = requests.get(comments_url, headers=headers, cookies=cookies, timeout=30)
    print(f"状态码: {response.status_code}")
    try:
        data = response.json()
        print(f"ok: {data.get('ok')}")
        print(f"msg: {data.get('msg', '')}")
        if data.get('ok') == 1:
            comments = data.get('data', [])
            print(f"✅ 获取到 {len(comments)} 条评论！")
            for i, c in enumerate(comments[:5]):
                user = c.get('user', {})
                text = re.sub(r'<[^>]+>', '', c.get('text', ''))
                print(f"  [{i+1}] {user.get('screen_name', '')}: {text[:50]}...")
        else:
            print(f"❌ 失败: {response.text[:200]}")
    except:
        print(f"❌ 解析失败: {response.text[:200]}")

    # 方式2：container API
    comments_url2 = f'https://m.weibo.cn/api/container/getIndex?containerid=230283{post_id}&type=comment&id={post_id}'
    print(f"\n方式2: {comments_url2}")
    response2 = requests.get(comments_url2, headers=headers, cookies=cookies, timeout=30)
    print(f"状态码: {response2.status_code}")
    try:
        data2 = response2.json()
        print(f"ok: {data2.get('ok')}")
        print(f"msg: {data2.get('msg', '')}")
        if data2.get('ok') == 1:
            cards = data2.get('data', {}).get('cards', [])
            print(f"✅ 获取到 {len(cards)} 个卡片！")
            for i, card in enumerate(cards[:5]):
                comment = card.get('comment', {})
                if comment:
                    user = comment.get('user', {})
                    text = re.sub(r'<[^>]+>', '', comment.get('text', ''))
                    print(f"  [{i+1}] {user.get('screen_name', '')}: {text[:50]}...")
        else:
            print(f"❌ 失败: {response2.text[:200]}")
    except:
        print(f"❌ 解析失败: {response2.text[:200]}")
