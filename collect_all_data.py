


# -*- coding: utf-8 -*-
"""
收集所有可用的数据到data/latest文件夹
"""
import os
import shutil
import pandas as pd
from datetime import datetime

project_root = os.path.dirname(os.path.abspath(__file__))
raw_data_dir = os.path.join(project_root, "data", "raw")
latest_data_dir = os.path.join(project_root, "data", "latest")

os.makedirs(latest_data_dir, exist_ok=True)

print("=" * 80)
print("收集所有可用的数据")
print("=" * 80)

platforms = ["weibo", "zhihu", "tieba", "hupu"]
keyword = "上海迪士尼"

total_data_count = 0
collected_files = []

for platform in platforms:
    print(f"\n处理 {platform} 数据...")
    
    platform_files = []
    for filename in os.listdir(raw_data_dir):
        if filename.startswith(f"{platform}_raw_{keyword}") and filename.endswith(".csv"):
            platform_files.append(filename)
    
    platform_files.sort(reverse=True)
    print(f"  找到 {len(platform_files)} 个文件")
    
    all_data = []
    for filename in platform_files:
        file_path = os.path.join(raw_data_dir, filename)
        try:
            df = pd.read_csv(file_path, encoding='utf-8-sig')
            print(f"  - {filename}: {len(df)} 条数据")
            all_data.append(df)
        except Exception as e:
            print(f"  - {filename}: 读取失败 - {e}")
    
    if all_data:
        merged_df = pd.concat(all_data, ignore_index=True)
        
        merged_df = merged_df.drop_duplicates()
        
        date_str = datetime.now().strftime("%Y%m%d")
        output_path = os.path.join(latest_data_dir, f"{platform}_raw_{keyword}_{date_str}.csv")
        
        merged_df.to_csv(output_path, index=False, encoding='utf-8-sig')
        
        print(f"  合并后: {len(merged_df)} 条数据 (去重后)")
        print(f"  已保存到: {output_path}")
        
        total_data_count += len(merged_df)
        collected_files.append(output_path)

print("\n" + "=" * 80)
print("数据收集完成！")
print(f"总数据量: {total_data_count} 条")
print(f"收集的文件: {len(collected_files)} 个")
print("=" * 80)

print("\n收集的文件列表:")
for f in collected_files:
    print(f"  - {os.path.basename(f)}")

