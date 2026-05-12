# -*- coding: utf-8 -*-
"""
批量爬取脚本 - 纯API方式，无需弹出浏览器
============================================
微博用API，知乎/贴吧/虎扑用requests模拟
"""
import os
import sys
import json
import re
import time
import random
import pandas as pd
import requests
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

COOKIE_DIR = os.path.join(PROJECT_ROOT, 'cookies')
RAW_DIR = os.path.join(PROJECT_ROOT, 'data', 'raw')
os.makedirs(RAW_DIR, exist_ok=True)


def load_cookies(platform):
    cookie_file = os.path.join(COOKIE_DIR, f'{platform}_playwright.json')
    if not os.path.exists(cookie_file):
        return {}, []
    with open(cookie_file, 'r') as f:
        cookies_list = json.load(f)
    cookies_dict = {c['name']: c['value'] for c in cookies_list}
    return cookies_dict, cookies_list


def crawl_weibo(keyword, target_count=3000):
    print(f"\n{'='*60}")
    print(f"📡 爬取微博 - 关键词: {keyword}, 目标: {target_count}")
    print(f"{'='*60}")

    cookies, _ = load_cookies('weibo')
    if not cookies:
        print("  ❌ 微博Cookie不存在")
        return pd.DataFrame()

    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15',
        'Referer': 'https://m.weibo.cn/',
        'Accept': 'application/json, text/plain, */*',
    }

    all_posts = []
    all_comments = []
    page = 1

    while len(all_posts) < target_count and page <= 50:
        url = f'https://m.weibo.cn/api/container/getIndex?containerid=100103type%3D1%26q%3D{keyword}&page_type=searchall&page={page}'
        try:
            resp = requests.get(url, headers=headers, cookies=cookies, timeout=20)
            data = resp.json()

            if data.get('ok') != 1:
                print(f"  第{page}页: 无数据，停止")
                break

            cards = data.get('data', {}).get('cards', [])
            if not cards:
                break

            for card in cards:
                if 'mblog' not in card:
                    continue
                blog = card['mblog']
                content = re.sub(r'<[^>]+>', '', blog.get('text', ''))
                post_id = blog.get('id', '')

                all_posts.append({
                    'platform': 'weibo',
                    'post_id': post_id,
                    'content': content,
                    'publish_time': blog.get('created_at', ''),
                    'like_count': blog.get('attitudes_count', 0),
                    'comment_count': blog.get('comments_count', 0),
                    'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                })

            print(f"  第{page}页: +{len(cards)}条, 累计{len(all_posts)}条")
            page += 1
            time.sleep(random.uniform(1.5, 3.0))

        except Exception as e:
            print(f"  第{page}页失败: {e}")
            break

    # 抓取热门帖子的评论
    posts_with_comments = sorted(all_posts, key=lambda x: x.get('comment_count', 0), reverse=True)
    comment_posts = posts_with_comments[:30]

    for idx, post in enumerate(comment_posts):
        post_id = post['post_id']
        if not post_id:
            continue

        for comment_page in range(1, 6):
            comment_url = f'https://m.weibo.cn/api/comments/show?id={post_id}&page={comment_page}'
            try:
                resp = requests.get(comment_url, headers=headers, cookies=cookies, timeout=15)
                cdata = resp.json()

                if cdata.get('ok') != 1:
                    break

                for c in cdata.get('data', {}).get('data', []):
                    comment_text = re.sub(r'<[^>]+>', '', c.get('text', ''))
                    all_comments.append({
                        'platform': 'weibo',
                        'post_id': post_id,
                        'content': comment_text,
                        'publish_time': c.get('created_at', ''),
                        'like_count': c.get('like_count', 0) if isinstance(c.get('like_count'), int) else 0,
                        'comment_count': 0,
                        'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    })

                time.sleep(random.uniform(1.0, 2.0))
            except:
                break

        if (idx + 1) % 5 == 0:
            print(f"  评论进度: {idx+1}/{len(comment_posts)}帖, 累计{len(all_comments)}条评论")
        time.sleep(random.uniform(1.0, 2.0))

    print(f"  ✅ 微博: {len(all_posts)}条帖子 + {len(all_comments)}条评论")

    df_posts = pd.DataFrame(all_posts) if all_posts else pd.DataFrame()
    df_comments = pd.DataFrame(all_comments) if all_comments else pd.DataFrame()
    df_all = pd.concat([df_posts, df_comments], ignore_index=True)

    if not df_all.empty:
        path = os.path.join(RAW_DIR, f'weibo_raw_{keyword}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
        df_all.to_csv(path, index=False, encoding='utf-8-sig')
        print(f"  保存: {path}")

    return df_all


def crawl_zhihu(keyword, target_count=2000):
    print(f"\n{'='*60}")
    print(f"📡 爬取知乎 - 关键词: {keyword}, 目标: {target_count}")
    print(f"{'='*60}")

    cookies, _ = load_cookies('zhihu')
    if not cookies:
        print("  ❌ 知乎Cookie不存在")
        return pd.DataFrame()

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://www.zhihu.com/search',
        'Accept': 'application/json, text/plain, */*',
    }

    all_data = []
    offset = 0

    while len(all_data) < target_count and offset < 200:
        url = f'https://www.zhihu.com/api/v4/search_v3?t=general&q={keyword}&correction=1&offset={offset}&limit=20'
        try:
            resp = requests.get(url, headers=headers, cookies=cookies, timeout=15)
            data = resp.json()

            items = data.get('data', [])
            if not items:
                break

            for item in items:
                obj = item.get('object', {}) or item.get('highlight', {})
                content = obj.get('content', '') or obj.get('excerpt', '') or ''
                content = re.sub(r'<[^>]+>', '', content)

                if len(content.strip()) < 5:
                    continue

                all_data.append({
                    'platform': 'zhihu',
                    'post_id': obj.get('id', ''),
                    'content': content.strip(),
                    'publish_time': obj.get('created_time', ''),
                    'like_count': obj.get('voteup_count', 0) if isinstance(obj.get('voteup_count'), int) else 0,
                    'comment_count': obj.get('comment_count', 0) if isinstance(obj.get('comment_count'), int) else 0,
                    'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                })

            print(f"  offset={offset}: +{len(items)}条, 累计{len(all_data)}条")
            offset += 20
            time.sleep(random.uniform(2.0, 4.0))

        except Exception as e:
            print(f"  offset={offset}失败: {e}")
            break

    print(f"  ✅ 知乎: {len(all_data)}条")

    df = pd.DataFrame(all_data) if all_data else pd.DataFrame()
    if not df.empty:
        path = os.path.join(RAW_DIR, f'zhihu_raw_{keyword}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
        df.to_csv(path, index=False, encoding='utf-8-sig')
        print(f"  保存: {path}")

    return df


def crawl_tieba(keyword, target_count=2000):
    print(f"\n{'='*60}")
    print(f"📡 爬取贴吧 - 关键词: {keyword}, 目标: {target_count}")
    print(f"{'='*60}")

    cookies, _ = load_cookies('tieba')
    if not cookies:
        print("  ❌ 贴吧Cookie不存在")
        return pd.DataFrame()

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://tieba.baidu.com/',
    }

    all_data = []
    pn = 0

    while len(all_data) < target_count and pn < 500:
        url = f'https://tieba.baidu.com/f?kw={keyword}&pn={pn}'
        try:
            resp = requests.get(url, headers=headers, cookies=cookies, timeout=15)
            if resp.status_code != 200:
                print(f"  pn={pn}: 状态码{resp.status_code}")
                break

            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, 'html.parser')

            threads = soup.select('li.j_thread_list')
            if not threads:
                threads = soup.select('.threadlist_li_title')

            if not threads:
                print(f"  pn={pn}: 无帖子")
                break

            for thread in threads:
                title_el = thread.select_one('a.j_th_tit') or thread.select_one('.threadlist_title a')
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                if not title or len(title) < 2:
                    continue

                all_data.append({
                    'platform': 'tieba',
                    'post_id': title_el.get('href', ''),
                    'content': title,
                    'publish_time': '',
                    'like_count': 0,
                    'comment_count': 0,
                    'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                })

            print(f"  pn={pn}: +{len(threads)}条, 累计{len(all_data)}条")
            pn += 50
            time.sleep(random.uniform(2.0, 4.0))

        except Exception as e:
            print(f"  pn={pn}失败: {e}")
            break

    print(f"  ✅ 贴吧: {len(all_data)}条")

    df = pd.DataFrame(all_data) if all_data else pd.DataFrame()
    if not df.empty:
        path = os.path.join(RAW_DIR, f'tieba_raw_{keyword}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
        df.to_csv(path, index=False, encoding='utf-8-sig')
        print(f"  保存: {path}")

    return df


def crawl_hupu(keyword, target_count=2000):
    print(f"\n{'='*60}")
    print(f"📡 爬取虎扑 - 关键词: {keyword}, 目标: {target_count}")
    print(f"{'='*60}")

    cookies, _ = load_cookies('hupu')
    if not cookies:
        print("  ❌ 虎扑Cookie不存在")
        return pd.DataFrame()

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://bbs.hupu.com/',
    }

    all_data = []
    page = 1

    while len(all_data) < target_count and page <= 50:
        url = f'https://bbs.hupu.com/search?q={keyword}&page={page}'
        try:
            resp = requests.get(url, headers=headers, cookies=cookies, timeout=15)
            if resp.status_code != 200:
                print(f"  page={page}: 状态码{resp.status_code}")
                break

            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, 'html.parser')

            items = soup.select('.search-result-item') or soup.select('.bbs-sl-a')
            if not items:
                items = soup.select('.list-item') or soup.select('div.title')

            if not items:
                print(f"  page={page}: 无结果")
                break

            for item in items:
                title_el = item.select_one('a') if item.name != 'a' else item
                if not title_el:
                    continue
                text = title_el.get_text(strip=True)
                if not text or len(text) < 2:
                    continue

                all_data.append({
                    'platform': 'hupu',
                    'post_id': title_el.get('href', ''),
                    'content': text,
                    'publish_time': '',
                    'like_count': 0,
                    'comment_count': 0,
                    'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                })

            print(f"  page={page}: +{len(items)}条, 累计{len(all_data)}条")
            page += 1
            time.sleep(random.uniform(2.0, 4.0))

        except Exception as e:
            print(f"  page={page}失败: {e}")
            break

    print(f"  ✅ 虎扑: {len(all_data)}条")

    df = pd.DataFrame(all_data) if all_data else pd.DataFrame()
    if not df.empty:
        path = os.path.join(RAW_DIR, f'hupu_raw_{keyword}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
        df.to_csv(path, index=False, encoding='utf-8-sig')
        print(f"  保存: {path}")

    return df


def restructure_and_analyze(new_data_list):
    from src.analysis.sentiment_analysis import analyze_dataframe, preprocess_data

    if not new_data_list:
        print("❌ 没有新数据")
        return

    df_new = pd.concat(new_data_list, ignore_index=True)
    print(f"\n{'='*60}")
    print(f"📊 数据重组与去重")
    print(f"{'='*60}")
    print(f"新爬取数据: {len(df_new)} 行")

    df_new['content'] = df_new['content'].astype(str).str.strip()
    df_new = df_new[df_new['content'].str.len() >= 5]
    df_new = df_new.drop_duplicates(subset=['content'], keep='first')
    print(f"去重后: {len(df_new)} 条")

    existing_path = os.path.join(PROJECT_ROOT, 'data', 'restructured_unique_data.csv')
    if os.path.exists(existing_path):
        df_existing = pd.read_csv(existing_path, encoding='utf-8-sig')
        existing_contents = set(df_existing['content'].dropna().astype(str).tolist())
        df_new = df_new[~df_new['content'].astype(str).isin(existing_contents)]
        print(f"去除与已有数据重复后: {len(df_new)} 条新增")

    if df_new.empty:
        print("⚠️ 没有新增数据")
        return

    if os.path.exists(existing_path):
        df_existing = pd.read_csv(existing_path, encoding='utf-8-sig')
        df_all = pd.concat([df_existing, df_new], ignore_index=True)
    else:
        df_all = df_new

    df_all = df_all.drop_duplicates(subset=['content'], keep='first')
    df_all.to_csv(existing_path, index=False, encoding='utf-8-sig')
    print(f"重组数据总量: {len(df_all)} 条")

    print(f"\n🤖 正在运行情感分析...")
    try:
        df_clean = preprocess_data(df_all)
    except Exception as e:
        print(f"预处理跳过: {e}")
        df_clean = df_all

    df_res = analyze_dataframe(df_clean, preferred='snownlp')

    analyzed_path = os.path.join(PROJECT_ROOT, 'data', 'analyzed_comments.csv')
    df_res.to_csv(analyzed_path, index=False, encoding='utf-8-sig')
    print(f"\n✅ 分析完成！共 {len(df_res)} 条")
    if 'polarity_label' in df_res.columns:
        dist = df_res['polarity_label'].value_counts()
        for label in ['积极', '中性', '消极']:
            if label in dist.index:
                print(f"  {label}: {dist[label]} ({dist[label]/len(df_res)*100:.1f}%)")


def main():
    keyword = "上海迪士尼"

    print("=" * 60)
    print(f"🏙️ 城市慧眼 - 批量爬取 ({keyword})")
    print("=" * 60)

    all_data = []

    df_weibo = crawl_weibo(keyword, target_count=3000)
    if not df_weibo.empty:
        all_data.append(df_weibo)

    df_zhihu = crawl_zhihu(keyword, target_count=2000)
    if not df_zhihu.empty:
        all_data.append(df_zhihu)

    df_tieba = crawl_tieba(keyword, target_count=2000)
    if not df_tieba.empty:
        all_data.append(df_tieba)

    df_hupu = crawl_hupu(keyword, target_count=2000)
    if not df_hupu.empty:
        all_data.append(df_hupu)

    restructure_and_analyze(all_data)

    print(f"\n{'='*60}")
    print(f"🎉 全部完成！请刷新 Streamlit 查看结果")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
