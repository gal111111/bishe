
# -*- coding: utf-8 -*-
"""
模块2：多平台数据规范化爬取
基于拓展关键词，自动化爬取多平台用户评论数据
"""
import os
import sys
import json
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from src.config.config_manager import config_manager


class PlatformCrawler:
    def __init__(self, platform: str):
        self.platform = platform
        self.config = config_manager
        self.crawl_data_path = self.config.get_crawl_data_path(platform)
        
    def _cleanup_temp_files(self):
        """冗余文件自动清理"""
        print(f"\n🧹 清理 {self.platform} 冗余文件...")
        
        temp_extensions = [".tmp", ".log", ".empty"]
        
        cleanup_count = 0
        for ext in temp_extensions:
            temp_files = list(Path(self.crawl_data_path).glob(f"*{ext}"))
            for f in temp_files:
                try:
                    f.unlink()
                    cleanup_count += 1
                except Exception as e:
                    print(f"⚠️  清理文件失败 {f}: {e}")
        
        print(f"✅ 清理完成，共删除 {cleanup_count} 个文件")
    
    def _save_structured_data(self, keyword: str, data_list: List[Dict]) -&gt; str:
        """
        结构化数据存储
        数据字段统一：platform, keyword, post_id, content, crawl_time, sentiment, content_length
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_keyword = keyword.replace(" ", "_").replace("/", "_").replace("\\", "_")
        filename = f"{safe_keyword}_{timestamp}.json"
        filepath = os.path.join(self.crawl_data_path, filename)
        
        structured_data = []
        for idx, item in enumerate(data_list):
            content = item.get("content", "")
            structured_item = {
                "platform": self.platform,
                "keyword": keyword,
                "post_id": f"post_{idx}_{uuid.uuid4().hex[:8]}",
                "content": content,
                "crawl_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "sentiment": None,
                "content_length": len(content)
            }
            structured_data.append(structured_item)
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(structured_data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 {self.platform} 数据已保存: {filepath} ({len(structured_data)} 条)")
        return filepath
    
    def crawl_keyword(self, keyword: str) -&gt; List[Dict]:
        """
        动态关键词爬取（单个关键词）
        返回该关键词下的评论数据列表
        """
        print(f"\n🔍 {self.platform} - 爬取关键词: {keyword}")
        
        data_list = []
        
        try:
            if self.platform == "weibo":
                from src.crawlers.selenium_spiders.weibo_spider import WeiboSpider
                spider = WeiboSpider()
                csv_path, content_list = spider.crawl(keyword=keyword)
                if content_list:
                    data_list = content_list
                    
            elif self.platform == "zhihu":
                from src.crawlers.selenium_spiders.zhihu_spider import ZhihuSpider
                spider = ZhihuSpider()
                csv_path, content_list = spider.crawl(keyword=keyword)
                if content_list:
                    data_list = content_list
                    
            elif self.platform == "hupu":
                from src.crawlers.selenium_spiders.hupu_spider import HupuSpider
                spider = HupuSpider()
                csv_path, content_list = spider.crawl(keyword=keyword)
                if content_list:
                    data_list = content_list
                    
            elif self.platform == "tieba":
                from src.crawlers.selenium_spiders.tieba_spider import TiebaSpider
                spider = TiebaSpider()
                csv_path, content_list = spider.crawl(keyword=keyword)
                if content_list:
                    data_list = content_list
                    
        except Exception as e:
            print(f"❌ {self.platform} 爬取关键词 '{keyword}' 失败: {e}")
            import traceback
            traceback.print_exc()
            
            log_file = os.path.join(self.crawl_data_path, f"{keyword}_error_{int(time.time())}.log")
            with open(log_file, "w", encoding="utf-8") as f:
                f.write(f"Error: {str(e)}\n")
                f.write(traceback.format_exc())
        
        return data_list
    
    def crawl_batch(self, keywords: List[str]) -&gt; List[str]:
        """
        批量关键词爬取
        """
        print(f"\n{'='*80}")
        print(f"🚀 {self.platform} 批量爬取启动 - {len(keywords)} 个关键词")
        print(f"{'='*80}")
        
        crawler_config = self.config.get_crawler_config()
        if crawler_config.get("cleanup_on_start", True):
            self._cleanup_temp_files()
        
        saved_files = []
        max_keywords = crawler_config.get("max_keywords_per_platform", 10)
        
        for idx, keyword in enumerate(keywords[:max_keywords]):
            print(f"\n--- [{idx+1}/{min(len(keywords), max_keywords)}] ---")
            
            data_list = self.crawl_keyword(keyword)
            
            if data_list:
                saved_file = self._save_structured_data(keyword, data_list)
                saved_files.append(saved_file)
            else:
                print(f"⚠️  {self.platform} 关键词 '{keyword}' 未获取到数据")
            
            time.sleep(2)
        
        print(f"\n✅ {self.platform} 批量爬取完成！保存了 {len(saved_files)} 个文件")
        return saved_files


def main():
    print("=" * 80)
    print("🕷️  多平台数据规范化爬取 - 示例调用")
    print("=" * 80)
    
    test_keywords = [
        "上海迪士尼 公共设施 满意度",
        "上海迪士尼 服务态度",
        "上海迪士尼 排队时间",
        "上海迪士尼 环境设施"
    ]
    
    platforms = ["weibo", "zhihu", "hupu", "tieba"]
    
    all_saved_files = []
    
    for platform in platforms:
        crawler = PlatformCrawler(platform)
        saved_files = crawler.crawl_batch(test_keywords)
        all_saved_files.extend(saved_files)
    
    print(f"\n{'='*80}")
    print("📊 所有平台爬取完成！")
    print(f"{'='*80}")
    print(f"共保存 {len(all_saved_files)} 个文件:")
    for f in all_saved_files:
        print(f"  📄 {f}")


if __name__ == "__main__":
    main()

