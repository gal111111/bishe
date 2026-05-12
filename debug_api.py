"""
调试评论API
"""
import os
import sys
import json
import requests

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.config.config_manager import PROJECT_ROOT

project_root = str(PROJECT_ROOT)

# 加载Cookie
cookie_file = os.path.join(project_root, 'cookies', 'weibo_playwright.json')
cookies = {}
with open(cookie_file, 'r') as f:
    cookies_list = json.load(f)
    for c in cookies_list:
        cookies[c['name']] = c['value']

print(f"Cookie数量: {len(cookies)}")
print(f"Cookie名称: {list(cookies.keys())[:10]}")

# 测试一条微博的评论API
post_id = '5293011380735056'

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': f'https://m.weibo.cn/detail/{post_id}',
    'Accept': 'application/json, text/plain, */*',
    'MWeibo-Pwa': '1',
}

# 方式1：containerid格式
url1 = f'https://m.weibo.cn/api/container/getIndex?containerid=230283{post_id}&type=comment&id={post_id}&page=1'
print(f"\n请求URL: {url1}")
response = requests.get(url1, headers=headers, cookies=cookies, timeout=30)
print(f"状态码: {response.status_code}")
data = response.json()
print(f"ok: {data.get('ok')}")
print(f"msg: {data.get('msg')}")
if 'data' in data:
    print(f"data keys: {data['data'].keys() if isinstance(data['data'], dict) else 'list'}")
    cards = data.get('data', {}).get('cards', [])
    print(f"cards数量: {len(cards)}")
    if cards:
        print(f"第一个card keys: {cards[0].keys() if isinstance(cards[0], dict) else cards[0]}")

# 方式2：不同的containerid
url2 = f'https://m.weibo.cn/comments/hot.json?id={post_id}&max_id_type=0'
print(f"\n\n方式2 URL: {url2}")
response2 = requests.get(url2, headers=headers, cookies=cookies, timeout=30)
print(f"状态码: {response2.status_code}")
print(f"响应: {response2.text[:500]}")
