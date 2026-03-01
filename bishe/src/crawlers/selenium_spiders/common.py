

# -*- coding: utf-8 -*-
"""
通用爬虫工具类 - 供4个平台复用
"""
import time
import os
import csv
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def init_csv_header(file_path, base_fields):
    """初始化CSV文件表头（确保格式规范）"""
    with open(file_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=base_fields)
        writer.writeheader()


def format_time_str(time_str):
    """统一时间格式为YYYY-MM-DD HH:MM:SS，失败返回NULL"""
    if not time_str or time_str == "NULL":
        return "NULL"
    try:
        if "分钟前" in time_str or "小时前" in time_str:
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        try:
            dt = datetime.strptime(time_str, "%Y-%m-%d")
            return dt.strftime("%Y-%m-%d 00:00:00")
        except:
            return "NULL"


def format_numeric_value(value):
    """统一数值格式，非数字返回NULL"""
    if not value or value == "NULL":
        return "NULL"
    try:
        return int(value)
    except:
        try:
            return float(value)
        except:
            return "NULL"


def save_to_csv_standard(data, file_path, fields):
    """按规范保存数据到CSV"""
    with open(file_path, 'a', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        for row in data:
            if "publish_time" in row:
                row["publish_time"] = format_time_str(row["publish_time"])
            if "crawl_time" not in row:
                row["crawl_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for num_field in ["like_count", "comment_count", "forward_count"]:
                if num_field in row:
                    row[num_field] = format_numeric_value(row[num_field])
            for k, v in row.items():
                if v is None or v == "":
                    row[k] = "NULL"
            writer.writerow(row)
    print(f"\033[34m[格式规范]\033[0m 已保存{len(data)}条数据到{file_path}，格式符合规范")


class BaseSpider:
    def __init__(self, use_edge=True):
        if use_edge:
            options = webdriver.EdgeOptions()
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)
            options.add_argument("--start-maximized")
            self.driver = webdriver.Edge(options=options)
        else:
            options = webdriver.ChromeOptions()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-blink-features=AutomationControlled")
            self.driver = webdriver.Chrome(options=options)
        
        self.wait = WebDriverWait(self.driver, 15)
        self.vars = {}

    def wait_for_element(self, locator, locator_type=By.CSS_SELECTOR, timeout=15):
        """等待元素可见并返回"""
        try:
            wait = WebDriverWait(self.driver, timeout)
            element = wait.until(EC.visibility_of_element_located((locator_type, locator)))
            return element
        except TimeoutException:
            print(f"元素 {locator} 超时未加载")
            return None

    def wait_for_clickable(self, locator, locator_type=By.CSS_SELECTOR, timeout=15):
        """等待元素可点击并返回"""
        try:
            wait = WebDriverWait(self.driver, timeout)
            element = wait.until(EC.element_to_be_clickable((locator_type, locator)))
            return element
        except TimeoutException:
            print(f"元素 {locator} 超时不可点击")
            return None

    def wait_for_window(self, timeout=2):
        """等待新窗口并返回句柄"""
        time.sleep(round(timeout / 1000))
        wh_now = self.driver.window_handles
        wh_then = self.vars.get("window_handles", [])
        if len(wh_now) > len(wh_then):
            return set(wh_now).difference(set(wh_then)).pop()
        return None

    def scroll_to_bottom(self, step=500, sleep_time=0.5, max_scrolls=10):
        """滚动到页面底部（逐步滚动，触发动态加载）"""
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        scroll_count = 0
        
        while scroll_count < max_scrolls:
            self.driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight - {step});")
            time.sleep(sleep_time)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
            scroll_count += 1

    def scroll_to_element(self, element):
        """滚动到指定元素"""
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(0.5)

    def teardown(self):
        """关闭浏览器"""
        pass

