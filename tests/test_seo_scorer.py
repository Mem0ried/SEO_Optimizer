import unittest
from unittest.mock import patch, MagicMock
from src.seo_automation.seo_scorer import SEOScorer, get_seo_scorer


class TestSEOScorer(unittest.TestCase):
    """测试SEO评分器类"""
    
    def setUp(self):
        """设置测试环境"""
        self.scorer = SEOScorer()
        
        # 创建一个模拟页面数据
        self.mock_page_data = {
            'url': 'https://example.com/test-page',
            'title': 'Example Page - SEO Testing',
            'content': 'This is example content for SEO testing. ' * 20,
            'content_length': 400,
            'meta_description': 'This is a description for the example page.',
            'meta_keywords': 'seo, testing, example',
            'headings': {
                'h1': ['Example Page'],
                'h2': ['Introduction', 'Methodology'],
                'h3': ['Results', 'Conclusion']
            },
            'images': [
                {'src': 'image1.jpg', 'alt': 'Example image 1'},
                {'src': 'image2.jpg', 'alt': 'Example image 2'},
                {'src': 'image3.jpg', 'alt': ''}
            ],
            'links': [
                {'href': 'https://example.com/page1', 'text': 'Page 1'},
                {'href': 'https://example.com/page2', 'text': 'Page 2'}
            ],
            'status_code': 200,
            'response_time': 1.5
        }
        
        # 创建模拟关键词分析数据
        self.mock_keyword_analysis = {
            'keyword_density': {
                'seo': 2.5,
                'testing': 1.8
            },
            'title_keyword_analysis': {
                'seo': {'present': True, 'early_in_title': True},
                'testing': {'present': True, 'early_in_title': False}
            },
            'heading_keyword_analysis': {
                'h1': ['example'],
                'h2': ['methodology']
            },
            'keyword_placement': {
                'seo': {'in_early_content': True},
                'testing': {'in_early_content': False}
            },
            'keyword_recommendations': [
                'Consider using more variations of your target keywords'
            ]
        }
    
    def test_initialization(self):
        """测试SEO评分器初始化"""
        self.assertIsInstance(self.scorer, SEOScorer)
        self.assertEqual(len(self.scorer.scores), 5)
        self.assertIn('content', self.scorer.scores)
        self.assertIn('keywords', self.scorer.scores)
        self.assertIn('meta_tags', self.scorer.scores)
        self.assertIn('performance', self.scorer.scores)
        self.assertIn('technical', self.scorer.scores)
    
    def test_score_content(self):
        """测试内容评分功能"""
        # 测试正常内容
        content_score = self.scorer._score_content(self.mock_page_data)
        self.assertGreaterEqual(content_score, 0)
        self.assertLessEqual(content_score, 100)
        
        # 测试内容长度评分
        short_page = self.mock_page_data.copy()
        short_page['content_length'] = 100
        short_content_score = self.scorer._score_content(short_page)
        self.assertLess(short_content_score, content_score)
        
        # 测试标题评分
        no_title_page = self.mock_page_data.copy()
        no_title_page['title'] = ''
        no_title_score = self.scorer._score_content(no_title_page)
        self.assertLess(no_title_score, content_score)
    
    def test_score_keywords(self):
        """测试关键词评分功能"""
        keyword_score = self.scorer._score_keywords(self.mock_page_data, self.mock_keyword_analysis)
        self.assertGreaterEqual(keyword_score, 0)
        self.assertLessEqual(keyword_score, 100)
    
    def test_score_meta_tags(self):
        """测试元标签评分功能"""
        # 测试正常元标签
        meta_score = self.scorer._score_meta_tags(self.mock_page_data)
        self.assertGreaterEqual(meta_score, 0)
        self.assertLessEqual(meta_score, 100)
        
        # 测试无标题
        no_title_page = self.mock_page_data.copy()
        no_title_page['title'] = ''
        no_title_score = self.scorer._score_meta_tags(no_title_page)
        self.assertLess(no_title_score, meta_score)
        
        # 测试无描述
        no_desc_page = self.mock_page_data.copy()
        no_desc_page['meta_description'] = ''
        no_desc_score = self.scorer._score_meta_tags(no_desc_page)
        self.assertLess(no_desc_score, meta_score)
    
    def test_score_performance(self):
        """测试性能评分功能"""
        # 测试正常性能
        perf_score = self.scorer._score_performance(self.mock_page_data)
        self.assertGreaterEqual(perf_score, 0)
        self.assertLessEqual(perf_score, 100)
        
        # 测试慢响应时间
        slow_page = self.mock_page_data.copy()
        slow_page['response_time'] = 6.0
        slow_perf_score = self.scorer._score_performance(slow_page)
        self.assertLess(slow_perf_score, perf_score)
        
        # 测试错误状态码
        error_page = self.mock_page_data.copy()
        error_page['status_code'] = 404
        error_perf_score = self.scorer._score_performance(error_page)
        self.assertLess(error_perf_score, perf_score)
    
    def test_score_technical(self):
        """测试技术SEO评分功能"""
        tech_score = self.scorer._score_technical(self.mock_page_data)
        self.assertGreaterEqual(tech_score, 0)
        self.assertLessEqual(tech_score, 100)
    
    def test_calculate_weighted_score(self):
        """测试加权总分计算"""
        scores = {
            'content': 80,
            'keywords': 70,
            'meta_tags': 90,
            'performance': 85,
            'technical': 75
        }
        
        weighted_score = self.scorer._calculate_weighted_score(scores)
        self.assertGreaterEqual(weighted_score, 0)
        self.assertLessEqual(weighted_score, 100)
    
    def test_score_page(self):
        """测试单页面评分"""
        page_score = self.scorer.score_page(self.mock_page_data, self.mock_keyword_analysis)
        
        # 验证返回结构
        self.assertIn('url', page_score)
        self.assertIn('scores', page_score)
        self.assertIn('overall_score', page_score)
        self.assertIn('detailed_analysis', page_score)
        self.assertIn('improvement_suggestions', page_score)
        
        # 验证评分范围
        for score in page_score['scores'].values():
            self.assertGreaterEqual(score, 0)
            self.assertLessEqual(score, 100)
        
        # 验证总分范围
        self.assertGreaterEqual(page_score['overall_score'], 0)
        self.assertLessEqual(page_score['overall_score'], 100)
    
    def test_score_multiple_pages(self):
        """测试多页面评分"""
        pages_data = {
            'page1': self.mock_page_data,
            'page2': {
                'url': 'https://example.com/page2',
                'title': 'Second Page',
                'content': 'This is the second page content. ' * 10,
                'content_length': 200,
                'meta_description': 'Second page description.',
                'headings': {'h1': ['Second Page']},
                'images': [],
                'links': [],
                'status_code': 200,
                'response_time': 2.0
            },
            'error_page': {
                'url': 'https://example.com/error',
                'error': '404 Not Found',
                'status_code': 404
            }
        }
        
        keyword_results = {
            'page_analyses': {
                'page1': self.mock_keyword_analysis,
                'page2': {
                    'keyword_density': {'second': 1.0},
                    'title_keyword_analysis': {'second': {'present': True}},
                    'keyword_recommendations': []
                }
            },
            'overall_recommendations': [
                'Improve overall content quality'
            ]
        }
        
        results = self.scorer.score_multiple_pages(pages_data, keyword_results)
        
        # 验证返回结构
        self.assertIn('page_scores', results)
        self.assertIn('overall_scores', results)
        self.assertIn('site_analysis', results)
        self.assertIn('overall_suggestions', results)
        
        # 验证页面评分数量（排除错误页面）
        self.assertEqual(len(results['page_scores']), 2)
        
        # 验证总分范围
        self.assertGreaterEqual(results['overall_scores']['weighted_total'], 0)
        self.assertLessEqual(results['overall_scores']['weighted_total'], 100)
    
    def test_generate_improvement_suggestions(self):
        """测试生成改进建议"""
        # 创建一个得分较低的页面数据
        low_score_page = self.mock_page_data.copy()
        low_score_page['content_length'] = 100
        low_score_page['title'] = ''
        low_score_page['meta_description'] = ''
        low_score_page['headings']['h1'] = []
        
        # 模拟详细分析数据
        self.scorer.detailed_analysis = {
            'content': {
                'length': {'score': 5},
                'title': {'score': 0},
                'headings': {'score': 0}
            }
        }
        
        scores = {
            'content': 20,
            'keywords': 80,
            'meta_tags': 30,
            'performance': 80,
            'technical': 80
        }
        
        suggestions = self.scorer._generate_improvement_suggestions(
            low_score_page, self.mock_keyword_analysis, scores
        )
        
        self.assertGreaterEqual(len(suggestions), 1)
        # 验证建议内容
        content_related_suggestions = [s for s in suggestions if '内容' in s]
        self.assertGreaterEqual(len(content_related_suggestions), 1)
    
    def test_get_seo_scorer_factory(self):
        """测试SEO评分器工厂函数"""
        scorer = get_seo_scorer()
        self.assertIsInstance(scorer, SEOScorer)
    
    def test_empty_page_data(self):
        """测试空页面数据"""
        empty_page = {
            'url': 'https://example.com/empty',
            'content_length': 0,
            'status_code': 200
        }
        
        page_score = self.scorer.score_page(empty_page)
        
        # 验证返回结构依然完整
        self.assertIn('url', page_score)
        self.assertIn('scores', page_score)
        self.assertIn('overall_score', page_score)
        
        # 验证内容得分较低
        self.assertLess(page_score['scores']['content'], 50)
    
    def test_no_keyword_analysis(self):
        """测试没有关键词分析的情况"""
        page_score = self.scorer.score_page(self.mock_page_data)
        
        # 验证返回结构依然完整
        self.assertIn('scores', page_score)
        self.assertIn('keywords', page_score['scores'])
        
        # 关键词得分为0
        self.assertEqual(page_score['scores']['keywords'], 0)


if __name__ == '__main__':
    unittest.main()