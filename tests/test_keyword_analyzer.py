import unittest
from unittest.mock import patch
from src.seo_automation.keyword_analyzer import KeywordAnalyzer


class TestKeywordAnalyzer(unittest.TestCase):
    
    def setUp(self):
        self.analyzer = KeywordAnalyzer()
    
    def test_preprocess_text(self):
        """测试文本预处理功能"""
        text = "This is a test text! It contains some numbers (123) and special characters."
        processed = self.analyzer._preprocess_text(text)
        
        # 检查停用词被移除
        self.assertNotIn('this', processed)
        self.assertNotIn('is', processed)
        self.assertNotIn('a', processed)
        
        # 检查特殊字符被移除
        self.assertNotIn('!', processed)
        self.assertNotIn('(', processed)
        self.assertNotIn(')', processed)
        
        # 检查实际单词保留
        self.assertIn('test', processed)
        self.assertIn('text', processed)
        self.assertIn('contains', processed)
        self.assertIn('numbers', processed)
        self.assertIn('special', processed)
        self.assertIn('characters', processed)
    
    def test_extract_keywords(self):
        """测试关键词提取功能"""
        text = "SEO is important for websites. SEO helps in ranking higher. SEO optimization is crucial."
        keywords = self.analyzer.extract_keywords(text)
        
        # 应该正确提取主要关键词
        keyword_list = [kw[0] for kw in keywords]
        self.assertIn('seo', keyword_list)
        self.assertIn('important', keyword_list)
        self.assertIn('websites', keyword_list)
        
        # 'seo'应该是最常见的关键词
        self.assertEqual(keywords[0][0], 'seo')
        self.assertEqual(keywords[0][1], 3)  # 出现3次
    
    def test_calculate_keyword_density(self):
        """测试关键词密度计算"""
        text = "SEO is important for SEO optimization. SEO helps in website ranking."
        keywords = ['seo', 'important', 'ranking']
        density = self.analyzer.calculate_keyword_density(text, keywords)
        
        # 计算总词数：text中除停用词外约有8个词，'seo'出现3次
        # 密度 = 3/8 * 100 ≈ 37.5%
        self.assertAlmostEqual(density['seo'], 37.5, places=1)
        self.assertAlmostEqual(density['important'], 12.5, places=1)
        self.assertAlmostEqual(density['ranking'], 12.5, places=1)
    
    def test_calculate_keyword_density_empty_text(self):
        """测试空文本的关键词密度计算"""
        text = ""
        keywords = ['seo', 'test']
        density = self.analyzer.calculate_keyword_density(text, keywords)
        
        self.assertEqual(density['seo'], 0.0)
        self.assertEqual(density['test'], 0.0)
    
    def test_analyze_page_keywords(self):
        """测试页面关键词分析功能"""
        page_data = {
            'url': 'https://example.com/test',
            'title': 'SEO Optimization Tips',
            'meta_description': 'Learn about SEO optimization techniques for better ranking.',
            'meta_keywords': 'seo, optimization, ranking',
            'content': 'SEO is crucial for websites. This article provides SEO optimization tips to improve your website ranking. SEO techniques include keyword research, content optimization, and link building.',
            'headings': {
                'h1': ['SEO Optimization Strategies'],
                'h2': ['Keyword Research', 'Content Optimization']
            }
        }
        
        analysis = self.analyzer.analyze_page_keywords(page_data)
        
        # 检查基本信息
        self.assertEqual(analysis['url'], 'https://example.com/test')
        self.assertTrue(analysis['meta_keywords_present'])
        
        # 检查提取的关键词
        extracted_keywords = [kw[0] for kw in analysis['extracted_keywords']]
        self.assertIn('seo', extracted_keywords)
        
        # 检查标题中的关键词分析
        self.assertTrue(analysis['title_keyword_analysis']['seo']['present'])
        
        # 检查H1中的关键词
        self.assertIn('seo', analysis['heading_keyword_analysis']['h1'])
    
    def test_multiple_pages_analysis(self):
        """测试多页面分析功能"""
        pages_data = {
            'page1': {
                'url': 'https://example.com/page1',
                'title': 'SEO Tips',
                'content': 'SEO is important for websites.',
                'meta_keywords': 'seo, tips',
                'headings': {'h1': ['SEO Best Practices']}
            },
            'page2': {
                'url': 'https://example.com/page2',
                'title': 'Website Optimization',
                'content': 'Optimizing your website for SEO can improve ranking.',
                'meta_keywords': 'website, optimization, seo',
                'headings': {'h1': ['Website SEO Guide']}
            }
        }
        
        results = self.analyzer.analyze_multiple_pages(pages_data)
        
        # 检查共有关键词
        common_keywords = [kw[0] for kw in results['common_keywords']]
        self.assertIn('seo', common_keywords)
        
        # 检查关键词覆盖率
        self.assertIn('seo', results['keyword_coverage'])
        self.assertEqual(results['keyword_coverage']['seo']['coverage_percentage'], 100.0)


if __name__ == '__main__':
    unittest.main()