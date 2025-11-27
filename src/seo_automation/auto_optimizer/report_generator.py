"""报告生成器，负责生成SEO优化过程和结果的详细报告"""

import os
import json
import datetime
import markdown
from typing import Dict, Any, List, Optional
from jinja2 import Template


class ReportGenerator:
    """
    报告生成器类，提供多种格式的报告生成功能
    支持HTML、Markdown、JSON等格式
    """
    
    # 报告模板
    HTML_TEMPLATE = '''
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{{ title }}</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Microsoft YaHei', sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .header {
                background: linear-gradient(135deg, #2c3e50, #3498db);
                color: white;
                padding: 30px;
                border-radius: 8px;
                margin-bottom: 30px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            .header h1 {
                margin: 0;
                font-size: 2.5em;
            }
            .header .subtitle {
                font-size: 1.2em;
                opacity: 0.9;
                margin-top: 10px;
            }
            .section {
                background: white;
                padding: 30px;
                margin-bottom: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .section h2 {
                color: #2c3e50;
                border-bottom: 2px solid #3498db;
                padding-bottom: 10px;
                margin-top: 0;
            }
            .score-overview {
                display: flex;
                justify-content: space-around;
                margin: 20px 0;
            }
            .score-card {
                text-align: center;
                padding: 20px;
                border-radius: 8px;
                flex: 1;
                margin: 0 10px;
            }
            .overall-score {
                background-color: #e8f4fd;
                border: 2px solid #3498db;
            }
            .before-score {
                background-color: #f9e8e8;
                border: 2px solid #e74c3c;
            }
            .after-score {
                background-color: #e8f9e8;
                border: 2px solid #2ecc71;
            }
            .score-value {
                font-size: 3em;
                font-weight: bold;
                margin: 10px 0;
            }
            .score-label {
                font-size: 1.2em;
                opacity: 0.8;
            }
            .table-container {
                overflow-x: auto;
                margin: 20px 0;
            }
            table {
                width: 100%;
                border-collapse: collapse;
            }
            th, td {
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }
            th {
                background-color: #f2f2f2;
                font-weight: bold;
            }
            tr:hover {
                background-color: #f5f5f5;
            }
            .success {
                color: #2ecc71;
                font-weight: bold;
            }
            .warning {
                color: #f39c12;
                font-weight: bold;
            }
            .error {
                color: #e74c3c;
                font-weight: bold;
            }
            .info {
                color: #3498db;
                font-weight: bold;
            }
            .change-list {
                list-style: none;
                padding: 0;
            }
            .change-list li {
                padding: 10px 0;
                border-bottom: 1px solid #eee;
                display: flex;
                align-items: flex-start;
            }
            .change-list .icon {
                margin-right: 10px;
                font-size: 1.2em;
            }
            .footer {
                text-align: center;
                margin-top: 40px;
                color: #777;
                font-size: 0.9em;
            }
            .metrics {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin: 20px 0;
            }
            .metric-card {
                background-color: #f9f9f9;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
                border: 1px solid #ddd;
            }
            .metric-value {
                font-size: 2em;
                font-weight: bold;
                margin: 10px 0;
            }
            .metric-label {
                font-size: 1em;
                opacity: 0.8;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>{{ title }}</h1>
            <div class="subtitle">
                生成时间: {{ generated_at }} | 网站: {{ website_url }} | 报告ID: {{ report_id }}
            </div>
        </div>
        
        <div class="section">
            <h2>执行摘要</h2>
            <p>{{ summary }}</p>
            
            <div class="metrics">
                <div class="metric-card">
                    <div class="metric-label">操作类型</div>
                    <div class="metric-value">{{ operation_type }}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">处理页面数</div>
                    <div class="metric-value">{{ processed_pages }}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">修改文件数</div>
                    <div class="metric-value">{{ modified_files }}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">发现问题数</div>
                    <div class="metric-value">{{ issues_found }}</div>
                </div>
            </div>
        </div>
        
        {% if has_score_data %}
        <div class="section">
            <h2>SEO评分对比</h2>
            <div class="score-overview">
                <div class="score-card before-score">
                    <div class="score-label">优化前评分</div>
                    <div class="score-value">{{ before_score }}</div>
                    <div class="score-label">/ 100</div>
                </div>
                <div class="score-card after-score">
                    <div class="score-label">优化后评分</div>
                    <div class="score-value">{{ after_score }}</div>
                    <div class="score-label">/ 100</div>
                </div>
                <div class="score-card overall-score">
                    <div class="score-label">提升幅度</div>
                    <div class="score-value">{{ score_improvement }}</div>
                    <div class="score-label">分</div>
                </div>
            </div>
        </div>
        {% endif %}
        
        <div class="section">
            <h2>问题分析</h2>
            {% if issues %}
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>问题类型</th>
                            <th>严重程度</th>
                            <th>页面</th>
                            <th>问题描述</th>
                            <th>修复状态</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for issue in issues %}
                        <tr>
                            <td>{{ issue.type }}</td>
                            <td class="{{ issue.severity }}">{{ issue.severity }}</td>
                            <td>{{ issue.page }}</td>
                            <td>{{ issue.description }}</td>
                            <td class="{{ issue.status }}">{{ issue.status }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            {% else %}
            <p>没有发现问题。</p>
            {% endif %}
        </div>
        
        <div class="section">
            <h2>优化操作</h2>
            {% if changes %}
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>文件</th>
                            <th>操作类型</th>
                            <th>优化项</th>
                            <th>操作前</th>
                            <th>操作后</th>
                            <th>状态</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for change in changes %}
                        <tr>
                            <td>{{ change.file }}</td>
                            <td>{{ change.operation_type }}</td>
                            <td>{{ change.optimization_item }}</td>
                            <td>{{ change.before | default('-') }}</td>
                            <td>{{ change.after | default('-') }}</td>
                            <td class="{{ change.status }}">{{ change.status }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            {% else %}
            <p>没有执行优化操作。</p>
            {% endif %}
        </div>
        
        {% if recommendations %}
        <div class="section">
            <h2>优化建议</h2>
            <ul class="change-list">
                {% for rec in recommendations %}
                <li>
                    <span class="icon {{ rec.priority }}">{{ rec.priority_symbol }}</span>
                    <div>
                        <strong>{{ rec.title }} (优先级: {{ rec.priority }})</strong>
                        <p>{{ rec.description }}</p>
                        <p><em>预期效果: {{ rec.expected_impact }}</em></p>
                    </div>
                </li>
                {% endfor %}
            </ul>
        </div>
        {% endif %}
        
        {% if performance_data %}
        <div class="section">
            <h2>性能分析</h2>
            <div class="metrics">
                {% for metric, value in performance_data.items() %}
                <div class="metric-card">
                    <div class="metric-label">{{ metric }}</div>
                    <div class="metric-value">{{ value }}</div>
                </div>
                {% endfor %}
            </div>
        </div>
        {% endif %}
        
        <div class="footer">
            <p>此报告由 SEO 自动优化工具生成 | 版本: {{ tool_version }}</p>
        </div>
    </body>
    </html>
    '''
    
    MARKDOWN_TEMPLATE = '''
# {{ title }}

## 基本信息
- 生成时间: {{ generated_at }}
- 网站: {{ website_url }}
- 报告ID: {{ report_id }}
- 操作类型: {{ operation_type }}
- 处理页面数: {{ processed_pages }}
- 修改文件数: {{ modified_files }}
- 发现问题数: {{ issues_found }}

## 执行摘要
{{ summary }}

{% if has_score_data %}
## SEO评分对比
- **优化前评分**: {{ before_score }}/100
- **优化后评分**: {{ after_score }}/100
- **提升幅度**: {{ score_improvement }}分
{% endif %}

## 问题分析
{% if issues %}
| 问题类型 | 严重程度 | 页面 | 问题描述 | 修复状态 |
|---------|---------|------|---------|----------|
{% for issue in issues %}
| {{ issue.type }} | {{ issue.severity }} | {{ issue.page }} | {{ issue.description }} | {{ issue.status }} |
{% endfor %}
{% else %}
没有发现问题。
{% endif %}

## 优化操作
{% if changes %}
| 文件 | 操作类型 | 优化项 | 操作前 | 操作后 | 状态 |
|------|---------|-------|--------|--------|------|
{% for change in changes %}
| {{ change.file }} | {{ change.operation_type }} | {{ change.optimization_item }} | {{ change.before | default('-') }} | {{ change.after | default('-') }} | {{ change.status }} |
{% endfor %}
{% else %}
没有执行优化操作。
{% endif %}

{% if recommendations %}
## 优化建议
{% for rec in recommendations %}
### {{ rec.priority_symbol }} {{ rec.title }} (优先级: {{ rec.priority }})
{{ rec.description }}

预期效果: {{ rec.expected_impact }}
{% endfor %}
{% endif %}

{% if performance_data %}
## 性能分析
{% for metric, value in performance_data.items() %}
- **{{ metric }}**: {{ value }}
{% endfor %}
{% endif %}

---
*此报告由 SEO 自动优化工具生成 | 版本: {{ tool_version }}*'''
    
    def __init__(self, report_dir: Optional[str] = None, tool_version: str = '1.0.0'):
        """
        初始化报告生成器
        
        Args:
            report_dir: 报告保存目录，如果为None则使用默认目录
            tool_version: 工具版本号
        """
        self.report_dir = self._get_report_directory(report_dir)
        self.tool_version = tool_version
        
        # 确保报告目录存在
        os.makedirs(self.report_dir, exist_ok=True)
    
    def _get_report_directory(self, report_dir: Optional[str]) -> str:
        """
        获取报告保存目录
        
        Args:
            report_dir: 指定的报告目录
            
        Returns:
            str: 报告保存目录路径
        """
        if report_dir:
            return report_dir
        
        # 默认报告目录 - 与optimizer.py中保持一致，使用'./seo_reports'
        return './seo_reports'
    
    def _generate_report_id(self) -> str:
        """
        生成报告ID
        
        Returns:
            str: 唯一的报告ID
        """
        now = datetime.datetime.now()
        return now.strftime('%Y%m%d_%H%M%S_%f')[:-3]
    
    def _get_template_context(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        准备模板渲染所需的上下文数据
        
        Args:
            data: 原始报告数据
            
        Returns:
            Dict: 模板上下文数据
        """
        # 基本信息
        context = {
            'title': data.get('title', 'SEO优化报告'),
            'generated_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'website_url': data.get('website_url', 'Unknown'),
            'report_id': self._generate_report_id(),
            'operation_type': data.get('operation_type', 'Unknown'),
            'processed_pages': len(data.get('pages', [])),
            'modified_files': len(data.get('changes', [])),
            'issues_found': len(data.get('issues', [])),
            'summary': data.get('summary', 'No summary provided.'),
            'tool_version': self.tool_version,
        }
        
        # 评分数据
        before_score = data.get('before_score', 0)
        after_score = data.get('after_score', 0)
        context.update({
            'has_score_data': before_score > 0 or after_score > 0,
            'before_score': before_score,
            'after_score': after_score,
            'score_improvement': after_score - before_score
        })
        
        # 问题数据
        context['issues'] = data.get('issues', [])
        
        # 变更数据
        context['changes'] = data.get('changes', [])
        
        # 建议数据
        recommendations = data.get('recommendations', [])
        # 添加优先级符号
        for rec in recommendations:
            priority_map = {
                'high': '⚠️',
                'medium': '❗',
                'low': 'ℹ️'
            }
            rec['priority_symbol'] = priority_map.get(rec.get('priority', 'medium'), '❗')
        context['recommendations'] = recommendations
        
        # 性能数据
        context['performance_data'] = data.get('performance_data', {})
        
        return context
    
    def generate_html_report(self, data: Dict[str, Any], output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        生成HTML格式的报告
        
        Args:
            data: 报告数据
            output_path: 输出文件路径，如果为None则自动生成
            
        Returns:
            Dict: 包含报告路径和其他信息的字典
        """
        try:
            # 准备上下文数据
            context = self._get_template_context(data)
            
            # 使用Jinja2模板渲染HTML
            template = Template(self.HTML_TEMPLATE)
            html_content = template.render(**context)
            
            # 确定输出路径
            if output_path is None:
                output_path = os.path.join(
                    self.report_dir,
                    f"seo_report_{context['report_id']}.html"
                )
            
            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            
            # 写入文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return {
                'status': 'success',
                'report_id': context['report_id'],
                'format': 'html',
                'path': output_path,
                'generated_at': context['generated_at']
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def generate_markdown_report(self, data: Dict[str, Any], output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        生成Markdown格式的报告
        
        Args:
            data: 报告数据
            output_path: 输出文件路径，如果为None则自动生成
            
        Returns:
            Dict: 包含报告路径和其他信息的字典
        """
        try:
            # 准备上下文数据
            context = self._get_template_context(data)
            
            # 使用Jinja2模板渲染Markdown
            template = Template(self.MARKDOWN_TEMPLATE)
            md_content = template.render(**context)
            
            # 确定输出路径
            if output_path is None:
                output_path = os.path.join(
                    self.report_dir,
                    f"seo_report_{context['report_id']}.md"
                )
            
            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            
            # 写入文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            
            return {
                'status': 'success',
                'report_id': context['report_id'],
                'format': 'markdown',
                'path': output_path,
                'generated_at': context['generated_at']
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def generate_json_report(self, data: Dict[str, Any], output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        生成JSON格式的报告
        
        Args:
            data: 报告数据
            output_path: 输出文件路径，如果为None则自动生成
            
        Returns:
            Dict: 包含报告路径和其他信息的字典
        """
        try:
            # 准备上下文数据
            context = self._get_template_context(data)
            
            # 构建JSON报告数据
            json_data = {
                'report_id': context['report_id'],
                'title': context['title'],
                'generated_at': context['generated_at'],
                'website_url': context['website_url'],
                'operation_type': context['operation_type'],
                'processed_pages': context['processed_pages'],
                'modified_files': context['modified_files'],
                'issues_found': context['issues_found'],
                'summary': context['summary'],
                'tool_version': context['tool_version'],
                'score_data': {
                    'before_score': context['before_score'],
                    'after_score': context['after_score'],
                    'improvement': context['score_improvement']
                } if context['has_score_data'] else None,
                'issues': context['issues'],
                'changes': context['changes'],
                'recommendations': context['recommendations'],
                'performance_data': context['performance_data']
            }
            
            # 确定输出路径
            if output_path is None:
                output_path = os.path.join(
                    self.report_dir,
                    f"seo_report_{context['report_id']}.json"
                )
            
            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            
            # 写入文件
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            
            return {
                'status': 'success',
                'report_id': context['report_id'],
                'format': 'json',
                'path': output_path,
                'generated_at': context['generated_at']
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def generate_report(self, data: Dict[str, Any], formats: List[str] = None, output_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        生成多种格式的报告
        
        Args:
            data: 报告数据
            formats: 要生成的报告格式列表，可选值: ['html', 'markdown', 'json']
            output_dir: 输出目录，如果为None则使用默认目录
            
        Returns:
            Dict: 包含所有生成的报告信息的字典
        """
        # 默认生成所有格式
        if formats is None:
            formats = ['html', 'markdown', 'json']
        
        # 确保格式列表有效
        valid_formats = [f for f in formats if f in ['html', 'markdown', 'json']]
        
        # 准备输出目录
        if output_dir is None:
            output_dir = self.report_dir
        
        # 生成报告
        results = {
            'status': 'success',
            'reports': []
        }
        
        for format_type in valid_formats:
            # 生成带格式后缀的文件名
            report_id = self._generate_report_id()
            output_path = os.path.join(output_dir, f"seo_report_{report_id}.{format_type}")
            
            # 根据格式调用相应的生成方法
            if format_type == 'html':
                result = self.generate_html_report(data, output_path)
            elif format_type == 'markdown':
                result = self.generate_markdown_report(data, output_path)
            elif format_type == 'json':
                result = self.generate_json_report(data, output_path)
            
            # 更新结果
            if result['status'] == 'success':
                results['reports'].append(result)
            else:
                results['status'] = 'partial'
                if 'errors' not in results:
                    results['errors'] = []
                results['errors'].append({
                    'format': format_type,
                    'error': result.get('error', 'Unknown error')
                })
        
        return results
    
    def generate_summary_report(self, data: Dict[str, Any]) -> str:
        """
        生成简短的文本摘要报告
        
        Args:
            data: 报告数据
            
        Returns:
            str: 摘要报告文本
        """
        # 准备上下文数据
        context = self._get_template_context(data)
        
        # 构建摘要文本
        summary_lines = [
            f"SEO优化报告摘要",
            f"- 网站: {context['website_url']}",
            f"- 生成时间: {context['generated_at']}",
            f"- 操作类型: {context['operation_type']}",
            f"- 处理页面数: {context['processed_pages']}",
        ]
        
        # 添加评分信息
        if context['has_score_data']:
            summary_lines.extend([
                f"- 优化前评分: {context['before_score']}/100",
                f"- 优化后评分: {context['after_score']}/100",
                f"- 提升幅度: {context['score_improvement']}分"
            ])
        
        # 添加问题和修改信息
        summary_lines.extend([
            f"- 发现问题数: {context['issues_found']}",
            f"- 修改文件数: {context['modified_files']}"
        ])
        
        # 添加执行摘要
        summary_lines.extend([
            "",
            "执行摘要:",
            context['summary']
        ])
        
        # 转换为文本
        return '\n'.join(summary_lines)
    
    def get_report_list(self) -> List[Dict[str, Any]]:
        """
        获取报告列表
        
        Returns:
            List[Dict]: 报告文件列表，包含文件名、大小、创建时间等信息
        """
        reports = []
        
        try:
            for filename in os.listdir(self.report_dir):
                file_path = os.path.join(self.report_dir, filename)
                
                # 只处理报告文件
                if os.path.isfile(file_path) and filename.startswith('seo_report_'):
                    # 获取文件信息
                    file_stats = os.stat(file_path)
                    
                    reports.append({
                        'filename': filename,
                        'path': file_path,
                        'size': file_stats.st_size,
                        'created_at': datetime.datetime.fromtimestamp(file_stats.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
                        'modified_at': datetime.datetime.fromtimestamp(file_stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                    })
            
            # 按修改时间排序，最新的在前
            reports.sort(key=lambda x: x['modified_at'], reverse=True)
            
        except Exception as e:
            # 处理异常
            print(f"获取报告列表失败: {str(e)}")
        
        return reports
    
    def delete_report(self, report_id: str) -> bool:
        """
        删除指定的报告文件
        
        Args:
            report_id: 报告ID
            
        Returns:
            bool: 是否删除成功
        """
        try:
            # 查找并删除所有与该ID相关的报告文件
            deleted = False
            for filename in os.listdir(self.report_dir):
                if filename.startswith(f'seo_report_{report_id}.'):
                    file_path = os.path.join(self.report_dir, filename)
                    os.remove(file_path)
                    deleted = True
            
            return deleted
            
        except Exception as e:
            print(f"删除报告失败: {str(e)}")
            return False
    
    def archive_old_reports(self, days: int = 30) -> Dict[str, Any]:
        """
        归档旧报告
        
        Args:
            days: 归档多少天前的报告，默认30天
            
        Returns:
            Dict: 归档结果
        """
        try:
            # 确保归档目录存在
            archive_dir = os.path.join(self.report_dir, 'archive')
            os.makedirs(archive_dir, exist_ok=True)
            
            # 获取时间范围
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)
            
            # 查找并归档旧报告
            archived_files = []
            for filename in os.listdir(self.report_dir):
                file_path = os.path.join(self.report_dir, filename)
                
                # 只处理报告文件
                if os.path.isfile(file_path) and filename.startswith('seo_report_'):
                    file_modified = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    # 只归档指定天数前的报告
                    if file_modified < cutoff_date:
                        # 创建归档文件名（添加日期前缀）
                        date_prefix = file_modified.strftime('%Y%m%d')
                        archive_filename = f"{date_prefix}_{filename}"
                        archive_path = os.path.join(archive_dir, archive_filename)
                        
                        # 移动文件到归档目录
                        shutil.move(file_path, archive_path)
                        archived_files.append(archive_filename)
            
            return {
                'status': 'success',
                'archived_count': len(archived_files),
                'archived_files': archived_files
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }


# 为了支持shutil移动文件
import shutil