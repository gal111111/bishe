import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable

from playwright.async_api import async_playwright, BrowserContext, Page, Browser
from playwright_stealth import Stealth

_stealth = Stealth()

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from src.config.config_manager import ConfigManager, PROJECT_ROOT as _PROJECT_ROOT


class PlaywrightBaseCrawler:
    """Playwright爬虫基类 - 统一浏览器管理、Cookie复用、反检测、重试机制"""

    def __init__(self, platform: str, headless: bool = False):
        self.platform = platform
        self.headless = headless
        self.config = ConfigManager()
        self.project_root = str(_PROJECT_ROOT)
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

        self._setup_directories()

        self.selenum_cookie_file = os.path.join(self.project_root, 'data', f'{platform}_cookies.json')
        self.playwright_cookie_file = os.path.join(self.project_root, 'cookies', f'{platform}_playwright.json')

        self.api_data: List[Dict] = []
        self.login_required = False
        self._cookies_loaded = False

    def _setup_directories(self):
        """创建必要的目录"""
        cookie_dir = os.path.join(self.project_root, 'cookies')
        os.makedirs(cookie_dir, exist_ok=True)

    async def start(self, force_login: bool = False):
        """启动浏览器并加载Cookie，优先使用系统Chrome"""
        self.playwright = await async_playwright().start()

        chrome_path = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
        launch_kwargs = {
            'headless': self.headless,
            'args': [
                '--disable-blink-features=AutomationControlled',
                '--disable-infobars',
                '--no-first-run',
                '--no-service-initialize'
            ]
        }
        if os.path.exists(chrome_path):
            launch_kwargs['executable_path'] = chrome_path
            print(f"✓ 使用系统Chrome: {chrome_path}")

        self.browser = await self.playwright.chromium.launch(**launch_kwargs)
        self.context = await self.browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='zh-CN',
            timezone_id='Asia/Shanghai',
            extra_http_headers={
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
            }
        )
        self.page = await self.context.new_page()
        await _stealth.apply_stealth_async(self.page)

        await self._load_cookies()

        if force_login or not self._cookies_loaded:
            await self._do_login()

    async def stop(self):
        """关闭浏览器"""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()

    async def _load_cookies(self):
        """智能加载Cookie：优先Playwright格式，复用Selenium格式"""
        self._cookies_loaded = False

        if os.path.exists(self.playwright_cookie_file):
            try:
                with open(self.playwright_cookie_file, 'r', encoding='utf-8') as f:
                    cookies = json.load(f)
                await self.context.add_cookies(cookies)
                self._cookies_loaded = True
                print(f"✓ {self.platform} Playwright Cookie已加载")
                return
            except Exception as e:
                print(f"⚠ Playwright Cookie加载失败: {e}")

        if os.path.exists(self.selenum_cookie_file):
            try:
                with open(self.selenum_cookie_file, 'r', encoding='utf-8') as f:
                    cookies = json.load(f)
                converted = self._convert_selenium_cookies(cookies)
                if converted:
                    await self.context.add_cookies(converted)
                    self._cookies_loaded = True
                    await self._save_cookies()
                    print(f"✓ {self.platform} Selenium Cookie已转换并加载")
                    return
            except Exception as e:
                print(f"⚠ Selenium Cookie转换失败: {e}")

        print(f"⚠ {self.platform} 未找到有效Cookie，需要登录")

    def _convert_selenium_cookies(self, selenium_cookies: List[Dict]) -> List[Dict]:
        """将Selenium格式Cookie转换为Playwright格式"""
        converted = []
        for cookie in selenium_cookies:
            try:
                pc = {
                    'name': cookie.get('name', ''),
                    'value': cookie.get('value', ''),
                    'domain': cookie.get('domain', ''),
                    'path': cookie.get('path', '/'),
                }
                if 'expiry' in cookie:
                    pc['expires'] = cookie['expiry']
                if 'secure' in cookie:
                    pc['secure'] = cookie['secure']
                if converted:
                    converted.append(pc)
            except:
                continue
        return converted

    async def _save_cookies(self):
        """保存Cookie到Playwright专用文件"""
        cookies = await self.context.cookies()
        with open(self.playwright_cookie_file, 'w', encoding='utf-8') as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)
        print(f"✓ {self.platform} Cookie已保存到Playwright专用文件")

    async def _do_login(self):
        """需要用户登录时调用此方法"""
        login_urls = {
            'weibo': 'https://login.sina.com.cn/signup/signin.php',
            'zhihu': 'https://www.zhihu.com/signin',
            'tieba': 'https://passport.baidu.com/v2/?login',
            'douyin': 'https://www.douyin.com',
            'xiaohongshu': 'https://www.xiaohongshu.com',
            'bilibili': 'https://passport.bilibili.com/login'
        }

        url = login_urls.get(self.platform, f'https://{self.platform}.com')
        print(f"\n🔐 请在打开的浏览器中完成{self.platform}登录...")
        print(f"   登录后按 Enter 继续（已登录请直接回车）")

        await self.page.goto(url, wait_until='domcontentloaded')

        if not self.headless:
            input(f"\n⏸ 等待登录完成...按 Enter 继续: ")

        await self._save_cookies()
        print(f"✓ {self.platform} 登录完成，Cookie已保存")

    async def verify_cookies(self, test_url: str) -> bool:
        """验证Cookie是否有效"""
        try:
            response = await self.page.goto(test_url, wait_until='domcontentloaded')
            if response and response.ok:
                title = await self.page.title()
                if '登录' not in title and 'signin' not in title.lower():
                    return True
        except:
            pass
        return False

    async def register_api_interceptor(self, url_pattern: str, handler: Callable):
        """注册API响应拦截器"""
        async def handle_response(response):
            if url_pattern in response.url:
                try:
                    data = await response.json()
                    handler(data)
                except:
                    pass
        self.page.on('response', handle_response)

    async def scroll_page(self, times: int = 5, wait_ms: int = 2000):
        """滚动加载更多内容"""
        for _ in range(times):
            await self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await self.page.wait_for_timeout(wait_ms)

    async def safe_click(self, selector: str, timeout: int = 10000):
        """安全点击，自动等待"""
        try:
            await self.page.click(selector, timeout=timeout)
        except Exception as e:
            print(f"⚠ 点击失败 {selector}: {e}")

    async def safe_text(self, selector: str, default: str = "") -> str:
        """安全获取文本"""
        try:
            elem = await self.page.query_selector(selector)
            if elem:
                return await elem.inner_text()
        except:
            pass
        return default

    def get_api_data(self) -> List[Dict]:
        """获取拦截到的API数据"""
        return self.api_data

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()
