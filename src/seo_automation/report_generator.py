import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def ensure_directory(directory: str) -> None:
    """确保目录存在，如果不存在则创建"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"创建目录: {directory}")


class ReportGenerator:
    """SEO报告生成器，支持HTML和PDF格式输出"""
    
    def __init__(self):
        # 设置Jinja2环境
        templates_dir = os.path.join(os.path.dirname(__file__), '../../templates')
        ensure_directory(templates_dir)
        
        self.env = Environment(
            loader=FileSystemLoader(templates_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )
        
        # 如果模板不存在，创建默认模板
        self._create_default_templates(templates_dir)
        
        # 报告输出目录
        self.output_dir = os.path.join(os.path.dirname(__file__), '../../output')
        ensure_directory(self.output_dir)
    
    def _create_default_templates(self, templates_dir: str) -> None:
        """创建默认的HTML报告模板"""
        html_template_path = os.path.join(templates_dir, 'seo_report.html')
        
        if not os.path.exists(html_template_path):
            html_template_content = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SEO分析报告 - {{ site_url }}</title>
    <style>
        /* 全局样式 */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: #fff;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }
        
        /* 头部样式 */
        .header {
            background: linear-gradient(135deg, #2c3e50, #3498db);
            color: white;
            padding: 40px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 600;
        }
        
        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }
        
        .header .meta {
            margin-top: 20px;
            font-size: 0.9em;
            opacity: 0.8;
        }
        
        /* 主内容样式 */
        .content {
            padding: 40px;
        }
        
        .section {
            margin-bottom: 40px;
        }
        
        .section h2 {
            color: #2c3e50;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #3498db;
            font-size: 1.8em;
        }
        
        .section h3 {
            color: #34495e;
            margin: 25px 0 15px;
            font-size: 1.4em;
        }
        
        /* 总体评分样式 */
        .overall-score {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
        }
        
        .score-display {
            text-align: center;
        }
        
        .score-number {
            font-size: 3em;
            font-weight: bold;
            color: #3498db;
            line-height: 1;
        }
        
        .score-label {
            font-size: 1.1em;
            color: #7f8c8d;
            margin-top: 5px;
        }
        
        .score-details {
            flex: 1;
            margin-left: 30px;
        }
        
        .score-details p {
            margin-bottom: 10px;
            font-size: 1.1em;
        }
        
        /* 评分卡片样式 */
        .score-cards {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .score-card {
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .score-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        }
        
        .score-card h4 {
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 1.1em;
        }
        
        .score-card .score {
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 10px;
        }
        
        .score-card .score.good {
            color: #27ae60;
        }
        
        .score-card .score.medium {
            color: #f39c12;
        }
        
        .score-card .score.bad {
            color: #e74c3c;
        }
        
        /* 分析文本样式 */
        .analysis-text {
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        
        .analysis-text p {
            margin-bottom: 10px;
            line-height: 1.8;
        }
        
        /* 列表样式 */
        .list-section {
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        
        .list-section h4 {
            color: #2c3e50;
            margin-bottom: 15px;
            font-size: 1.2em;
        }
        
        ul.suggestions,
        ul.strengths,
        ul.weaknesses {
            list-style-type: none;
            padding-left: 0;
        }
        
        ul.suggestions li,
        ul.strengths li,
        ul.weaknesses li {
            position: relative;
            padding-left: 25px;
            margin-bottom: 10px;
            line-height: 1.6;
        }
        
        ul.suggestions li::before {
            content: "▶";
            position: absolute;
            left: 0;
            color: #3498db;
            font-size: 1.1em;
        }
        
        ul.strengths li::before {
            content: "✓";
            position: absolute;
            left: 0;
            color: #27ae60;
            font-size: 1.1em;
        }
        
        ul.weaknesses li::before {
            content: "!";
            position: absolute;
            left: 0;
            color: #e74c3c;
            font-size: 1.1em;
            font-weight: bold;
        }
        
        /* 表格样式 */
        .table-section {
            margin-top: 30px;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        
        th,
        td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        
        th {
            background-color: #f8f9fa;
            font-weight: 600;
            color: #2c3e50;
        }
        
        tr:hover {
            background-color: #f5f5f5;
        }
        
        /* 页面评分样式 */
        .page-scores {
            margin-top: 30px;
        }
        
        .page-card {
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            border-left: 4px solid #3498db;
        }
        
        .page-card h4 {
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 1.2em;
        }
        
        .page-card .page-overview {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .page-card .page-score {
            font-size: 1.5em;
            font-weight: bold;
            color: #3498db;
        }
        
        .page-card .page-details {
            margin-top: 15px;
        }
        
        .page-card .page-details h5 {
            color: #34495e;
            margin-bottom: 10px;
            font-size: 1.1em;
        }
        
        /* 响应式样式 */
        @media (max-width: 768px) {
            .content {
                padding: 20px;
            }
            
            .overall-score {
                flex-direction: column;
                text-align: center;
            }
            
            .score-details {
                margin-left: 0;
                margin-top: 20px;
            }
            
            .score-cards {
                grid-template-columns: 1fr;
            }
        }
        
        /* 打印样式 */
        @media print {
            body {
                background-color: white;
                padding: 0;
            }
            
            .container {
                box-shadow: none;
                max-width: 100%;
            }
            
            .header {
                background: none;
                color: black;
                border-bottom: 2px solid #3498db;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- 头部 -->
        <div class="header">
            <h1>SEO分析报告</h1>
            <p>{{ site_url }}</p>
            <div class="meta">
                <p>生成时间: {{ report_date }}</p>
                <p>分析页面数量: {{ total_pages }}</p>
            </div>
        </div>
        
        <!-- 主内容 -->
        <div class="content">
            <!-- 总体评分部分 -->
            <div class="section">
                <h2>总体评估</h2>
                <div class="overall-score">
                    <div class="score-display">
                        <div class="score-number">{{ "%.1f"|format(overall_score) }}</div>
                        <div class="score-label">综合得分</div>
                    </div>
                    <div class="score-details">
                        <p><strong>评估等级:</strong> {{ overall_rating }}</p>
                        <p>{{ overall_comment }}</p>
                    </div>
                </div>
                
                <h3>类别得分</h3>
                <div class="score-cards">
                    {% for category, score in category_scores.items() %}
                    <div class="score-card">
                        <h4>{{ get_category_name(category) }}</h4>
                        <div class="score {% if score >= 80 %}good{% elif score >= 60 %}medium{% else %}bad{% endif %}">
                            {{ "%.1f"|format(score) }}
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
            
            <!-- 网站分析部分 -->
            <div class="section">
                <h2>网站分析</h2>
                
                <div class="analysis-text">
                    <h3>总体评价</h3>
                    <p>您的网站在SEO方面{% if overall_score >= 80 %}表现良好{% elif overall_score >= 60 %}有一定基础但需要改进{% else %}存在较大问题{% endif %}。{% if overall_score >= 80 %}继续保持良好的SEO实践，定期更新内容并监控关键词排名。{% elif overall_score >= 60 %}重点关注得分较低的方面，特别是{% for weakness in weaknesses %}{{ weakness.split(' (')[0] }}{% if not loop.last %}和{% endif %}{% endfor %}方面的改进。{% else %}建议进行全面的SEO优化，从基础的技术SEO开始，逐步改进内容和关键词策略。{% endif %}</p>
                </div>
                
                {% if strengths %}
                <div class="list-section">
                    <h4>优势</h4>
                    <ul class="strengths">
                        {% for strength in strengths %}
                        <li>{{ strength }}</li>
                        {% endfor %}
                    </ul>
                </div>
                {% endif %}
                
                {% if weaknesses %}
                <div class="list-section">
                    <h4>劣势</h4>
                    <ul class="weaknesses">
                        {% for weakness in weaknesses %}
                        <li>{{ weakness }}</li>
                        {% endfor %}
                    </ul>
                </div>
                {% endif %}
            </div>
            
            <!-- 改进建议部分 -->
            <div class="section">
                <h2>改进建议</h2>
                <div class="list-section">
                    <ul class="suggestions">
                        {% for suggestion in overall_suggestions %}
                        <li>{{ suggestion }}</li>
                        {% endfor %}
                    </ul>
                </div>
            </div>
            
            <!-- 页面评分部分 -->
            {% if page_scores %}
            <div class="section">
                <h2>页面评分详情</h2>
                <div class="page-scores">
                    {% for url, page_data in page_scores.items() %}
                    <div class="page-card">
                        <h4>{{ url }}</h4>
                        <div class="page-overview">
                            <div>页面得分: <span class="page-score">{{ "%.1f"|format(page_data.overall_score) }}</span></div>
                        </div>
                        
                        <div class="page-details">
                            <h5>类别得分</h5>
                            <table>
                                <thead>
                                    <tr>
                                        <th>类别</th>
                                        <th>得分</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for category, score in page_data.scores.items() %}
                                    <tr>
                                        <td>{{ get_category_name(category) }}</td>
                                        <td>{{ "%.1f"|format(score) }}</td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                            
                            {% if page_data.improvement_suggestions %}
                            <h5>改进建议</h5>
                            <ul class="suggestions">
                                {% for suggestion in page_data.improvement_suggestions %}
                                <li>{{ suggestion }}</li>
                                {% endfor %}
                            </ul>
                            {% endif %}
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
            {% endif %}
            
            <!-- 页脚说明 -->
            <div class="section">
                <h2>报告说明</h2>
                <div class="analysis-text">
                    <p><strong>关于本报告：</strong>本报告由SEO自动化工具生成，提供网站SEO质量的客观评估。报告中的得分基于多种SEO因素的综合分析，但不保证与搜索引擎的实际排名直接相关。</p>
                    <p><strong>使用建议：</strong>将报告中的建议与您的业务目标结合考虑，优先实施影响最大的改进措施。定期重新生成报告以监控SEO优化的进展。</p>
                </div>
            </div>
        </div>
    </div>
</body>
</html>'''
            
            with open(html_template_path, 'w', encoding='utf-8') as f:
                f.write(html_template_content)
                logger.info(f"创建默认HTML模板: {html_template_path}")
    
    def _get_category_name(self, category: str) -> str:
        """获取类别的中文名称"""
        names = {
            'content': '内容质量',
            'keywords': '关键词优化',
            'meta_tags': '元标签',
            'performance': '性能',
            'technical': '技术SEO'
        }
        return names.get(category, category)
    
    def _prepare_report_data(self, seo_results: Dict, keyword_results: Dict = None) -> Dict:
        """准备报告数据"""
        # 提取必要的数据
        page_scores = seo_results.get('page_scores', {})
        overall_scores = seo_results.get('overall_scores', {})
        site_analysis = seo_results.get('site_analysis', {})
        overall_suggestions = seo_results.get('overall_suggestions', [])
        
        # 确定网站URL
        if page_scores:
            site_url = list(page_scores.keys())[0].split('/')[2]  # 从第一个URL中提取域名
        else:
            site_url = "未知网站"
        
        # 准备报告数据
        report_data = {
            'site_url': site_url,
            'report_date': datetime.now().strftime("%Y年%m月%d日 %H:%M:%S"),
            'total_pages': site_analysis.get('total_pages', 0),
            'overall_score': overall_scores.get('weighted_total', 0),
            'overall_rating': site_analysis.get('overall_rating', '未评估'),
            'overall_comment': site_analysis.get('overall_comment', ''),
            'category_scores': overall_scores,
            'strengths': site_analysis.get('strengths', []),
            'weaknesses': site_analysis.get('weaknesses', []),
            'overall_suggestions': overall_suggestions,
            'page_scores': page_scores
        }
        
        # 添加过滤器函数
        report_data['get_category_name'] = self._get_category_name
        
        return report_data
    
    def generate_html_report(self, seo_results: Dict, output_path: Optional[str] = None, 
                           keyword_results: Dict = None) -> str:
        """生成HTML格式的SEO报告"""
        try:
            # 准备报告数据
            report_data = self._prepare_report_data(seo_results, keyword_results)
            
            # 渲染HTML模板
            template = self.env.get_template('seo_report.html')
            html_content = template.render(**report_data)
            
            # 确定输出路径
            if not output_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"seo_report_{timestamp}.html"
                output_path = os.path.join(self.output_dir, output_filename)
            else:
                # 确保输出目录存在
                output_dir = os.path.dirname(output_path)
                if output_dir:
                    ensure_directory(output_dir)
            
            # 写入文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"HTML报告已生成: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"生成HTML报告失败: {str(e)}")
            raise
    
    def generate_pdf_report(self, seo_results: Dict, output_path: Optional[str] = None,
                          keyword_results: Dict = None) -> str:
        """生成PDF格式的SEO报告"""
        try:
            # 首先生成HTML报告
            html_path = self.generate_html_report(seo_results, None, keyword_results)
            
            # 确定PDF输出路径
            if not output_path:
                # 从HTML路径推断PDF路径
                pdf_filename = os.path.basename(html_path).replace('.html', '.pdf')
                output_path = os.path.join(self.output_dir, pdf_filename)
            else:
                # 确保输出目录存在
                output_dir = os.path.dirname(output_path)
                if output_dir:
                    ensure_directory(output_dir)
            
            # 使用WeasyPrint生成PDF
            try:
                from weasyprint import HTML
                
                # 生成PDF
                HTML(filename=html_path).write_pdf(output_path)
                logger.info(f"PDF报告已生成: {output_path}")
                return output_path
                
            except ImportError:
                logger.warning("WeasyPrint库未安装，尝试使用pdfkit")
                
                try:
                    import pdfkit
                    
                    # 使用pdfkit生成PDF
                    pdfkit.from_file(html_path, output_path)
                    logger.info(f"PDF报告已使用pdfkit生成: {output_path}")
                    return output_path
                    
                except ImportError:
                    logger.error("pdfkit库也未安装，无法生成PDF报告")
                    raise ImportError("请安装weasyprint或pdfkit库以生成PDF报告")
            
        except Exception as e:
            logger.error(f"生成PDF报告失败: {str(e)}")
            raise
    
    def generate_report(self, seo_results: Dict, output_path: Optional[str] = None,
                       format_type: str = 'html', keyword_results: Dict = None) -> str:
        """生成SEO报告
        
        Args:
            seo_results: SEO分析结果
            output_path: 输出文件路径，如果为None则使用默认路径
            format_type: 报告格式，'html'或'pdf'
            keyword_results: 关键词分析结果
            
        Returns:
            生成的报告文件路径
        """
        if format_type.lower() == 'pdf':
            return self.generate_pdf_report(seo_results, output_path, keyword_results)
        else:
            # 默认生成HTML报告
            return self.generate_html_report(seo_results, output_path, keyword_results)
    
    def save_results_to_json(self, seo_results: Dict, output_path: Optional[str] = None) -> str:
        """将SEO分析结果保存为JSON格式"""
        try:
            # 确定输出路径
            if not output_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"seo_results_{timestamp}.json"
                output_path = os.path.join(self.output_dir, output_filename)
            else:
                # 确保输出目录存在
                output_dir = os.path.dirname(output_path)
                if output_dir:
                    ensure_directory(output_dir)
            
            # 写入JSON文件
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(seo_results, f, ensure_ascii=False, indent=2)
            
            logger.info(f"分析结果已保存为JSON: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"保存JSON结果失败: {str(e)}")
            raise


def get_report_generator() -> ReportGenerator:
    """工厂函数，返回报告生成器实例"""
    return ReportGenerator()