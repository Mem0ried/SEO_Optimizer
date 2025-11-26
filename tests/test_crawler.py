import unittest
from unittest.mock import patch, MagicMock
from src.seo_automation.crawler import WebCrawler, get_crawler
import requests


class TestWebCrawler(unittest.TestCase):
    
    def setUp(self):
        self.test_url = "https://example.com"
        self.crawler = WebCrawler(self.test_url, depth=1, max_pages=5)
    
    def test_is_valid_url(self):
        """测试URL验证功能"""
        # 有效的URL
        self.assertTrue(self.crawler._is_valid_url("https://example.com/page"))
        self.assertTrue(self.crawler._is_valid_url("https://sub.example.com/page"))
        
        # 无效的URL
        self.assertFalse(self.crawler._is_valid_url("https://other-site.com"))
        self.assertFalse(self.crawler._is_valid_url("javascript:void(0)"))
        self.assertFalse(self.crawler._is_valid_url("#section"))
        self.assertFalse(self.crawler._is_valid_url("https://example.com/image.jpg"))
    
    @patch('requests.Session.get')
    def test_crawl_page_basic(self, mock_get):
        """测试基本页面爬取功能"""
        # 模拟响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.elapsed.total_seconds.return_value = 0.5
        mock_response.headers = {'Content-Type': 'text/html'}
        mock_response.text = """
        <html>
            <head>
                <title>Test Page</title>
                <meta name="description" content="Test description">
                <meta name="keywords" content="test,keywords">
            </head>
            <body>
                <h1>Test H1</h1>
                <p>Test content</p>
                <a href="/page2">Page 2</a>
                <img src="/image.jpg" alt="Test Image">
            </body>
        </html>
        """
        mock_get.return_value = mock_response
        
        # 执行爬取
        self.crawler._crawl_page(self.test_url, 0)
        
        # 验证结果
        self.assertIn(self.test_url, self.crawler.pages)
        page_data = self.crawler.pages[self.test_url]
        
        self.assertEqual(page_data['title'], "Test Page")
        self.assertEqual(page_data['meta_description'], "Test description")
        self.assertEqual(page_data['meta_keywords'], "test,keywords")
        self.assertEqual(page_data['headings']['h1'], ["Test H1"])
        self.assertIn("Test content", page_data['content'])
        self.assertEqual(page_data['status_code'], 200)
        self.assertEqual(page_data['response_time'], 0.5)
        self.assertEqual(len(page_data['links']), 1)
        self.assertEqual(len(page_data['images']), 1)
    
    @patch('requests.Session.get')
    def test_crawl_page_error(self, mock_get):
        """测试页面爬取错误处理"""
        mock_get.side_effect = requests.RequestException("Connection error")
        
        self.crawler._crawl_page(self.test_url, 0)
        
        self.assertIn(self.test_url, self.crawler.pages)
        self.assertIn('error', self.crawler.pages[self.test_url])
        self.assertEqual(self.crawler.pages[self.test_url]['error'], "Connection error")
    
    def test_get_crawler_factory(self):
        """测试爬虫工厂函数"""
        # 默认返回WebCrawler
        crawler = get_crawler(self.test_url)
        self.assertIsInstance(crawler, WebCrawler)
        
        # 并发爬虫
        from src.seo_automation.crawler import ConcurrentWebCrawler
        crawler = get_crawler(self.test_url, concurrent=True)
        self.assertIsInstance(crawler, ConcurrentWebCrawler)


if __name__ == '__main__':
    unittest.main()