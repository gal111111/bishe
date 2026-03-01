# -*- coding: utf-8 -*-
"""
时间序列分析模块
使用ARIMA、Prophet和LSTM进行时间序列分析和预测
"""
import os
import sys
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 尝试导入必要的库
try:
    from statsmodels.tsa.arima.model import ARIMA
except ImportError:
    print("⚠️  statsmodels not installed. ARIMA modeling will not be available.")
    print("To install statsmodels, run: pip install statsmodels")
    ARIMA = None

try:
    from prophet import Prophet
except ImportError:
    print("⚠️  Prophet not installed. Time series prediction will not be available.")
    print("To install Prophet, run: pip install prophet")
    Prophet = None

try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
except ImportError:
    print("⚠️  TensorFlow not available. LSTM dynamic alert disabled")
    print("⚠️  TensorFlow not available. LSTM prediction disabled")
    tf = None
    Sequential = None
    LSTM = None
    Dense = None
    Dropout = None

class TimeSeriesAnalyzer:
    """时间序列分析器"""
    
    def __init__(self, output_dir: str):
        """初始化时间序列分析器"""
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
    
    def detect_changepoints_pelt(self, scores: List[float]) -> List[int]:
        """使用PELT算法检测变点"""
        # 简单的变点检测实现
        changepoints = []
        
        if len(scores) < 5:
            return changepoints
        
        # 计算相邻点之间的差异
        diffs = [abs(scores[i] - scores[i-1]) for i in range(1, len(scores))]
        
        # 找到差异大于阈值的点
        threshold = np.mean(diffs) + 2 * np.std(diffs) if diffs else 0
        
        for i, diff in enumerate(diffs):
            if diff > threshold:
                changepoints.append(i+1)  # +1 因为差异是i和i+1之间的
        
        return changepoints
    
    def plot_trends_with_changepoints(self, df: pd.DataFrame, score_col: str = 'csi_score', title: str = '满意度趋势与变点检测', filename: str = 'trends.png') -> Optional[str]:
        """绘制趋势图并标记变点"""
        try:
            # 确保日期列存在
            if 'date' not in df.columns:
                df = df.copy()
                df['date'] = pd.date_range(start='2024-01-01', periods=len(df), freq='D')
            
            # 按日期排序
            df_sorted = df.sort_values('date')
            
            # 准备数据
            dates = df_sorted['date']
            scores = df_sorted[score_col]
            
            # 检测变点
            changepoints = self.detect_changepoints_pelt(scores.tolist())
            
            # 创建图表
            plt.figure(figsize=(12, 6))
            plt.plot(dates, scores, 'b-', label='满意度指数')
            
            # 标记变点
            for cp in changepoints:
                if cp < len(dates):
                    plt.axvline(x=dates.iloc[cp], color='r', linestyle='--', alpha=0.7, label='变点' if cp == changepoints[0] else "")
            
            # 添加标题和标签
            plt.title(title, fontsize=16)
            plt.xlabel('日期', fontsize=12)
            plt.ylabel('满意度指数', fontsize=12)
            plt.grid(True, alpha=0.3)
            plt.legend()
            plt.tight_layout()
            
            # 保存图表
            output_path = os.path.join(self.output_dir, filename)
            plt.savefig(output_path)
            plt.close()
            
            print(f"✅ 趋势图已保存: {output_path}")
            return output_path
        except Exception as e:
            print(f"⚠️  绘制趋势图失败: {e}")
            return None
    
    def predict_with_prophet(self, df: pd.DataFrame, periods: int = 7, value_col: str = 'csi_score') -> Dict[str, Any]:
        """使用Prophet进行预测"""
        if not Prophet:
            return {"error": "Prophet not installed"}
        
        try:
            # 准备数据
            if 'date' not in df.columns:
                df = df.copy()
                df['date'] = pd.date_range(start='2024-01-01', periods=len(df), freq='D')
            
            # 按日期排序
            df_sorted = df.sort_values('date')
            
            # 准备Prophet格式的数据
            prophet_df = pd.DataFrame({
                'ds': df_sorted['date'],
                'y': df_sorted[value_col]
            })
            
            # 训练模型
            model = Prophet()
            model.fit(prophet_df)
            
            # 创建预测数据框
            future = model.make_future_dataframe(periods=periods)
            
            # 预测
            forecast = model.predict(future)
            
            # 提取预测结果
            predictions = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(periods)
            
            # 格式化结果
            result = {
                "success": True,
                "predictions": [],
                "model_info": {
                    "train_size": len(prophet_df),
                    "forecast_periods": periods
                }
            }
            
            for _, row in predictions.iterrows():
                result["predictions"].append({
                    "date": row['ds'].strftime('%Y-%m-%d'),
                    "value": float(row['yhat']),
                    "lower_bound": float(row['yhat_lower']),
                    "upper_bound": float(row['yhat_upper'])
                })
            
            return result
        except Exception as e:
            print(f"⚠️  Prophet预测失败: {e}")
            return {"error": str(e)}
    
    def plot_predictions(self, df: pd.DataFrame, prediction_result: Dict[str, Any], score_col: str = 'csi_score', title: str = '满意度趋势预测', filename: str = 'prediction.png') -> Optional[str]:
        """绘制预测图"""
        try:
            if "error" in prediction_result or not prediction_result.get("success", False):
                return None
            
            # 确保日期列存在
            if 'date' not in df.columns:
                df = df.copy()
                df['date'] = pd.date_range(start='2024-01-01', periods=len(df), freq='D')
            
            # 按日期排序
            df_sorted = df.sort_values('date')
            
            # 准备历史数据
            historical_dates = df_sorted['date']
            historical_scores = df_sorted[score_col]
            
            # 准备预测数据
            predictions = prediction_result.get("predictions", [])
            if not predictions:
                return None
            
            pred_dates = [datetime.strptime(p['date'], '%Y-%m-%d') for p in predictions]
            pred_values = [p['value'] for p in predictions]
            pred_lower = [p['lower_bound'] for p in predictions]
            pred_upper = [p['upper_bound'] for p in predictions]
            
            # 创建图表
            plt.figure(figsize=(12, 6))
            
            # 绘制历史数据
            plt.plot(historical_dates, historical_scores, 'b-', label='历史满意度')
            
            # 绘制预测数据
            plt.plot(pred_dates, pred_values, 'r-', label='预测满意度')
            
            # 绘制预测区间
            plt.fill_between(pred_dates, pred_lower, pred_upper, color='r', alpha=0.2, label='预测区间')
            
            # 添加标题和标签
            plt.title(title, fontsize=16)
            plt.xlabel('日期', fontsize=12)
            plt.ylabel('满意度指数', fontsize=12)
            plt.grid(True, alpha=0.3)
            plt.legend()
            plt.tight_layout()
            
            # 保存图表
            output_path = os.path.join(self.output_dir, filename)
            plt.savefig(output_path)
            plt.close()
            
            print(f"✅ 预测图已保存: {output_path}")
            return output_path
        except Exception as e:
            print(f"⚠️  绘制预测图失败: {e}")
            return None
    
    def detect_anomalies(self, df: pd.DataFrame, score_col: str = 'csi_score', window: int = 7, threshold: float = 2.0) -> List[int]:
        """检测异常值"""
        try:
            # 确保日期列存在
            if 'date' not in df.columns:
                df = df.copy()
                df['date'] = pd.date_range(start='2024-01-01', periods=len(df), freq='D')
            
            # 按日期排序
            df_sorted = df.sort_values('date')
            
            # 计算滚动平均值和标准差
            df_sorted['rolling_mean'] = df_sorted[score_col].rolling(window=window, min_periods=1).mean()
            df_sorted['rolling_std'] = df_sorted[score_col].rolling(window=window, min_periods=1).std().fillna(0)
            
            # 计算Z-score
            df_sorted['z_score'] = abs((df_sorted[score_col] - df_sorted['rolling_mean']) / (df_sorted['rolling_std'] + 1e-9))
            
            # 找到异常值
            anomalies = df_sorted[df_sorted['z_score'] > threshold].index.tolist()
            
            return anomalies
        except Exception as e:
            print(f"⚠️  检测异常值失败: {e}")
            return []

if __name__ == "__main__":
    # 测试
    df = pd.DataFrame({
        'content': [f"评论{i}" for i in range(30)],
        'csi_score': np.random.normal(70, 10, 30).tolist(),
        'date': pd.date_range(start='2024-01-01', periods=30, freq='D')
    })
    
    # 添加一些异常值
    df.loc[5, 'csi_score'] = 30
    df.loc[15, 'csi_score'] = 95
    df.loc[25, 'csi_score'] = 25
    
    analyzer = TimeSeriesAnalyzer('test_output')
    
    # 测试变点检测
    changepoints = analyzer.detect_changepoints_pelt(df['csi_score'].tolist())
    print(f"变点检测结果: {changepoints}")
    
    # 测试绘制趋势图
    trend_path = analyzer.plot_trends_with_changepoints(df, score_col='csi_score', title='测试满意度趋势与变点检测', filename='test_trends.png')
    print(f"趋势图保存路径: {trend_path}")
    
    # 测试异常检测
    anomalies = analyzer.detect_anomalies(df, score_col='csi_score')
    print(f"异常检测结果: {anomalies}")
    
    # 测试Prophet预测
    if Prophet:
        prediction_result = analyzer.predict_with_prophet(df, periods=7, value_col='csi_score')
        print(f"Prophet预测结果: {prediction_result}")
        
        # 测试绘制预测图
        prediction_path = analyzer.plot_predictions(df, prediction_result, score_col='csi_score', title='测试满意度趋势预测', filename='test_prediction.png')
        print(f"预测图保存路径: {prediction_path}")
