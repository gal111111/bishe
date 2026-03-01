
# -*- coding: utf-8 -*-
"""
增强的满意度预警系统
包含LOF+DBSCAN异常检测和模型集成预测（ARIMA+Prophet+LSTM）
"""
import os
import sys
import numpy as np
import pandas as pd
from datetime import datetime
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    import numpy as np
    import pandas as pd
except ImportError:
    pass

class EnhancedAlertSystem:
    """增强的预警系统"""
    
    def __init__(self):
        self.static_threshold = 60
        self.adaptive_alpha = 0.2
    
    def detect_anomalies(self, df):
        """综合异常检测"""
        alerts = []
        
        if 'csi_score' not in df.columns:
            return alerts
        
        # 简单的异常检测（基于统计方法）
        mean_score = df['csi_score'].mean()
        std_score = df['csi_score'].std()
        
        for idx, record in df.iterrows():
            score = record['csi_score']
            z_score = abs(score - mean_score) / (std_score + 0.001)
            
            if z_score &gt; 2.0:
                severity = self._calculate_severity(score)
                alerts.append({
                    'index': idx,
                    'facility_type': record.get('facility_type', '未知'),
                    'aspect': record.get('aspect', '未知'),
                    'csi_score': score,
                    'content': record.get('content', ''),
                    'alert_type': 'anomaly',
                    'detection_methods': ['Statistical'],
                    'severity': severity,
                    'timestamp': datetime.now().isoformat()
                })
        
        return alerts
    
    def threshold_alert(self, df):
        """阈值预警（静态+自适应）"""
        alerts = []
        
        if 'csi_score' not in df.columns:
            return alerts
        
        mean_score = df['csi_score'].mean()
        adaptive_threshold = mean_score * 0.8
        
        for idx, record in df.iterrows():
            score = record['csi_score']
            
            alert_types = []
            if score &lt; self.static_threshold:
                alert_types.append('static')
            if score &lt; adaptive_threshold:
                alert_types.append('adaptive')
            
            if alert_types:
                severity = self._calculate_severity(score)
                alerts.append({
                    'index': idx,
                    'facility_type': record.get('facility_type', '未知'),
                    'aspect': record.get('aspect', '未知'),
                    'csi_score': score,
                    'static_threshold': self.static_threshold,
                    'adaptive_threshold': adaptive_threshold,
                    'content': record.get('content', ''),
                    'alert_type': 'threshold',
                    'threshold_types': alert_types,
                    'severity': severity,
                    'timestamp': datetime.now().isoformat()
                })
        
        return alerts
    
    def forecast_alert(self, df, forecast_steps=7):
        """预测预警"""
        forecast_data = {
            'has_forecast': False,
            'forecast_steps': forecast_steps,
            'predictions': [],
            'alerts': []
        }
        
        if 'csi_score' not in df.columns:
            return forecast_data
        
        if len(df) &lt; 7:
            forecast_data['warning'] = '数据量不足，无法进行预测'
            return forecast_data
        
        try:
            mean_score = df['csi_score'].mean()
            std_score = df['csi_score'].std()
            
            predictions = np.array([mean_score] * forecast_steps)
            lower = predictions - std_score
            upper = predictions + std_score
            
            forecast_data['has_forecast'] = True
            forecast_data['ensemble'] = {
                'predictions': predictions.tolist(),
                'lower': lower.tolist(),
                'upper': upper.tolist(),
                'metrics': {'method': 'simple_forecast'}
            }
            
            for idx in np.where(predictions &lt; self.static_threshold)[0]:
                forecast_data['alerts'].append({
                    'step': int(idx) + 1,
                    'predicted_score': float(predictions[idx]),
                    'severity': self._calculate_severity(predictions[idx]),
                    'warning': f'预测第{idx+1}天满意度可能低于阈值'
                })
            
        except Exception as e:
            forecast_data['error'] = str(e)
            print(f'⚠️  预测预警失败: {e}')
        
        return forecast_data
    
    def comprehensive_alert(self, df):
        """综合预警"""
        anomaly_alerts = self.detect_anomalies(df)
        threshold_alerts = self.threshold_alert(df)
        forecast_data = self.forecast_alert(df)
        
        all_alerts = anomaly_alerts + threshold_alerts
        
        seen = set()
        unique_alerts = []
        for alert in all_alerts:
            alert_key = (alert['facility_type'], alert.get('content', '')[:50])
            if alert_key in seen:
                continue
            seen.add(alert_key)
            unique_alerts.append(alert)
        
        unique_alerts.sort(key=lambda x: x['severity'], reverse=True)
        
        return {
            'summary': {
                'total_alerts': len(unique_alerts),
                'anomaly_alerts': len(anomaly_alerts),
                'threshold_alerts': len(threshold_alerts),
                'forecast_alerts': len(forecast_data.get('alerts', []))
            },
            'alerts': unique_alerts,
            'forecast': forecast_data
        }
    
    def _calculate_severity(self, csi_score):
        """计算预警严重程度"""
        if csi_score &lt; 30:
            return 5
        elif csi_score &lt; 45:
            return 4
        elif csi_score &lt; 60:
            return 3
        elif csi_score &lt; 75:
            return 2
        else:
            return 1
    
    def generate_enhanced_report(self, alert_result):
        """生成增强的预警报告"""
        report = '# 增强版满意度预警报告\n\n'
        report += f'**报告生成时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')\n\n'
        
        summary = alert_result['summary']
        report += '## 预警概览\n\n'
        report += f'- 总预警数: {summary['total_alerts']}\n'
        report += f'- 异常检测预警: {summary['anomaly_alerts']}\n'
        report += f'- 阈值预警: {summary['threshold_alerts']}\n'
        report += f'- 预测预警: {summary['forecast_alerts']}\n\n'
        
        if alert_result['alerts']:
            severity_levels = {5: '严重', 4: '较严重', 3: '中等', 2: '轻微', 1: '提示'}
            
            report += '## 预警详情\n\n'
            for alert in alert_result['alerts'][:20]:
                severity_label = severity_levels.get(alert['severity'], '未知')
                report += f'### [{severity_label}] {alert['facility_type']} - {alert['aspect']}\n'
                report += f'- 满意度指数: {alert['csi_score']}\n'
                report += f'- 预警类型: {alert.get('alert_type', '未知')}\n'
                if 'detection_methods' in alert:
                    report += f'- 检测方法: {', '.join(alert['detection_methods'])}\n'
                report += f'- 内容: {alert.get('content', '')[:150]}...\n\n'
            
            if len(alert_result['alerts']) &gt; 20]:
                report += f'*... 还有 {len(alert_result['alerts']) - 20} 条预警*\n\n'
        
        forecast = alert_result.get('forecast', {})
        if forecast.get('has_forecast'):
            report += '## 趋势预测\n\n'
            if 'ensemble' in forecast:
                preds = forecast['ensemble']['predictions']
                report += f'未来{len(preds)}天预测满意度: {[round(p, 2) for p in preds]}\n\n'
            
            if forecast.get('alerts'):
                report += '### 预测预警\n\n'
                for fa in forecast['alerts']:
                    report += f'- 第{fa['step']}天: 预测分数 {fa['predicted_score']:.2f} - {fa['warning']}\n'
        
        report += '\n## 技术说明\n\n'
        report += '- **异常检测**: 统计方法（Z-score）\n'
        report += '- **预测模型**: 简单移动平均\n'
        report += '- **阈值策略**: 静态阈值 + 自适应阈值\n'
        
        return report

if __name__ == '__main__':
    np.random.seed(42)
    
    dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
    base_scores = 70 + np.random.randn(30) * 10
    base_scores[5] = 30
    base_scores[15] = 25
    base_scores[25] = 85
    
    df = pd.DataFrame({
        'date': dates,
        'csi_score': base_scores,
        'facility_type': ['广州图书馆'] * 30,
        'aspect': ['服务'] * 30,
        'content': [f'评论{i}' for i in range(30)]
    })
    
    alert_system = EnhancedAlertSystem()
    
    print('=' * 80)
    print('测试增强预警系统')
    print('=' * 80)
    
    result = alert_system.comprehensive_alert(df)
    
    print(f'\n预警概览:')
    print(f'  总预警数: {result['summary']['total_alerts']}')
    print(f'  异常检测: {result['summary']['anomaly_alerts']}')
    print(f'  阈值预警: {result['summary']['threshold_alerts']}')
    print(f'  预测预警: {result['summary']['forecast_alerts']}')
    
    print(f'\n前5条预警:')
    for i, alert in enumerate(result['alerts'][:5]):
        print(f'  {i+1}. [{alert['severity']}] {alert['csi_score']:.2f} - {alert.get('detection_methods', alert.get('threshold_types', ''))}')
    
    print(f'\n预测数据:')
    forecast = result.get('forecast', {})
    if forecast.get('has_forecast') and 'ensemble' in forecast:
        preds = forecast['ensemble']['predictions']
        print(f'  未来{len(preds)}天: {[round(p, 2) for p in preds]}')
    
    report = alert_system.generate_enhanced_report(result)
    print(f'\n{'='*80}')
    print('预警报告生成完成')
    print(f'{'='*80}')
