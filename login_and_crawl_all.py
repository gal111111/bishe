# -*- coding: utf-8 -*-
"""
一键登录 + 批量爬取脚本
========================
流程：弹出浏览器 → 用户扫码登录 → 保存Cookie → 自动批量爬取4平台数据
"""
import os
import sys
import json
import time
import pandas as pd
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from src.config.config_manager import PROJECT_ROOT as CONFIG_ROOT

COOKIE_DIR = os.path.join(str(CONFIG_ROOT), 'cookies')
RAW_DIR = os.path.join(str(CONFIG_ROOT), 'data', 'raw')
os.makedirs(COOKIE_DIR, exist_ok=True)
os.makedirs(RAW_DIR, exist_ok=True)


def login_platforms():
    """逐个弹出浏览器让用户扫码登录，保存Cookie"""
    from playwright.sync_api import sync_playwright
    from playwright_stealth import Stealth

    platforms = {
        'weibo': {
            'login_url': 'https://login.sina.com.cn/signup/signin.php',
            'verify_url': 'https://m.weibo.cn/',
            'cookie_file': os.path.join(COOKIE_DIR, 'weibo_playwright.json'),
            'name': '微博',
        },
        'zhihu': {
            'login_url': 'https://www.zhihu.com/signin',
            'verify_url': 'https://www.zhihu.com/',
            'cookie_file': os.path.join(COOKIE_DIR, 'zhihu_playwright.json'),
            'name': '知乎',
        },
        'tieba': {
            'login_url': 'https://passport.baidu.com/v2/?login',
            'verify_url': 'https://tieba.baidu.com/',
            'cookie_file': os.path.join(COOKIE_DIR, 'tieba_playwright.json'),
            'name': '百度贴吧',
        },
        'hupu': {
            'login_url': 'https://passport.hupu.com/site/login',
            'verify_url': 'https://bbs.hupu.com/',
            'cookie_file': os.path.join(COOKIE_DIR, 'hupu_playwright.json'),
            'name': '虎扑',
        },
    }

    chrome_path = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
    logged_in = {}

    with sync_playwright() as p:
        launch_args = {
            'headless': False,
            'args': ['--disable-blink-features=AutomationControlled', '--no-first-run']
        }
        if os.path.exists(chrome_path):
            launch_args['executable_path'] = chrome_path

        browser = p.chromium.launch(**launch_args)

        for plat_key, plat_info in platforms.items():
            print(f"\n{'='*60}")
            print(f"🔐 请登录 {plat_info['name']} ({plat_info['login_url']})")
            print(f"{'='*60}")

            context = browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='zh-CN',
            )
            page = context.new_page()
            Stealth().apply_stealth_sync(page)

            # 先加载已有Cookie
            if os.path.exists(plat_info['cookie_file']):
                try:
                    with open(plat_info['cookie_file'], 'r') as f:
                        old_cookies = json.load(f)
                    context.add_cookies(old_cookies)
                    print(f"  已加载旧Cookie")
                except:
                    pass

            page.goto(plat_info['verify_url'], wait_until='domcontentloaded', timeout=30000)
            time.sleep(3)

            # 检查是否已经登录
            current_url = page.url
            title = page.title()
            already_logged_in = '登录' not in title and 'signin' not in current_url.lower() and 'passport' not in current_url.lower()

            if already_logged_in:
                print(f"  ✅ {plat_info['name']} Cookie仍有效，无需重新登录！")
                logged_in[plat_key] = True
                # 更新Cookie
                cookies = context.cookies()
                with open(plat_info['cookie_file'], 'w') as f:
                    json.dump(cookies, f, ensure_ascii=False, indent=2)
                context.close()
                continue

            # 需要登录
            page.goto(plat_info['login_url'], wait_until='domcontentloaded', timeout=30000)
            print(f"\n  📱 请在弹出的浏览器中扫码/登录 {plat_info['name']}")
            print(f"  ⏳ 等待登录...（30秒后自动检查）")

            time.sleep(30)

            # 保存Cookie
            cookies = context.cookies()
            with open(plat_info['cookie_file'], 'w') as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)
            print(f"  ✅ {plat_info['name']} Cookie已保存！({len(cookies)} 条)")
            logged_in[plat_key] = True

            context.close()

        browser.close()

    print(f"\n{'='*60}")
    print(f"✅ 登录完成！已登录平台: {[platforms[k]['name'] for k in logged_in if logged_in[k]]}")
    print(f"{'='*60}")
    return logged_in


def crawl_all(keyword="上海迪士尼", target_per_platform=3000):
    """批量爬取所有平台数据"""
    from src.crawlers.playwright_spiders.weibo_playwright import WeiboPlaywrightCrawler
    from src.crawlers.playwright_spiders.zhihu_playwright import ZhihuPlaywrightCrawler
    from src.crawlers.playwright_spiders.tieba_playwright import TiebaPlaywrightCrawler
    from src.crawlers.playwright_spiders.hupu_playwright import HupuPlaywrightCrawler

    all_data = []

    # 1. 微博
    print(f"\n{'='*60}")
    print(f"📡 正在爬取微博 - 关键词: {keyword}, 目标: {target_per_platform}条")
    print(f"{'='*60}")
    try:
        weibo_crawler = WeiboPlaywrightCrawler()
        df_weibo = weibo_crawler.crawl(keyword, target_count=target_per_platform, fetch_comments=True, comment_posts=20)
        if not df_weibo.empty:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = os.path.join(RAW_DIR, f'weibo_raw_{keyword}_{timestamp}.csv')
            df_weibo.to_csv(path, index=False, encoding='utf-8-sig')
            print(f"  ✅ 微博: {len(df_weibo)} 条 → {path}")
            all_data.append(df_weibo)
    except Exception as e:
        print(f"  ❌ 微博爬取失败: {e}")

    # 2. 知乎
    print(f"\n{'='*60}")
    print(f"📡 正在爬取知乎 - 关键词: {keyword}, 目标: {target_per_platform}条")
    print(f"{'='*60}")
    try:
        zhihu_crawler = ZhihuPlaywrightCrawler()
        df_zhihu = zhihu_crawler.crawl(keyword, target_count=target_per_platform, fetch_comments=True, comment_posts=20)
        if not df_zhihu.empty:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = os.path.join(RAW_DIR, f'zhihu_raw_{keyword}_{timestamp}.csv')
            df_zhihu.to_csv(path, index=False, encoding='utf-8-sig')
            print(f"  ✅ 知乎: {len(df_zhihu)} 条 → {path}")
            all_data.append(df_zhihu)
    except Exception as e:
        print(f"  ❌ 知乎爬取失败: {e}")

    # 3. 贴吧
    print(f"\n{'='*60}")
    print(f"📡 正在爬取贴吧 - 关键词: {keyword}, 目标: {target_per_platform}条")
    print(f"{'='*60}")
    try:
        tieba_crawler = TiebaPlaywrightCrawler()
        df_tieba = tieba_crawler.crawl(keyword, target_count=target_per_platform, fetch_comments=True, comment_posts=20)
        if not df_tieba.empty:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = os.path.join(RAW_DIR, f'tieba_raw_{keyword}_{timestamp}.csv')
            df_tieba.to_csv(path, index=False, encoding='utf-8-sig')
            print(f"  ✅ 贴吧: {len(df_tieba)} 条 → {path}")
            all_data.append(df_tieba)
    except Exception as e:
        print(f"  ❌ 贴吧爬取失败: {e}")

    # 4. 虎扑
    print(f"\n{'='*60}")
    print(f"📡 正在爬取虎扑 - 关键词: {keyword}, 目标: {target_per_platform}条")
    print(f"{'='*60}")
    try:
        hupu_crawler = HupuPlaywrightCrawler()
        df_hupu = hupu_crawler.crawl(keyword, target_count=target_per_platform, fetch_comments=True, comment_posts=20)
        if not df_hupu.empty:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = os.path.join(RAW_DIR, f'hupu_raw_{keyword}_{timestamp}.csv')
            df_hupu.to_csv(path, index=False, encoding='utf-8-sig')
            print(f"  ✅ 虎扑: {len(df_hupu)} 条 → {path}")
            all_data.append(df_hupu)
    except Exception as e:
        print(f"  ❌ 虎扑爬取失败: {e}")

    return all_data


def restructure_and_analyze(all_data_list):
    """将爬取数据重组为去重格式并运行情感分析"""
    from src.analysis.sentiment_analysis import analyze_dataframe, preprocess_data

    if not all_data_list:
        print("❌ 没有新数据可处理")
        return

    # 合并所有新数据
    df_new = pd.concat(all_data_list, ignore_index=True)
    print(f"\n{'='*60}")
    print(f"📊 数据重组与去重")
    print(f"{'='*60}")
    print(f"新爬取数据: {len(df_new)} 行")

    # 统一列名
    if 'content' not in df_new.columns and 'text' in df_new.columns:
        df_new = df_new.rename(columns={'text': 'content'})

    # 提取帖子 + 评论
    records = []

    # 帖子
    if 'content' in df_new.columns:
        posts = df_new[['content']].dropna().copy()
        posts['content'] = posts['content'].astype(str).str.strip()
        posts = posts[posts['content'].str.len() >= 5]
        posts = posts.drop_duplicates(subset=['content'], keep='first')
        for _, row in posts.iterrows():
            records.append({
                'platform': df_new['platform'].iloc[0] if 'platform' in df_new.columns else 'unknown',
                'content': row['content'],
                'data_type': 'post',
            })

    # 评论
    comment_cols = ['comment_content', 'comment', 'comments']
    for col in comment_cols:
        if col in df_new.columns:
            comments = df_new[[col]].dropna().copy()
            comments[col] = comments[col].astype(str).str.strip()
            comments = comments[comments[col].str.len() >= 5]
            comments = comments.drop_duplicates(subset=[col], keep='first')
            for _, row in comments.iterrows():
                records.append({
                    'platform': df_new['platform'].iloc[0] if 'platform' in df_new.columns else 'unknown',
                    'content': row[col],
                    'data_type': 'comment',
                })
            break

    df_records = pd.DataFrame(records)
    df_records = df_records.drop_duplicates(subset=['content'], keep='first')

    # 与已有数据合并去重
    existing_path = os.path.join(str(CONFIG_ROOT), 'data', 'restructured_unique_data.csv')
    if os.path.exists(existing_path):
        df_existing = pd.read_csv(existing_path, encoding='utf-8-sig')
        existing_contents = set(df_existing['content'].dropna().astype(str).tolist())
        df_records = df_records[~df_records['content'].astype(str).isin(existing_contents)]

    print(f"新增唯一记录: {len(df_records)} 条")

    if df_records.empty:
        print("⚠️ 没有新增数据")
        return

    # 保存重组数据
    if os.path.exists(existing_path):
        df_existing = pd.read_csv(existing_path, encoding='utf-8-sig')
        df_all = pd.concat([df_existing, df_records], ignore_index=True)
    else:
        df_all = df_records
    df_all.to_csv(existing_path, index=False, encoding='utf-8-sig')
    print(f"重组数据总量: {len(df_all)} 条")

    # 情感分析
    print(f"\n🤖 正在运行情感分析...")
    try:
        df_clean = preprocess_data(df_all)
    except:
        df_clean = df_all

    df_res = analyze_dataframe(df_clean, preferred='snownlp')

    # 保存分析结果
    analyzed_path = os.path.join(str(CONFIG_ROOT), 'data', 'analyzed_comments.csv')
    df_res.to_csv(analyzed_path, index=False, encoding='utf-8-sig')
    print(f"\n✅ 分析完成！共 {len(df_res)} 条")
    if 'polarity_label' in df_res.columns:
        dist = df_res['polarity_label'].value_counts()
        for label in ['积极', '中性', '消极']:
            if label in dist.index:
                print(f"  {label}: {dist[label]} ({dist[label]/len(df_res)*100:.1f}%)")


def main():
    print("=" * 60)
    print("🏙️ 城市慧眼 - 一键登录 + 批量爬取")
    print("=" * 60)

    # 第一步：登录
    logged_in = login_platforms()

    if not any(logged_in.values()):
        print("❌ 没有成功登录任何平台，退出")
        return

    # 第二步：爬取
    print(f"\n{'='*60}")
    print(f"📡 开始批量爬取数据...")
    print(f"{'='*60}")

    keyword = "上海迪士尼"

    all_data = crawl_all(keyword=keyword, target_per_platform=3000)

    # 第三步：重组分析
    restructure_and_analyze(all_data)

    print(f"\n{'='*60}")
    print(f"🎉 全部完成！请刷新 Streamlit 查看结果")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
