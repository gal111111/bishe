
# -*- coding: utf-8 -*-
"""
模块3：多平台数据合并与整理
合并各平台数据，去重，字段补全
"""
import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Set

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from src.config.config_manager import config_manager


class DataMerger:
    def __init__(self):
        self.config = config_manager
        self.data_config = self.config.get_data_config()
        self.crawl_data_dir = Path(self.config.crawl_data_dir)
        self.merged_data_path = self.config.get_merged_data_path()
    
    def _read_platform_files(self, platform: str) -&gt; List[Dict]:
        """读取单个平台的所有JSON文件"""
        platform_dir = self.crawl_data_dir / platform
        if not platform_dir.exists():
            return []
        
        all_data = []
        json_files = list(platform_dir.glob("*.json"))
        
        print(f"\n📂 读取 {platform} 数据 - {len(json_files)} 个文件")
        
        for json_file in json_files:
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        all_data.extend(data)
                    else:
                        all_data.append(data)
            except Exception as e:
                print(f"⚠️  读取文件失败 {json_file}: {e}")
        
        print(f"   共读取 {len(all_data)} 条数据")
        return all_data
    
    def _deduplicate_data(self, data_list: List[Dict]) -&gt; List[Dict]:
        """
        数据去重
        基于"content"字段去重，过滤空内容数据
        """
        print(f"\n🔍 数据去重...")
        print(f"   去重前: {len(data_list)} 条")
        
        deduplicate_by = self.data_config.get("deduplicate_by", "content")
        min_content_length = self.data_config.get("min_content_length", 5)
        
        seen_contents: Set[str] = set()
        unique_data = []
        
        for item in data_list:
            content = item.get(deduplicate_by, "")
            
            if not content or len(content.strip()) &lt; min_content_length:
                continue
            
            if content not in seen_contents:
                seen_contents.add(content)
                unique_data.append(item)
        
        print(f"   去重后: {len(unique_data)} 条")
        print(f"   去除重复: {len(data_list) - len(unique_data)} 条")
        return unique_data
    
    def _enhance_data(self, data_list: List[Dict]) -&gt; List[Dict]:
        """
        字段补全与增强
        新增"content_length"字段（内容长度），补全"platform"字段（避免空值）
        """
        print(f"\n✨ 字段补全与增强...")
        
        enhanced_data = []
        for item in data_list:
            enhanced_item = item.copy()
            
            if "platform" not in enhanced_item or not enhanced_item["platform"]:
                enhanced_item["platform"] = "unknown"
            
            content = enhanced_item.get("content", "")
            enhanced_item["content_length"] = len(content)
            
            if "sentiment" not in enhanced_item:
                enhanced_item["sentiment"] = None
            
            enhanced_data.append(enhanced_item)
        
        print(f"   增强完成: {len(enhanced_data)} 条")
        return enhanced_data
    
    def merge_all_platforms(self) -&gt; List[Dict]:
        """
        多平台数据合并
        读取所有平台数据，去重，字段补全，合并存储
        """
        print("=" * 80)
        print("📊 多平台数据合并与整理")
        print("=" * 80)
        
        platforms = ["tieba", "weibo", "hupu", "zhihu"]
        all_data = []
        
        for platform in platforms:
            platform_data = self._read_platform_files(platform)
            all_data.extend(platform_data)
        
        print(f"\n📊 原始总数据: {len(all_data)} 条")
        
        if not all_data:
            print("⚠️  没有找到任何数据！")
            return []
        
        deduplicated_data = self._deduplicate_data(all_data)
        
        enhanced_data = self._enhance_data(deduplicated_data)
        
        print(f"\n💾 保存合并数据...")
        with open(self.merged_data_path, "w", encoding="utf-8") as f:
            json.dump(enhanced_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 合并数据已保存: {self.merged_data_path}")
        
        print(f"\n{'='*80}")
        print("📋 合并完成统计")
        print(f"{'='*80}")
        
        platform_counts = {}
        for item in enhanced_data:
            platform = item.get("platform", "unknown")
            platform_counts[platform] = platform_counts.get(platform, 0) + 1
        
        for platform, count in platform_counts.items():
            print(f"  📱 {platform}: {count} 条")
        
        print(f"\n  📊 总有效数据: {len(enhanced_data)} 条")
        
        return enhanced_data


def main():
    print("=" * 80)
    print("📊 多平台数据合并与整理 - 示例调用")
    print("=" * 80)
    
    merger = DataMerger()
    merged_data = merger.merge_all_platforms()
    
    if merged_data:
        print(f"\n🎉 数据合并完成！")
        print(f"📁 合并文件: {merger.merged_data_path}")
        
        print(f"\n📋 前5条数据预览:")
        for i, item in enumerate(merged_data[:5]):
            print(f"\n[{i+1}]")
            print(f"  平台: {item.get('platform')}")
            print(f"  关键词: {item.get('keyword')}")
            print(f"  内容: {item.get('content', '')[:60]}...")
            print(f"  长度: {item.get('content_length')}")


if __name__ == "__main__":
    main()

