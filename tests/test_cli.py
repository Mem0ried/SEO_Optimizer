import unittest
from unittest.mock import patch, MagicMock
import click.testing
from src.seo_automation.cli import main


class TestCLI(unittest.TestCase):
    
    def setUp(self):
        self.runner = click.testing.CliRunner()
    
    def test_info_command(self):
        """测试info命令输出"""
        result = self.runner.invoke(main, ['info'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('SEO自动化分析工具', result.output)
        self.assertIn('版本:', result.output)
        self.assertIn('功能:', result.output)
    
    @patch('src.seo_automation.cli.get_crawler')
    def test_crawl_command_valid_url(self, mock_get_crawler):
        """测试crawl命令使用有效URL"""
        # 模拟爬虫返回值
        mock_crawler = MagicMock()
        mock_crawler.crawl.return_value = {
            'https://example.com': {'status_code': 200, 'content_length': 1000},
            'https://example.com/page1': {'status_code': 200, 'content_length': 500}
        }
        mock_get_crawler.return_value = mock_crawler
        
        # 运行命令
        result = self.runner.invoke(main, ['crawl', 'https://example.com', '--depth', '1'])
        
        # 验证结果
        self.assertEqual(result.exit_code, 0)
        self.assertIn('开始爬取网站: https://example.com', result.output)
        self.assertIn('爬取完成！', result.output)
        self.assertIn('总页面数: 2', result.output)
        mock_get_crawler.assert_called_once()
        mock_crawler.crawl.assert_called_once()
    
    def test_crawl_command_invalid_url(self):
        """测试crawl命令使用无效URL"""
        result = self.runner.invoke(main, ['crawl', 'invalid-url'])
        self.assertEqual(result.exit_code, 0)  # click不会返回错误码，但会输出错误信息
        self.assertIn('错误: invalid-url 不是有效的URL', result.output)
    
    @patch('src.seo_automation.cli.get_crawler')
    @patch('src.seo_automation.cli.get_keyword_analyzer')
    @patch('src.seo_automation.cli._generate_simple_report')
    def test_analyze_command(self, mock_generate_report, mock_get_analyzer, mock_get_crawler):
        """测试analyze命令"""
        # 模拟爬虫返回值
        mock_crawler = MagicMock()
        mock_crawler.crawl.return_value = {
            'https://example.com': {
                'url': 'https://example.com',
                'title': 'Test Page',
                'content': 'Test content with seo keywords',
                'meta_keywords': 'seo, test',
                'headings': {'h1': ['Test Heading']}
            }
        }
        mock_get_crawler.return_value = mock_crawler
        
        # 模拟分析器返回值
        mock_analyzer = MagicMock()
        mock_analyzer.analyze_multiple_pages.return_value = {
            'common_keywords': [('seo', 1), ('test', 1)],
            'keyword_coverage': {
                'seo': {'coverage_percentage': 100.0},
                'test': {'coverage_percentage': 100.0}
            },
            'overall_recommendations': ['Test recommendation']
        }
        mock_get_analyzer.return_value = mock_analyzer
        
        # 运行命令
        result = self.runner.invoke(main, [
            'analyze', 
            'https://example.com', 
            '--output', 'test_report.html'
        ])
        
        # 验证结果
        self.assertEqual(result.exit_code, 0)
        self.assertIn('开始分析网站SEO', result.output)
        self.assertIn('SEO分析摘要', result.output)
        self.assertIn('test_report.html', result.output)
        
        # 验证调用
        mock_get_crawler.assert_called_once()
        mock_crawler.crawl.assert_called_once()
        mock_get_analyzer.assert_called_once()
        mock_analyzer.analyze_multiple_pages.assert_called_once()
        mock_generate_report.assert_called_once()


if __name__ == '__main__':
    unittest.main()