# -*- coding: utf-8 -*-
"""
性能监控模块
监控系统运行状态、性能指标和资源使用
"""
import os
import sys
import time
import json
import psutil
import functools
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from collections import defaultdict

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, log_file: str = None):
        self.log_file = log_file or os.path.join(PROJECT_ROOT, "data", "cache", "performance_log.json")
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        
        self.metrics = defaultdict(list)
        self.start_times = {}
        self.function_stats = defaultdict(lambda: {
            "call_count": 0,
            "total_time": 0,
            "min_time": float('inf'),
            "max_time": 0,
            "avg_time": 0
        })
    
    def start_timer(self, name: str):
        """开始计时"""
        self.start_times[name] = time.time()
    
    def stop_timer(self, name: str) -> float:
        """停止计时并返回耗时"""
        if name not in self.start_times:
            return 0
        
        elapsed = time.time() - self.start_times[name]
        self.metrics[name].append(elapsed)
        del self.start_times[name]
        
        return elapsed
    
    def record_metric(self, name: str, value: float):
        """记录指标"""
        self.metrics[name].append(value)
    
    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "timestamp": datetime.now().isoformat(),
                "cpu": {
                    "percent": cpu_percent,
                    "count": psutil.cpu_count()
                },
                "memory": {
                    "total": memory.total / (1024 ** 3),
                    "available": memory.available / (1024 ** 3),
                    "percent": memory.percent,
                    "used": memory.used / (1024 ** 3)
                },
                "disk": {
                    "total": disk.total / (1024 ** 3),
                    "used": disk.used / (1024 ** 3),
                    "free": disk.free / (1024 ** 3),
                    "percent": disk.percent
                }
            }
        except:
            return {
                "timestamp": datetime.now().isoformat(),
                "cpu": {"percent": 0, "count": 0},
                "memory": {"total": 0, "available": 0, "percent": 0, "used": 0},
                "disk": {"total": 0, "used": 0, "free": 0, "percent": 0}
            }
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """获取指标摘要"""
        summary = {}
        
        for name, values in self.metrics.items():
            if values:
                summary[name] = {
                    "count": len(values),
                    "min": min(values),
                    "max": max(values),
                    "avg": sum(values) / len(values),
                    "total": sum(values)
                }
        
        return summary
    
    def save_log(self):
        """保存日志"""
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "system_info": self.get_system_info(),
            "metrics_summary": self.get_metrics_summary(),
            "function_stats": dict(self.function_stats)
        }
        
        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2, default=str)
    
    def clear(self):
        """清除所有指标"""
        self.metrics.clear()
        self.start_times.clear()
        self.function_stats.clear()

def timing_decorator(monitor: PerformanceMonitor = None):
    """
    计时装饰器
    
    使用方法:
        @timing_decorator()
        def my_function():
            pass
        
        或
        
        monitor = PerformanceMonitor()
        @timing_decorator(monitor)
        def my_function():
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                elapsed = time.time() - start_time
                
                if monitor:
                    stats = monitor.function_stats[func.__name__]
                    stats["call_count"] += 1
                    stats["total_time"] += elapsed
                    stats["min_time"] = min(stats["min_time"], elapsed)
                    stats["max_time"] = max(stats["max_time"], elapsed)
                    stats["avg_time"] = stats["total_time"] / stats["call_count"]
                    
                    monitor.record_metric(func.__name__, elapsed)
        
        return wrapper
    return decorator

class AnalysisProfiler:
    """分析性能分析器"""
    
    def __init__(self):
        self.monitor = PerformanceMonitor()
        self.analysis_stats = {}
    
    def profile_sentiment_analysis(self, df, method: str = "snownlp"):
        """分析情感分析性能"""
        from src.analysis.sentiment_analysis import analyze_dataframe
        
        self.monitor.start_timer("sentiment_analysis")
        
        start_mem = psutil.Process().memory_info().rss / (1024 ** 2)
        
        result_df = analyze_dataframe(df, preferred=method)
        
        end_mem = psutil.Process().memory_info().rss / (1024 ** 2)
        elapsed = self.monitor.stop_timer("sentiment_analysis")
        
        self.analysis_stats["sentiment_analysis"] = {
            "method": method,
            "data_size": len(df),
            "elapsed_time": elapsed,
            "time_per_record": elapsed / len(df) if len(df) > 0 else 0,
            "memory_used_mb": end_mem - start_mem,
            "timestamp": datetime.now().isoformat()
        }
        
        return result_df
    
    def profile_knowledge_graph(self, df):
        """分析知识图谱构建性能"""
        from src.analysis.knowledge_graph import KnowledgeGraphBuilder
        
        self.monitor.start_timer("knowledge_graph")
        
        builder = KnowledgeGraphBuilder()
        builder.build_from_dataframe(df)
        
        elapsed = self.monitor.stop_timer("knowledge_graph")
        insights = builder.get_insights()
        
        self.analysis_stats["knowledge_graph"] = {
            "data_size": len(df),
            "elapsed_time": elapsed,
            "entities_found": len(insights.get("top_mentioned_entities", [])),
            "timestamp": datetime.now().isoformat()
        }
        
        return insights
    
    def get_full_report(self) -> Dict[str, Any]:
        """获取完整性能报告"""
        return {
            "system_info": self.monitor.get_system_info(),
            "analysis_stats": self.analysis_stats,
            "metrics_summary": self.monitor.get_metrics_summary()
        }

def print_system_status():
    """打印系统状态"""
    monitor = PerformanceMonitor()
    info = monitor.get_system_info()
    
    print("\n" + "=" * 60)
    print("系统状态监控")
    print("=" * 60)
    print(f"时间: {info['timestamp']}")
    print(f"\nCPU:")
    print(f"  使用率: {info['cpu']['percent']}%")
    print(f"  核心数: {info['cpu']['count']}")
    print(f"\n内存:")
    print(f"  总量: {info['memory']['total']:.2f} GB")
    print(f"  已用: {info['memory']['used']:.2f} GB ({info['memory']['percent']}%)")
    print(f"  可用: {info['memory']['available']:.2f} GB")
    print(f"\n磁盘:")
    print(f"  总量: {info['disk']['total']:.2f} GB")
    print(f"  已用: {info['disk']['used']:.2f} GB ({info['disk']['percent']}%)")
    print(f"  可用: {info['disk']['free']:.2f} GB")
    print("=" * 60)

if __name__ == "__main__":
    print("=" * 80)
    print("性能监控模块测试")
    print("=" * 80)
    
    print_system_status()
    
    monitor = PerformanceMonitor()
    
    @timing_decorator(monitor)
    def test_function():
        time.sleep(0.1)
        return "done"
    
    print("\n测试计时装饰器...")
    for _ in range(5):
        test_function()
    
    stats = monitor.function_stats["test_function"]
    print(f"\n函数执行统计:")
    print(f"  调用次数: {stats['call_count']}")
    print(f"  平均耗时: {stats['avg_time']:.4f}s")
    print(f"  最小耗时: {stats['min_time']:.4f}s")
    print(f"  最大耗时: {stats['max_time']:.4f}s")
    
    monitor.save_log()
    print(f"\n✅ 性能日志已保存")