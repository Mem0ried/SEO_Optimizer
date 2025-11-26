import unittest
import os
import tempfile
from unittest.mock import patch, MagicMock, mock_open
from src.seo_automation.report_generator import ReportGenerator, get_report_generator


class TestReportGenerator(unittest.TestCase):
    """测试报告生成器类"""
    
    def setUp(self):
        """设置测试环境"""
        self.report_generator = ReportGenerator()
        
        # 创建模拟SEO分析结果
        self.mock_seo_results = {
            'page_scores': {
                'https://example.com/page1': {
                    'url': 'https://example.com/page1',
                    'scores': {
                        'content': 85.5,
                        'keywords': 75.0,
                        'meta_tags': 88.0,
                        'performance': 72.0,
                        'technical': 80.0
                    },
                    'overall_score': 80.1,
                    'detailed_analysis': {},
                    'improvement_suggestions': [
                        '优化页面加载速度',
                        '增加关键词密度'
                    ]
                },
                'https://example.com/page2': {
                    'url': 'https://example.com/page2',
                    'scores': {
                        'content': 70.0,
                        'keywords': 82.0,
                        'meta_tags': 75.0,
                        'performance': 88.0,
                        'technical': 78.0
                    },
                    'overall_score': 78.6,
                    'detailed_analysis': {},
                    'improvement_suggestions': [
                        '增加内容长度'
                    ]
                }
            },
            'overall_scores': {
                'content': 77.75,
                'keywords': 78.5,
                'meta_tags': 81.5,
                'performance': 80.0,
                'technical': 79.0,
                'weighted_total': 79.35
            },
            'site_analysis': {
                'total_pages': 2,
                'category_scores': {
                    'content': 77.75,
                    'keywords': 78.5,
                    'meta_tags': 81.5,
                    'performance': 80.0,
                    'technical': 79.0
                },
                'strengths': [
                    '元标签 (得分: 81.5)',
                    '性能 (得分: 80.0)'
                ],
                'weaknesses': [
                    '内容质量 (得分: 77.75)'
                ],
                'overall_rating': '良好',
                'overall_comment': '您的网站SEO状况良好，有小部分可以优化的空间。'
            },
            'overall_suggestions': [
                '提高网站内容质量',
                '优化关键词策略',
                '定期更新网站内容'
            ]
        }
        
        # 创建模拟关键词分析结果
        self.mock_keyword_results = {
            'page_analyses': {
                'https://example.com/page1': {
                    'keyword_density': {'example': 2.5},
                    'title_keyword_analysis': {'example': {'present': True}}
                }
            },
            'overall_recommendations': [
                '增加长尾关键词覆盖率'
            ]
        }
    
    def test_initialization(self):
        """测试报告生成器初始化"""
        self.assertIsInstance(self.report_generator, ReportGenerator)
        self.assertTrue(hasattr(self.report_generator, 'env'))
        self.assertTrue(hasattr(self.report_generator, 'output_dir'))
    
    def test_get_category_name(self):
        """测试获取类别中文名称"""
        self.assertEqual(self.report_generator._get_category_name('content'), '内容质量')
        self.assertEqual(self.report_generator._get_category_name('keywords'), '关键词优化')
        self.assertEqual(self.report_generator._get_category_name('meta_tags'), '元标签')
        self.assertEqual(self.report_generator._get_category_name('performance'), '性能')
        self.assertEqual(self.report_generator._get_category_name('technical'), '技术SEO')
        self.assertEqual(self.report_generator._get_category_name('unknown'), 'unknown')
    
    def test_prepare_report_data(self):
        """测试准备报告数据"""
        report_data = self.report_generator._prepare_report_data(
            self.mock_seo_results, self.mock_keyword_results
        )
        
        # 验证数据结构
        self.assertIn('site_url', report_data)
        self.assertEqual(report_data['site_url'], 'example.com')
        self.assertIn('report_date', report_data)
        self.assertEqual(report_data['total_pages'], 2)
        self.assertEqual(report_data['overall_score'], 79.35)
        self.assertEqual(report_data['overall_rating'], '良好')
        self.assertEqual(report_data['strengths'], ['元标签 (得分: 81.5)', '性能 (得分: 80.0)'])
        self.assertEqual(report_data['weaknesses'], ['内容质量 (得分: 77.75)'])
        self.assertEqual(len(report_data['page_scores']), 2)
    
    @patch('src.seo_automation.report_generator.open', new_callable=mock_open)
    @patch('src.seo_automation.report_generator.os.path.exists', return_value=True)
    @patch('src.seo_automation.report_generator.ensure_directory')
    def test_generate_html_report_with_path(self, mock_ensure_dir, mock_exists, mock_file):
        """测试生成指定路径的HTML报告"""
        with patch.object(self.report_generator.env, 'get_template') as mock_get_template:
            # 模拟模板渲染
            mock_template = MagicMock()
            mock_template.render.return_value = '<html>测试报告</html>'
            mock_get_template.return_value = mock_template
            
            # 生成报告
            output_path = 'test_path/seo_report.html'
            result_path = self.report_generator.generate_html_report(
                self.mock_seo_results, output_path, self.mock_keyword_results
            )
            
            # 验证结果
            self.assertEqual(result_path, output_path)
            mock_get_template.assert_called_once_with('seo_report.html')
            mock_template.render.assert_called_once()
            mock_ensure_dir.assert_called_once_with('test_path')
            mock_file.assert_called_once_with(output_path, 'w', encoding='utf-8')
    
    @patch('src.seo_automation.report_generator.datetime')
    @patch('src.seo_automation.report_generator.open', new_callable=mock_open)
    @patch('src.seo_automation.report_generator.os.path.exists', return_value=True)
    def test_generate_html_report_default_path(self, mock_exists, mock_file, mock_datetime):
        """测试使用默认路径生成HTML报告"""
        # 模拟当前时间
        mock_datetime.now.return_value.strftime.return_value = '20230101_120000'
        
        with patch.object(self.report_generator.env, 'get_template') as mock_get_template:
            # 模拟模板渲染
            mock_template = MagicMock()
            mock_template.render.return_value = '<html>测试报告</html>'
            mock_get_template.return_value = mock_template
            
            # 生成报告
            result_path = self.report_generator.generate_html_report(
                self.mock_seo_results, None, self.mock_keyword_results
            )
            
            # 验证结果
            expected_path = os.path.join(self.report_generator.output_dir, 'seo_report_20230101_120000.html')
            self.assertEqual(result_path, expected_path)
    
    @patch('src.seo_automation.report_generator.ReportGenerator.generate_html_report')
    @patch('src.seo_automation.report_generator.open', new_callable=mock_open)
    def test_save_results_to_json(self, mock_file, mock_generate_html):
        """测试保存结果为JSON"""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # 保存JSON结果
            result_path = self.report_generator.save_results_to_json(self.mock_seo_results, temp_path)
            
            # 验证结果
            self.assertEqual(result_path, temp_path)
        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    @patch('src.seo_automation.report_generator.ReportGenerator.generate_html_report')
    @patch('src.seo_automation.report_generator.ReportGenerator.generate_pdf_report')
    def test_generate_report_format_selection(self, mock_generate_pdf, mock_generate_html):
        """测试根据格式生成不同类型的报告"""
        # 设置模拟返回值
        mock_generate_html.return_value = 'html_report_path.html'
        mock_generate_pdf.return_value = 'pdf_report_path.pdf'
        
        # 测试生成HTML报告
        html_result = self.report_generator.generate_report(
            self.mock_seo_results, format_type='html'
        )
        self.assertEqual(html_result, 'html_report_path.html')
        mock_generate_html.assert_called_once()
        mock_generate_pdf.assert_not_called()
        
        # 重置模拟
        mock_generate_html.reset_mock()
        mock_generate_pdf.reset_mock()
        
        # 测试生成PDF报告
        pdf_result = self.report_generator.generate_report(
            self.mock_seo_results, format_type='pdf'
        )
        self.assertEqual(pdf_result, 'pdf_report_path.pdf')
        mock_generate_html.assert_not_called()
        mock_generate_pdf.assert_called_once()
    
    @patch('src.seo_automation.report_generator.get_report_generator')
    def test_get_report_generator_factory(self, mock_get_report_generator):
        """测试报告生成器工厂函数"""
        # 设置模拟返回值
        mock_generator = MagicMock()
        mock_get_report_generator.return_value = mock_generator
        
        # 调用工厂函数
        result = get_report_generator()
        
        # 验证结果
        mock_get_report_generator.assert_called_once()
        self.assertEqual(result, mock_generator)
    
    def test_ensure_directory(self):
        """测试确保目录存在的功能"""
        with tempfile.TemporaryDirectory() as temp_dir:
            new_dir = os.path.join(temp_dir, 'new_subdir')
            
            # 确认目录不存在
            self.assertFalse(os.path.exists(new_dir))
            
            # 调用函数创建目录
            from src.seo_automation.report_generator import ensure_directory
            ensure_directory(new_dir)
            
            # 确认目录已创建
            self.assertTrue(os.path.exists(new_dir))
            
            # 再次调用函数（目录已存在的情况）
            ensure_directory(new_dir)
            # 不应抛出异常
            self.assertTrue(os.path.exists(new_dir))
    
    @patch('src.seo_automation.report_generator.open', side_effect=IOError('写入失败'))
    def test_generate_html_report_error(self, mock_open_error):
        """测试生成HTML报告时的错误处理"""
        with patch.object(self.report_generator.env, 'get_template') as mock_get_template:
            # 模拟模板渲染
            mock_template = MagicMock()
            mock_template.render.return_value = '<html>测试报告</html>'
            mock_get_template.return_value = mock_template
            
            # 验证抛出异常
            with self.assertRaises(Exception):
                self.report_generator.generate_html_report(
                    self.mock_seo_results, 'error_path.html'
                )
    
    @patch('src.seo_automation.report_generator.datetime')
    @patch('src.seo_automation.report_generator.ReportGenerator.generate_html_report')
    def test_generate_pdf_with_weasyprint(self, mock_generate_html, mock_datetime):
        """测试使用WeasyPrint生成PDF报告"""
        # 模拟当前时间
        mock_datetime.now.return_value.strftime.return_value = '20230101_120000'
        mock_generate_html.return_value = 'test_html_path.html'
        
        # 模拟WeasyPrint
        with patch('src.seo_automation.report_generator.HTML') as mock_html_class:
            mock_html_instance = MagicMock()
            mock_html_class.return_value = mock_html_instance
            
            # 生成PDF报告
            output_path = 'test_pdf_path.pdf'
            result_path = self.report_generator.generate_pdf_report(
                self.mock_seo_results, output_path
            )
            
            # 验证结果
            self.assertEqual(result_path, output_path)
            mock_html_class.assert_called_once_with(filename='test_html_path.html')
            mock_html_instance.write_pdf.assert_called_once_with(output_path)
    
    @patch('src.seo_automation.report_generator.ReportGenerator.generate_html_report')
    def test_generate_pdf_no_weasyprint_with_pdfkit(self, mock_generate_html):
        """测试没有WeasyPrint但有pdfkit时生成PDF报告"""
        mock_generate_html.return_value = 'test_html_path.html'
        
        # 模拟导入错误（没有WeasyPrint）和pdfkit
        with patch('src.seo_automation.report_generator.HTML', side_effect=ImportError()):
            with patch('src.seo_automation.report_generator.pdfkit') as mock_pdfkit:
                # 生成PDF报告
                output_path = 'test_pdf_path.pdf'
                result_path = self.report_generator.generate_pdf_report(
                    self.mock_seo_results, output_path
                )
                
                # 验证结果
                self.assertEqual(result_path, output_path)
                mock_pdfkit.from_file.assert_called_once_with('test_html_path.html', output_path)
    
    @patch('src.seo_automation.report_generator.ReportGenerator.generate_html_report')
    def test_generate_pdf_no_libraries(self, mock_generate_html):
        """测试没有PDF生成库时的错误处理"""
        mock_generate_html.return_value = 'test_html_path.html'
        
        # 模拟两个库都没有安装
        with patch('src.seo_automation.report_generator.HTML', side_effect=ImportError()):
            with patch('src.seo_automation.report_generator.pdfkit', side_effect=ImportError()):
                # 验证抛出异常
                with self.assertRaises(ImportError):
                    self.report_generator.generate_pdf_report(
                        self.mock_seo_results, 'test_pdf_path.pdf'
                    )


if __name__ == '__main__':
    unittest.main()