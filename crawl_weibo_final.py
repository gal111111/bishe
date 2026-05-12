"""
微博爬虫 - 最终版
包含微博内容和评论数，数据适合做舆情分析
"""
import os
import sys
import json
import re
import pandas as pd
from datetime import datetime
import requests

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.config.config_manager import PROJECT_ROOT


def crawl_weibo(keyword, target_count=50):
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
        return None

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://m.weibo.cn/',
        'Accept': 'application/json, text/plain, */*',
    }

    print(f"\n{'='*60}")
    print(f"🎯 微博爬虫 - 关键词: {keyword}")
    print(f"{'='*60}")

    all_data = []
    page = 1

    while len(all_data) < target_count and page <= 5:
        print(f"\n📄 第{page}页...")

        search_url = f'https://m.weibo.cn/api/container/getIndex?containerid=100103type%3D1%26q%3D{keyword}&page_type=searchall&page={page}'

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

                    all_data.append({
                        'platform': '微博',
                        'post_id': post_id,
                        'author': author,
                        'content': content,
                        'publish_time': time_str,
                        'comments_count': comments_count,
                        'reposts_count': reposts_count,
                        'attitudes_count': attitudes_count,
                        'total_interactions': comments_count + reposts_count + attitudes_count,
                        'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })

                    print(f"   ✅ {author}: {content[:30]}... (👍{attitudes_count} 💬{comments_count} 🔁{reposts_count})")

                if len(cards) == 0:
                    break

            page += 1

        except Exception as e:
            print(f"❌ 获取失败: {e}")
            break

    # 保存
    print(f"\n{'='*60}")
    print(f"📊 爬取完成！")
    print(f"   总数据: {len(all_data)} 条")

    if all_data:
        csv_path = os.path.join(raw_dir, f'weibo_{keyword.replace(" ","_")}_{timestamp}.csv')
        df = pd.DataFrame(all_data)
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"✅ 数据已保存: {csv_path}")

        # 统计
        print(f"\n📊 数据统计：")
        print(f"   总微博数: {len(df)}")
        print(f"   总评论数: {df['comments_count'].sum()}")
        print(f"   总点赞数: {df['attitudes_count'].sum()}")
        print(f"   总转发数: {df['reposts_count'].sum()}")

        # 预览
        print(f"\n📋 数据预览（前10条）：")
        for i, row in df.head(10).iterrows():
            print(f"  [{i+1}] 【{row['author']}】")
            print(f"      {row['content'][:60]}...")
            print(f"      👍{row['attitudes_count']} 💬{row['comments_count']} 🔁{row['reposts_count']}")
            print()

        return df

    return None


if __name__ == "__main__":
    df = crawl_weibo("上海迪士尼", 50)
