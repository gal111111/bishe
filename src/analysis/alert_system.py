# -*- coding: utf-8 -*-
"""
满意度预警系统模块
使用静态、动态和自适应阈值进行预警
"""
import os
import sys
import json
import numpy as np
import pandas as pd
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

class AlertSystem:
    """满意度预警系统"""
    
    def __init__(self):
        """初始化预警系统"""
        self.static_threshold = 60  # 静态阈值
        self.dynamic_window = 7  # 动态窗口大小
        self.adaptive_alpha = 0.2  # 自适应学习率
        
    def static_alert(self, df: pd.DataFrame) -> list:
        """静态阈值预警"""
        alerts = []
        
        if 'csi_score' not in df.columns:
            return alerts
        
        # 基于静态阈值的预警
        low_score_records = df[df['csi_score'] < self.static_threshold]
        
        for idx, record in low_score_records.iterrows():
            alerts.append({
                'index': idx,
                'facility_type': record.get('facility_type', '未知'),
                'aspect': record.get('aspect', '未知'),
                'csi_score': record['csi_score'],
                'content': record.get('content', ''),
                'alert_type': 'static',
                'severity': self._calculate_severity(record['csi_score']),
                'timestamp': datetime.now().isoformat()
            })
        
        return alerts
    
    def dynamic_alert(self, df: pd.DataFrame) -> list:
        """动态阈值预警"""
        alerts = []
        
        if 'csi_score' not in df.columns:
            return alerts
        
        if 'date' not in df.columns:
            # 如果没有日期列，使用索引作为时间
            df = df.copy()
            df['date'] = pd.date_range(start='2024-01-01', periods=len(df), freq='D')
        
        # 按日期排序
        df_sorted = df.sort_values('date')
        
        # 计算滚动平均值和标准差
        df_sorted['rolling_mean'] = df_sorted['csi_score'].rolling(window=self.dynamic_window, min_periods=1).mean()
        df_sorted['rolling_std'] = df_sorted['csi_score'].rolling(window=self.dynamic_window, min_periods=1).std().fillna(0)
        
        # 动态阈值 = 滚动平均值 - 滚动标准差
        df_sorted['dynamic_threshold'] = df_sorted['rolling_mean'] - df_sorted['rolling_std']
        
        # 标记异常点
        for idx, record in df_sorted.iterrows():
            if record['csi_score'] < record['dynamic_threshold']:
                alerts.append({
                    'index': idx,
                    'facility_type': record.get('facility_type', '未知'),
                    'aspect': record.get('aspect', '未知'),
                    'csi_score': record['csi_score'],
                    'dynamic_threshold': record['dynamic_threshold'],
                    'content': record.get('content', ''),
                    'alert_type': 'dynamic',
                    'severity': self._calculate_severity(record['csi_score']),
                    'timestamp': datetime.now().isoformat()
                })
        
        return alerts
    
    def adaptive_static_alert(self, df: pd.DataFrame) -> list:
        """自适应静态阈值预警"""
        alerts = []
        
        if 'csi_score' not in df.columns:
            return alerts
        
        # 计算初始平均值
        initial_mean = df['csi_score'].mean()
        adaptive_threshold = initial_mean * 0.8  # 初始自适应阈值
        
        # 自适应调整阈值
        for idx, record in df.iterrows():
            # 更新自适应阈值
            adaptive_threshold = adaptive_threshold * (1 - self.adaptive_alpha) + record['csi_score'] * self.adaptive_alpha
            
            # 预警判断
            if record['csi_score'] < adaptive_threshold * 0.8:
                alerts.append({
                    'index': idx,
                    'facility_type': record.get('facility_type', '未知'),
                    'aspect': record.get('aspect', '未知'),
                    'csi_score': record['csi_score'],
                    'adaptive_threshold': adaptive_threshold,
                    'content': record.get('content', ''),
                    'alert_type': 'adaptive',
                    'severity': self._calculate_severity(record['csi_score']),
                    'timestamp': datetime.now().isoformat()
                })
        
        return alerts
    
    def combo_alert(self, df: pd.DataFrame) -> list:
        """组合预警"""
        alerts = []
        
        if 'csi_score' not in df.columns:
            return alerts
        
        # 获取静态预警
        static_alerts = self.static_alert(df)
        
        # 获取动态预警
        dynamic_alerts = self.dynamic_alert(df)
        
        # 获取自适应预警
        adaptive_alerts = self.adaptive_static_alert(df)
        
        # 合并预警，去除重复
        all_alerts = static_alerts + dynamic_alerts + adaptive_alerts
        
        # 去重
        seen = set()
        unique_alerts = []
        for alert in all_alerts:
            alert_key = (alert['facility_type'], alert['content'][:50])
            if alert_key not in seen:
                seen.add(alert_key)
                unique_alerts.append(alert)
        
        # 标记组合预警
        for alert in unique_alerts:
            if any(a['index'] == alert['index'] for a in static_alerts) and any(a['index'] == alert['index'] for a in dynamic_alerts):
                alert['alert_type'] = 'combo'
                alert['severity'] = min(alert['severity'] + 1, 5)  # 提高严重程度
        
        return unique_alerts
    
    def _calculate_severity(self, csi_score: float) -> int:
        """计算预警严重程度"""
        if csi_score < 40:
            return 5  # 严重
        elif csi_score < 50:
            return 4  # 较严重
        elif csi_score < 60:
            return 3  # 中等
        elif csi_score < 70:
            return 2  # 轻微
        else:
            return 1  # 提示
    
    def generate_alert_report(self, alerts: list) -> str:
        """生成预警报告"""
        if not alerts:
            return "当前无预警信息"
        
        report = "# 满意度预警报告\n\n"
        report += f"**报告生成时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"**预警总数:** {len(alerts)}\n\n"
        
        # 按严重程度分组
        severity_groups = {1: [], 2: [], 3: [], 4: [], 5: []}
        for alert in alerts:
            severity_groups[alert['severity']].append(alert)
        
        # 按严重程度排序输出
        severity_levels = {5: '严重', 4: '较严重', 3: '中等', 2: '轻微', 1: '提示'}
        
        for severity in sorted(severity_groups.keys(), reverse=True):
            if severity_groups[severity]:
                report += f"## {severity_levels[severity]}预警 ({len(severity_groups[severity])}个)\n\n"
                
                for alert in severity_groups[severity]:
                    report += f"### {alert['facility_type']} - {alert['aspect']}\n"
                    report += f"- 满意度指数: {alert['csi_score']}\n"
                    report += f"- 预警类型: {alert['alert_type']}\n"
                    report += f"- 内容: {alert['content'][:100]}...\n\n"
        
        # 统计信息
        report += "## 统计信息\n\n"
        report += f"- 严重预警: {len(severity_groups[5])}个\n"
        report += f"- 较严重预警: {len(severity_groups[4])}个\n"
        report += f"- 中等预警: {len(severity_groups[3])}个\n"
        report += f"- 轻微预警: {len(severity_groups[2])}个\n"
        report += f"- 提示预警: {len(severity_groups[1])}个\n\n"
        
        # 预警建议
        report += "## 预警建议\n\n"
        report += "1. **严重预警**: 立即采取措施，优先解决\n"
        report += "2. **较严重预警**: 制定计划，在短期内解决\n"
        report += "3. **中等预警**: 纳入常规改进计划\n"
        report += "4. **轻微预警**: 持续关注，定期评估\n"
        report += "5. **提示预警**: 作为参考，优化服务\n"
        
        return report

if __name__ == "__main__":
    # 测试
    df = pd.DataFrame({
        'content': ["服务态度很差", "环境很脏", "设施很旧", "服务态度很好", "环境很干净"],
        'facility_type': ["广州图书馆", "广州图书馆", "广州图书馆", "广州图书馆", "广州图书馆"],
        'aspect': ["服务态度", "环境", "设施", "服务态度", "环境"],
        'csi_score': [30, 45, 55, 85, 90],
        'date': pd.date_range(start='2024-01-01', periods=5, freq='D')
    })
    
    alert_system = AlertSystem()
    
    # 测试静态预警
    static_alerts = alert_system.static_alert(df)
    print(f"静态预警: {len(static_alerts)}个")
    
    # 测试动态预警
    dynamic_alerts = alert_system.dynamic_alert(df)
    print(f"动态预警: {len(dynamic_alerts)}个")
    
    # 测试自适应预警
    adaptive_alerts = alert_system.adaptive_static_alert(df)
    print(f"自适应预警: {len(adaptive_alerts)}个")
    
    # 测试组合预警
    combo_alerts = alert_system.combo_alert(df)
    print(f"组合预警: {len(combo_alerts)}个")
    
    # 生成预警报告
    report = alert_system.generate_alert_report(combo_alerts)
    print("\n预警报告:")
    print(report)
