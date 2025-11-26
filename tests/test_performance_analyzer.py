import unittest
from unittest.mock import patch, MagicMock, mock_open
import time
import tempfile
import os
from src.seo_automation.performance_analyzer import PerformanceAnalyzer, get_performance_analyzer


class TestPerformanceAnalyzer(unittest.TestCase):
    """测试性能分析器类"""
    
    def setUp(self):
        """设置测试环境"""
        self.analyzer = PerformanceAnalyzer(timeout=10)
        self.test_url = 'https://example.com'
        
    def test_initialization(self):
        """测试性能分析器初始化"""
        # 测试默认参数
        analyzer_default = PerformanceAnalyzer()
        self.assertEqual(analyzer_default.timeout, 30)
        self.assertIsNotNone(analyzer_default.user_agent)
        self.assertIsNotNone(analyzer_default.session)
        
        # 测试自定义参数
        custom_timeout = 15
        custom_ua = 'Test User Agent'
        analyzer_custom = PerformanceAnalyzer(timeout=custom_timeout, user_agent=custom_ua)
        self.assertEqual(analyzer_custom.timeout, custom_timeout)
        self.assertEqual(analyzer_custom.user_agent, custom_ua)
    
    def test_get_performance_grade(self):
        """测试获取性能等级"""
        self.assertEqual(self.analyzer.get_performance_grade(95), '优秀')
        self.assertEqual(self.analyzer.get_performance_grade(80), '良好')
        self.assertEqual(self.analyzer.get_performance_grade(70), '一般')
        self.assertEqual(self.analyzer.get_performance_grade(50), '较差')
        self.assertEqual(self.analyzer.get_performance_grade(30), '差')
    
    @patch('src.seo_automation.performance_analyzer.requests.Session.get')
    def test_measure_page_load_metrics(self, mock_get):
        """测试测量页面加载指标"""
        # 模拟响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'<html><body>Test Content</body></html>'
        mock_response.headers = {
            'Content-Type': 'text/html',
            'Content-Encoding': 'gzip'
        }
        mock_get.return_value = mock_response
        
        # 调用方法
        metrics = self.analyzer._measure_page_load_metrics(self.test_url)
        
        # 验证结果
        self.assertEqual(metrics['url'], self.test_url)
        self.assertEqual(metrics['status_code'], 200)
        self.assertEqual(metrics['content_type'], 'text/html')
        self.assertEqual(metrics['content_encoding'], 'gzip')
        self.assertTrue('page_load_time' in metrics)
        self.assertTrue('ttfb' in metrics)
        self.assertTrue('page_size' in metrics)
        mock_get.assert_called_once_with(self.test_url, timeout=10, stream=True)
    
    def test_calculate_metric_score(self):
        """测试指标评分计算"""
        # 测试页面加载时间评分
        thresholds = {
            'excellent': 1.0,
            'good': 2.0,
            'fair': 3.0,
            'poor': 5.0
        }
        
        # 优秀分数
        self.assertAlmostEqual(
            self.analyzer._calculate_metric_score(0.5, thresholds),
            100.0,
            places=1
        )
        
        # 良好分数区间
        self.assertAlmostEqual(
            self.analyzer._calculate_metric_score(1.5, thresholds),
            80.0 + ((2.0 - 1.5) / (2.0 - 1.0)) * 20.0,
            places=1
        )
        
        # 一般分数区间
        self.assertAlmostEqual(
            self.analyzer._calculate_metric_score(2.5, thresholds),
            60.0 + ((3.0 - 2.5) / (3.0 - 2.0)) * 20.0,
            places=1
        )
        
        # 较差分数区间
        self.assertAlmostEqual(
            self.analyzer._calculate_metric_score(4.0, thresholds),
            40.0 + ((5.0 - 4.0) / (5.0 - 3.0)) * 20.0,
            places=1
        )
        
        # 差分数
        self.assertAlmostEqual(
            self.analyzer._calculate_metric_score(6.0, thresholds),
            40.0 - (6.0 / 5.0 - 1.0) * 5.0,
            places=1
        )
    
    def test_calculate_performance_scores(self):
        """测试计算性能评分"""
        # 创建模拟指标数据
        metrics = {
            'page_load_time': 1.5,
            'ttfb': 0.4,
            'page_size': 800000,
            'status_code': 200,
            'content_type': 'text/html',
            'content_encoding': 'gzip',
            'headers_size': 500,
            'content': '<html>test</html>'
        }
        
        resources = {
            'total_resources': 40,
            'resources_by_type': {
                'css': 5,
                'javascript': 10,
                'images': 20,
                'fonts': 3,
                'other': 2
            },
            'estimated_total_size': 1200000,
            'estimated_sizes_by_type': {},
            'has_large_images': False,
            'has_inline_css': False,
            'has_inline_js': False
        }
        
        # 计算分数
        scores = self.analyzer._calculate_performance_scores(metrics, resources)
        
        # 验证结果包含所有必要的字段
        self.assertIn('load_time_score', scores)
        self.assertIn('ttfb_score', scores)
        self.assertIn('page_size_score', scores)
        self.assertIn('requests_count_score', scores)
        self.assertIn('weighted_total', scores)
        
        # 验证加权总分计算正确
        expected_total = (
            scores['load_time_score'] * 0.4 +
            scores['ttfb_score'] * 0.2 +
            scores['page_size_score'] * 0.2 +
            scores['requests_count_score'] * 0.2
        )
        self.assertAlmostEqual(scores['weighted_total'], expected_total, places=1)
    
    def test_generate_optimization_suggestions(self):
        """测试生成优化建议"""
        # 创建模拟数据 - 低分情况
        metrics = {
            'page_load_time': 6.0,
            'ttfb': 1.8,
            'page_size': 4000000,
            'content_encoding': 'none',
            'status_code': 200,
            'content_type': 'text/html',
            'headers_size': 500,
            'content': '<html>test</html>'
        }
        
        resources = {
            'total_resources': 200,
            'resources_by_type': {'images': 30},
            'has_large_images': True,
            'has_inline_css': True,
            'has_inline_js': True
        }
        
        scores = {
            'load_time_score': 30,
            'ttfb_score': 25,
            'page_size_score': 20,
            'requests_count_score': 15,
            'weighted_total': 22
        }
        
        # 生成建议
        suggestions = self.analyzer._generate_optimization_suggestions(metrics, resources, scores)
        
        # 验证生成了多个建议
        self.assertGreater(len(suggestions), 5)
        
        # 验证包含预期的建议
        expected_suggestions = [
            '优化页面加载时间',
            '优化服务器响应时间',
            '减小页面大小',
            '减少HTTP请求数量',
            '优化图片资源',
            '检查并优化大尺寸图片',
            '避免大量内联CSS',
            '避免大量内联JavaScript',
            '启用Gzip或Brotli压缩',
            '考虑实施前端性能优化技术'
        ]
        
        for expected in expected_suggestions:
            found = False
            for suggestion in suggestions:
                if expected in suggestion:
                    found = True
                    break
            self.assertTrue(found, f'预期的建议未找到: {expected}')
    
    @patch('src.seo_automation.performance_analyzer.PerformanceAnalyzer._measure_page_load_metrics')
    @patch('src.seo_automation.performance_analyzer.PerformanceAnalyzer._calculate_performance_scores')
    @patch('src.seo_automation.performance_analyzer.PerformanceAnalyzer._generate_optimization_suggestions')
    def test_analyze_page_performance_no_resources(self, mock_suggestions, mock_scores, mock_metrics):
        """测试不分析资源的页面性能分析"""
        # 设置模拟返回值
        mock_metrics.return_value = {
            'url': self.test_url,
            'page_load_time': 1.2,
            'ttfb': 0.3,
            'page_size': 500000,
            'content': '<html>test</html>'
        }
        
        mock_scores.return_value = {
            'load_time_score': 90,
            'ttfb_score': 95,
            'page_size_score': 85,
            'requests_count_score': 80,
            'weighted_total': 88
        }
        
        mock_suggestions.return_value = ['测试建议']
        
        # 调用分析方法
        result = self.analyzer.analyze_page_performance(self.test_url, analyze_resources=False)
        
        # 验证结果
        self.assertEqual(result['url'], self.test_url)
        self.assertEqual(result['load_time_metrics'], mock_metrics.return_value)
        self.assertEqual(result['performance_scores'], mock_scores.return_value)
        self.assertEqual(result['optimization_suggestions'], mock_suggestions.return_value)
        self.assertEqual(result['resources_analysis'], {})
        
        # 验证方法调用
        mock_metrics.assert_called_once_with(self.test_url)
        mock_scores.assert_called_once()
        mock_suggestions.assert_called_once()
    
    @patch('src.seo_automation.performance_analyzer.PerformanceAnalyzer._measure_page_load_metrics')
    @patch('src.seo_automation.performance_analyzer.PerformanceAnalyzer._analyze_page_resources')
    @patch('src.seo_automation.performance_analyzer.PerformanceAnalyzer._calculate_performance_scores')
    @patch('src.seo_automation.performance_analyzer.PerformanceAnalyzer._generate_optimization_suggestions')
    def test_analyze_page_performance_with_resources(self, mock_suggestions, mock_scores, 
                                                   mock_resources, mock_metrics):
        """测试分析资源的页面性能分析"""
        # 设置模拟返回值
        mock_metrics.return_value = {
            'url': self.test_url,
            'page_load_time': 1.2,
            'ttfb': 0.3,
            'page_size': 500000,
            'content': '<html>test</html>'
        }
        
        mock_resources.return_value = {
            'total_resources': 30,
            'resources_by_type': {'css': 5, 'javascript': 10, 'images': 15}
        }
        
        # 调用分析方法
        result = self.analyzer.analyze_page_performance(self.test_url, analyze_resources=True)
        
        # 验证资源分析被调用
        mock_resources.assert_called_once_with(self.test_url, '<html>test</html>')
        self.assertEqual(result['resources_analysis'], mock_resources.return_value)
    
    @patch('src.seo_automation.performance_analyzer.PerformanceAnalyzer.analyze_page_performance')
    def test_analyze_multiple_pages(self, mock_page_analyze):
        """测试分析多个页面"""
        # 设置模拟返回值
        urls = ['https://example.com/page1', 'https://example.com/page2']
        
        mock_page_analyze.side_effect = [
            {
                'url': urls[0],
                'load_time_metrics': {
                    'page_load_time': 1.0,
                    'ttfb': 0.2,
                    'page_size': 400000
                },
                'performance_scores': {'weighted_total': 92}
            },
            {
                'url': urls[1],
                'load_time_metrics': {
                    'page_load_time': 1.5,
                    'ttfb': 0.4,
                    'page_size': 600000
                },
                'performance_scores': {'weighted_total': 85}
            }
        ]
        
        # 调用分析方法
        result = self.analyzer.analyze_multiple_pages(urls)
        
        # 验证结果
        self.assertEqual(result['total_pages_analyzed'], 2)
        self.assertEqual(result['successful_analyses'], 2)
        self.assertEqual(result['failed_analyses'], 0)
        self.assertEqual(len(result['page_results']), 2)
        
        # 验证平均指标
        self.assertAlmostEqual(result['average_metrics']['average_load_time'], 1.25)
        self.assertAlmostEqual(result['average_metrics']['average_ttfb'], 0.3)
        self.assertAlmostEqual(result['average_metrics']['average_page_size'], 500000)
        self.assertAlmostEqual(result['average_metrics']['average_weighted_score'], 88.5)
    
    def test_calculate_average_metrics(self):
        """测试计算平均性能指标"""
        # 创建测试数据
        results = [
            {
                'url': 'https://example.com/page1',
                'load_time_metrics': {
                    'page_load_time': 1.0,
                    'ttfb': 0.2,
                    'page_size': 400000
                },
                'performance_scores': {'weighted_total': 92}
            },
            {
                'url': 'https://example.com/page2',
                'load_time_metrics': {
                    'page_load_time': 1.5,
                    'ttfb': 0.4,
                    'page_size': 600000
                },
                'performance_scores': {'weighted_total': 85}
            },
            {
                'url': 'https://example.com/page3',
                'load_time_metrics': {
                    'page_load_time': 2.0,
                    'ttfb': 0.6,
                    'page_size': 800000
                },
                'performance_scores': {'weighted_total': 78}
            }
        ]
        
        # 计算平均指标
        avg_metrics = self.analyzer._calculate_average_metrics(results)
        
        # 验证结果
        self.assertAlmostEqual(avg_metrics['average_load_time'], 1.5)
        self.assertAlmostEqual(avg_metrics['median_load_time'], 1.5)
        self.assertAlmostEqual(avg_metrics['average_ttfb'], 0.4)
        self.assertAlmostEqual(avg_metrics['median_ttfb'], 0.4)
        self.assertAlmostEqual(avg_metrics['average_page_size'], 600000)
        self.assertAlmostEqual(avg_metrics['median_page_size'], 600000)
        self.assertAlmostEqual(avg_metrics['average_weighted_score'], 85)
        self.assertAlmostEqual(avg_metrics['median_weighted_score'], 85)
        self.assertEqual(avg_metrics['best_page_score'], 92)
        self.assertEqual(avg_metrics['worst_page_score'], 78)
    
    @patch('src.seo_automation.performance_analyzer.requests.Session.get', side_effect=Exception('Connection error'))
    def test_analyze_page_performance_error(self, mock_get):
        """测试页面性能分析错误处理"""
        # 调用可能出错的方法
        result = self.analyzer.analyze_page_performance(self.test_url)
        
        # 验证错误处理
        self.assertEqual(result['url'], self.test_url)
        self.assertIn('error', result)
        self.assertIn('Connection error', result['error'])
    
    def test_get_performance_analyzer_factory(self):
        """测试性能分析器工厂函数"""
        # 使用默认参数
        analyzer_default = get_performance_analyzer()
        self.assertIsInstance(analyzer_default, PerformanceAnalyzer)
        
        # 使用自定义参数
        analyzer_custom = get_performance_analyzer(timeout=20, user_agent='Custom UA')
        self.assertIsInstance(analyzer_custom, PerformanceAnalyzer)
        self.assertEqual(analyzer_custom.timeout, 20)
        self.assertEqual(analyzer_custom.user_agent, 'Custom UA')


if __name__ == '__main__':
    unittest.main()