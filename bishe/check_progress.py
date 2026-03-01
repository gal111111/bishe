# -*- coding: utf-8 -*-
"""
检查爬虫进度
"""
import os
import pandas as pd

data_dir = "data/raw"

print("=" * 80)
print("📊 爬虫进度统计")
print("=" * 80)

for platform in ['weibo', 'zhihu', 'tieba', 'hupu']:
    files = [f for f in os.listdir(data_dir) if f.startswith(platform) and f.endswith('.csv')]
    if files:
        # 获取最新的文件
        files.sort(key=lambda x: os.path.getmtime(os.path.join(data_dir, x)), reverse=True)
        latest_file = files[0]
        filepath = os.path.join(data_dir, latest_file)
        
        try:
            df = pd.read_csv(filepath)
            row_count = len(df)
            print(f"\n📱 {platform.upper()}")
            print(f"   文件: {latest_file}")
            print(f"   数据行数: {row_count}")
            print(f"   文件大小: {os.path.getsize(filepath)/1024:.1f} KB")
            print(f"   修改时间: {pd.to_datetime(os.path.getmtime(filepath), unit='s')}")
        except Exception as e:
            print(f"\n📱 {platform.upper()}: 读取失败 - {e}")
    else:
        print(f"\n📱 {platform.upper()}: 暂无数据")

print("\n" + "=" * 80)
