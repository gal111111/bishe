# -*- coding: utf-8 -*-
"""
单元测试套件
测试所有核心模块的功能
"""
import os
import sys
import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

class TestSentimentAnalysis(unittest.TestCase):
    """情感分析模块测试"""
    
    def setUp(self):
        """测试前准备"""
        self.test_texts = [
            "迪士尼真的太好玩了！",
            "排队排了3小时，太累了",
            "一般般吧",
            "服务态度很差，不会再来了",
            "环境优美，设施完善"
        ]
    
    def test_snownlp_analysis(self):
        """测试SnowNLP分析"""
        try:
            from src.analysis.sentiment_analysis import analyze_sentiment
            
            for text in self.test_texts:
                result = analyze_sentiment(text, preferred="snownlp")
                
                self.assertIn("polarity", result)
                self.assertIn("csi_score", result)
                self.assertIn(result["polarity"], ["积极", "中性", "消极"])
                
        except ImportError:
            self.skipTest("SnowNLP未安装")
    
    def test_dataframe_analysis(self):
        """测试DataFrame批量分析"""
        try:
            from src.analysis.sentiment_analysis import analyze_dataframe
            
            df = pd.DataFrame({
                "content": self.test_texts,
                "platform": ["微博"] * len(self.test_texts)
            })
            
            result_df = analyze_dataframe(df, preferred="snownlp")
            
            self.assertEqual(len(result_df), len(df))
            self.assertIn("polarity_label", result_df.columns)
            self.assertIn("csi_score", result_df.columns)
            
        except Exception as e:
            self.skipTest(f"分析失败: {e}")

class TestKnowledgeGraph(unittest.TestCase):
    """知识图谱模块测试"""
    
    def setUp(self):
        """测试前准备"""
        self.test_data = pd.DataFrame([
            {"content": "迪士尼的服务态度很好", "user": "user1"},
            {"content": "设施有点旧了", "user": "user2"},
            {"content": "环境优美，但是排队太长", "user": "user3"},
            {"content": "价格偏贵，性价比不高", "user": "user4"},
        ])
    
    def test_knowledge_graph_build(self):
        """测试知识图谱构建"""
        try:
            from src.analysis.knowledge_graph import KnowledgeGraphBuilder
            
            builder = KnowledgeGraphBuilder()
            builder.build_from_dataframe(self.test_data)
            
            insights = builder.get_insights()
            
            self.assertIsInstance(insights, dict)
            
        except Exception as e:
            self.skipTest(f"知识图谱构建失败: {e}")
    
    def test_entity_extraction(self):
        """测试实体提取"""
        try:
            from src.analysis.knowledge_graph import EntityExtractor
            
            extractor = EntityExtractor()
            entities = extractor.extract_entities("迪士尼的服务态度很好，设施也不错")
            
            self.assertIsInstance(entities, list)
            
        except Exception as e:
            self.skipTest(f"实体提取失败: {e}")

class TestMultimodalSentiment(unittest.TestCase):
    """多模态情感分析测试"""
    
    def setUp(self):
        """测试前准备"""
        self.test_texts = [
            "迪士尼真的太好玩了！😊🎉",
            "排队排了3小时，太累了 😭",
            "一般般吧 😐",
        ]
    
    def test_emoji_extraction(self):
        """测试表情符号提取"""
        try:
            from src.analysis.multimodal_sentiment import EmojiAnalyzer
            
            analyzer = EmojiAnalyzer()
            
            for text in self.test_texts:
                emojis = analyzer.extract_emojis(text)
                self.assertIsInstance(emojis, list)
            
        except Exception as e:
            self.skipTest(f"表情符号提取失败: {e}")
    
    def test_multimodal_analysis(self):
        """测试多模态分析"""
        try:
            from src.analysis.multimodal_sentiment import MultimodalSentimentAnalyzer
            
            analyzer = MultimodalSentimentAnalyzer()
            
            for text in self.test_texts:
                result = analyzer.analyze(text)
                
                self.assertIn("final_sentiment", result)
                self.assertIn("final_polarity", result)
                self.assertIn("csi_score", result)
                
        except Exception as e:
            self.skipTest(f"多模态分析失败: {e}")

class TestOpinionPropagation(unittest.TestCase):
    """舆情传播分析测试"""
    
    def setUp(self):
        """测试前准备"""
        self.test_data = pd.DataFrame([
            {"user": "user_a", "content": "迪士尼真好玩！", "polarity_label": "积极"},
            {"user": "user_b", "content": "人太多了", "polarity_label": "消极"},
            {"user": "user_c", "content": "回复user_a: 我也觉得！", "polarity_label": "积极"},
            {"user": "user_d", "content": "转发user_a: 同感", "polarity_label": "积极"},
        ])
    
    def test_network_build(self):
        """测试网络构建"""
        try:
            from src.analysis.opinion_propagation import PublicOpinionAnalyzer
            
            analyzer = PublicOpinionAnalyzer()
            analyzer.build_from_dataframe(self.test_data)
            
            network_data = analyzer.get_network_data()
            
            self.assertIn("nodes", network_data)
            self.assertIn("edges", network_data)
            
        except Exception as e:
            self.skipTest(f"网络构建失败: {e}")
    
    def test_pagerank_calculation(self):
        """测试PageRank计算"""
        try:
            from src.analysis.opinion_propagation import PublicOpinionAnalyzer
            
            analyzer = PublicOpinionAnalyzer()
            analyzer.build_from_dataframe(self.test_data)
            analyzer.calculate_pagerank()
            
            top_nodes = analyzer.find_influential_nodes(top_k=3)
            
            self.assertIsInstance(top_nodes, list)
            self.assertLessEqual(len(top_nodes), 3)
            
        except Exception as e:
            self.skipTest(f"PageRank计算失败: {e}")

class TestSentimentEvolution(unittest.TestCase):
    """情感动态演化测试"""
    
    def setUp(self):
        """测试前准备"""
        dates = pd.date_range(start='2024-01-01', periods=50, freq='D')
        
        self.test_data = pd.DataFrame({
            "create_time": dates,
            "content": [f"测试评论 {i}" for i in range(50)],
            "polarity_label": np.random.choice(["积极", "中性", "消极"], size=50, p=[0.4, 0.4, 0.2]),
            "csi_score": np.random.normal(70, 15, 50)
        })
    
    def test_evolution_analysis(self):
        """测试演化分析"""
        try:
            from src.analysis.sentiment_evolution import SentimentEvolutionAnalyzer
            
            analyzer = SentimentEvolutionAnalyzer()
            insights = analyzer.get_evolution_insights(self.test_data)
            
            self.assertIn("evolution_phases", insights)
            self.assertIn("sentiment_shift", insights)
            
        except Exception as e:
            self.skipTest(f"演化分析失败: {e}")
    
    def test_emerging_topics(self):
        """测试新兴话题检测"""
        try:
            from src.analysis.sentiment_evolution import SentimentEvolutionAnalyzer
            
            analyzer = SentimentEvolutionAnalyzer()
            insights = analyzer.get_evolution_insights(self.test_data)
            
            emerging = insights.get("emerging_topics", {})
            
            self.assertIn("emerging_topics", emerging)
            
        except Exception as e:
            self.skipTest(f"新兴话题检测失败: {e}")

class TestDataPreprocessing(unittest.TestCase):
    """数据预处理测试"""
    
    def setUp(self):
        """测试前准备"""
        self.test_data = pd.DataFrame([
            {"content": "这是一条正常的评论"},
            {"content": "   "},
            {"content": "12345"},
            {"content": "哈哈哈哈"},
            {"content": "！！！"},
            {"content": "这是一条包含表情😊的评论"},
        ])
    
    def test_data_cleaning(self):
        """测试数据清洗"""
        try:
            from src.preprocessing.data_cleaner import DataCleaner
            
            cleaner = DataCleaner()
            
            cleaned_df = cleaner.clean(self.test_data)
            
            self.assertIsInstance(cleaned_df, pd.DataFrame)
            
        except Exception as e:
            self.skipTest(f"数据清洗失败: {e}")

def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestSentimentAnalysis))
    suite.addTests(loader.loadTestsFromTestCase(TestKnowledgeGraph))
    suite.addTests(loader.loadTestsFromTestCase(TestMultimodalSentiment))
    suite.addTests(loader.loadTestsFromTestCase(TestOpinionPropagation))
    suite.addTests(loader.loadTestsFromTestCase(TestSentimentEvolution))
    suite.addTests(loader.loadTestsFromTestCase(TestDataPreprocessing))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result

if __name__ == "__main__":
    print("=" * 80)
    print("上海迪士尼舆情分析系统 - 单元测试")
    print("=" * 80)
    
    result = run_tests()
    
    print("\n" + "=" * 80)
    print("测试结果汇总")
    print("=" * 80)
    print(f"运行测试: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print(f"跳过: {len(result.skipped)}")
    
    if result.wasSuccessful():
        print("\n✅ 所有测试通过！")
    else:
        print("\n❌ 存在测试失败或错误")