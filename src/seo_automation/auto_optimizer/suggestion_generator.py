"""SEO优化建议生成器，根据分析结果生成优化建议"""

import logging
from typing import Dict, List, Any, Optional
import json
import os

from .config_manager import ConfigManager

logger = logging.getLogger(__name__)


class SuggestionGenerator:
    """SEO优化建议生成器"""
    
    def __init__(self, config_manager: ConfigManager):
        """
        初始化优化建议生成器
        
        Args:
            config_manager: 配置管理器实例
        """
        self.config_manager = config_manager
        # 获取配置项并添加防御性检查
        optimization_config = config_manager.get_config('optimization_config')
        logger.info(f"SuggestionGenerator: optimization_config类型: {type(optimization_config)}")
        
        # 防止ConfigManager实例被错误使用
        if isinstance(optimization_config, ConfigManager):
            logger.error("错误：optimization_config是ConfigManager实例，使用空字典")
            self.optimization_config = {}
        elif isinstance(optimization_config, dict):
            self.optimization_config = optimization_config
        else:
            self.optimization_config = {}
        
        custom_rules = config_manager.get_config('custom_rules')
        logger.info(f"SuggestionGenerator: custom_rules类型: {type(custom_rules)}")
        
        # 防止ConfigManager实例被错误使用
        if isinstance(custom_rules, ConfigManager):
            logger.error("错误：custom_rules是ConfigManager实例，使用空字典")
            self.custom_rules = {}
        elif isinstance(custom_rules, dict):
            self.custom_rules = custom_rules
        else:
            self.custom_rules = {}
        
        # 初始化建议结果
        self.suggestions = []
        self.priority_weights = {
            'critical': 3,
            'high': 2,
            'medium': 1,
            'low': 0
        }
    
    def generate_suggestions(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        根据分析结果生成优化建议
        
        Args:
            analysis_results: 分析结果
            
        Returns:
            List[Dict]: 优化建议列表
        """
        logger.info("开始生成SEO优化建议...")
        
        try:
            # 清空之前的建议
            self.suggestions = []
            
            # 分析页面内容
            if 'raw_pages_data' in analysis_results:
                self._generate_content_suggestions(analysis_results['raw_pages_data'])
            
            # 分析关键词
            if 'keyword_analysis_results' in analysis_results:
                self._generate_keyword_suggestions(analysis_results['keyword_analysis_results'])
            
            # 分析SEO评分
            if 'seo_scores' in analysis_results:
                self._generate_score_suggestions(analysis_results['seo_scores'])
            
            # 分析性能
            if 'performance_results' in analysis_results:
                self._generate_performance_suggestions(analysis_results['performance_results'])
            
            # 应用自定义规则
            self._apply_custom_rules(analysis_results)
            
            # 按优先级排序
            self.suggestions.sort(key=lambda x: (self.priority_weights.get(x.get('priority', 'low'), 0), 
                                               x.get('impact', 0)), reverse=True)
            
            # 添加详细的调试日志
            logger.critical("CRITICAL: 生成的优化建议详情:")
            for i, suggestion in enumerate(self.suggestions):
                logger.critical(f"CRITICAL: 建议{i+1}: {suggestion}")
                logger.critical(f"CRITICAL: auto_fixable: {suggestion.get('auto_fixable', 'NOT_SET')}")
            
            logger.info(f"成功生成 {len(self.suggestions)} 条优化建议")
            return self.suggestions
            
        except Exception as e:
            logger.error(f"生成优化建议时发生错误: {str(e)}")
            raise
    
    def _generate_content_suggestions(self, pages_data: Dict[str, Dict]):
        """根据页面内容生成建议"""
        for url, page_data in pages_data.items():
            # 检查标题
            if 'title' in page_data:
                title = page_data['title']
                if title == 'No Title':
                    self._add_suggestion(
                        page=url,
                        category='content',
                        issue='missing_title',
                        description='页面缺少标题',
                        recommendation='添加一个描述性的页面标题',
                        priority='high',
                        impact=8
                    )
                elif len(title) > 70:
                    self._add_suggestion(
                        page=url,
                        category='content',
                        issue='title_too_long',
                        description=f'页面标题过长 ({len(title)} 字符)',
                        recommendation='优化标题，使其长度不超过70个字符',
                        priority='medium',
                        impact=5
                    )
            
            # 检查元描述
            if 'meta_description' in page_data:
                meta_desc = page_data['meta_description']
                if not meta_desc:
                    self._add_suggestion(
                        page=url,
                        category='content',
                        issue='missing_meta_description',
                        description='页面缺少元描述',
                        recommendation='添加一个引人注目的元描述',
                        priority='high',
                        impact=7
                    )
                elif len(meta_desc) > 160:
                    self._add_suggestion(
                        page=url,
                        category='content',
                        issue='meta_description_too_long',
                        description=f'元描述过长 ({len(meta_desc)} 字符)',
                        recommendation='优化元描述，使其长度不超过160个字符',
                        priority='medium',
                        impact=4
                    )
            
            # 检查H1标签
            if 'headings' in page_data and 'h1' in page_data['headings']:
                h1_tags = page_data['headings']['h1']
                if not h1_tags:
                    self._add_suggestion(
                        page=url,
                        category='content',
                        issue='missing_h1',
                        description='页面缺少H1标签',
                        recommendation='添加一个主要标题(H1标签)',
                        priority='high',
                        impact=6
                    )
                elif len(h1_tags) > 1:
                    self._add_suggestion(
                        page=url,
                        category='content',
                        issue='multiple_h1',
                        description=f'页面有多个H1标签 ({len(h1_tags)})',
                        recommendation='确保每个页面只有一个H1标签',
                        priority='medium',
                        impact=5
                    )
            
            # 检查图片alt属性
            if 'images' in page_data:
                for img in page_data['images']:
                    if not img.get('alt', '').strip():
                        self._add_suggestion(
                            page=url,
                            category='content',
                            issue='missing_image_alt',
                            description=f'图片缺少alt属性: {img.get("src", "")}',
                            recommendation='为图片添加描述性的alt属性',
                            priority='medium',
                            impact=4
                        )
    
    def _generate_keyword_suggestions(self, keyword_results: Dict[str, Any]):
        """根据关键词分析生成建议"""
        # 检查关键词密度
        if 'keyword_density' in keyword_results:
            for keyword, density in keyword_results['keyword_density'].items():
                if density > 5.0:
                    self._add_suggestion(
                        category='keywords',
                        issue='keyword_stuffing',
                        description=f'关键词 "{keyword}" 密度过高 ({density:.2f}%)',
                        recommendation='降低关键词密度，避免关键词堆砌',
                        priority='high',
                        impact=7
                    )
                elif density < 0.5:
                    self._add_suggestion(
                        category='keywords',
                        issue='low_keyword_density',
                        description=f'关键词 "{keyword}" 密度过低 ({density:.2f}%)',
                        recommendation='适当增加关键词在内容中的使用',
                        priority='medium',
                        impact=4
                    )
        
        # 检查关键词位置
        if 'keyword_position' in keyword_results:
            for keyword, position in keyword_results['keyword_position'].items():
                if position > 100:
                    self._add_suggestion(
                        category='keywords',
                        issue='keyword_late_occurrence',
                        description=f'关键词 "{keyword}" 出现在内容较晚位置 ({position}字符)',
                        recommendation='将关键词移到内容的前100个字符中',
                        priority='medium',
                        impact=5
                    )
    
    def _generate_score_suggestions(self, seo_scores: Dict[str, Any]):
        """根据SEO评分生成建议"""
        # 检查总分
        if 'total_score' in seo_scores and seo_scores['total_score'] < 60:
            self._add_suggestion(
                category='seo_score',
                issue='low_overall_score',
                description=f'整体SEO评分较低: {seo_scores["total_score"]}/100',
                recommendation='全面改进网站SEO，优先解决高优先级问题',
                priority='critical',
                impact=10
            )
        
        # 检查各分项评分
        categories = {
            'content_score': '内容质量',
            'technical_score': '技术SEO',
            'mobile_score': '移动友好性',
            'user_experience_score': '用户体验'
        }
        
        for score_key, category_name in categories.items():
            if score_key in seo_scores and seo_scores[score_key] < 50:
                self._add_suggestion(
                    category=score_key.replace('_score', ''),
                    issue=f'low_{score_key}',
                    description=f'{category_name}评分较低: {seo_scores[score_key]}/100',
                    recommendation=f'重点改进{category_name}相关的SEO因素',
                    priority='high',
                    impact=8
                )
    
    def _generate_performance_suggestions(self, performance_results: Dict[str, Any]):
        """根据性能分析生成建议"""
        # 检查加载时间
        if 'load_time' in performance_results and performance_results['load_time'] > 3.0:
            self._add_suggestion(
                category='performance',
                issue='slow_page_load',
                description=f'页面加载时间过长: {performance_results["load_time"]:.2f}秒',
                recommendation='优化页面加载速度，包括压缩图片、减少HTTP请求等',
                priority='high',
                impact=8
            )
        
        # 检查页面大小
        if 'page_size' in performance_results and performance_results['page_size'] > 2000000:  # 2MB
            self._add_suggestion(
                category='performance',
                issue='large_page_size',
                description=f'页面大小过大: {performance_results["page_size"]/1024/1024:.2f}MB',
                recommendation='减小页面大小，压缩图片和资源文件',
                priority='medium',
                impact=6
            )
        
        # 检查移动端性能
        if 'mobile_performance' in performance_results and performance_results['mobile_performance'] < 50:
            self._add_suggestion(
                category='performance',
                issue='poor_mobile_performance',
                description=f'移动端性能较差: {performance_results["mobile_performance"]}/100',
                recommendation='优化移动端体验，确保响应式设计和快速加载',
                priority='high',
                impact=9
            )
    
    def _apply_custom_rules(self, analysis_results: Dict[str, Any]):
        """应用自定义规则生成建议"""
        if not self.custom_rules:
            return
        
        for rule_name, rule_config in self.custom_rules.items():
            try:
                # 这里可以根据不同的自定义规则类型实现相应的逻辑
                # 简单示例：如果规则指定了某个关键词必须出现在标题中
                if rule_config.get('type') == 'keyword_in_title':
                    keyword = rule_config.get('keyword', '')
                    for url, page_data in analysis_results.get('raw_pages_data', {}).items():
                        if 'title' in page_data and keyword.lower() not in page_data['title'].lower():
                            self._add_suggestion(
                                page=url,
                                category='custom',
                                issue=rule_name,
                                description=f'页面标题缺少指定关键词: {keyword}',
                                recommendation=f'在标题中包含关键词 "{keyword}"',
                                priority=rule_config.get('priority', 'medium'),
                                impact=rule_config.get('impact', 5)
                            )
            except Exception as e:
                logger.warning(f"应用自定义规则 {rule_name} 时出错: {str(e)}")
    
    def _add_suggestion(self, page: str = None, category: str = 'general', 
                       issue: str = 'unspecified', description: str = '',
                       recommendation: str = '', priority: str = 'medium',
                       impact: int = 5):
        """添加一条优化建议"""
        suggestion = {
            'id': f'{category}_{len(self.suggestions)}_{issue}',
            'page': page,
            'category': category,
            'issue': issue,
            'description': description,
            'recommendation': recommendation,
            'priority': priority,
            'impact': impact,
            'auto_fixable': self._is_auto_fixable(issue)
        }
        self.suggestions.append(suggestion)
    
    def _is_auto_fixable(self, issue: str) -> bool:
        """判断问题是否可以自动修复"""
        # 定义可以自动修复的问题类型
        auto_fixable_issues = [
            'missing_meta_description',
            'missing_image_alt',
            'title_too_long',
            'meta_description_too_long'
        ]
        return issue in auto_fixable_issues
    
    def export_suggestions(self, file_path: str = None, format: str = 'json') -> str:
        """
        导出优化建议
        
        Args:
            file_path: 导出文件路径
            format: 导出格式 (json, csv, txt)
            
        Returns:
            str: 导出的内容（如果未指定file_path）
        """
        if not file_path:
            # 获取输出目录配置
            output_dir = self.config_manager.get_config('output_dir') or '.'
            file_path = os.path.join(output_dir,
                                    'seo_suggestions.' + format)
        
        content = ''
        
        if format == 'json':
            content = json.dumps(self.suggestions, indent=2, ensure_ascii=False)
        elif format == 'csv':
            # 简单的CSV导出
            import csv
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                if self.suggestions:
                    fieldnames = self.suggestions[0].keys()
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(self.suggestions)
                return file_path
        elif format == 'txt':
            # 简单的文本导出
            for i, suggestion in enumerate(self.suggestions, 1):
                content += f"建议 {i}:\n"
                content += f"类别: {suggestion['category']}\n"
                content += f"问题: {suggestion['issue']}\n"
                if suggestion['page']:
                    content += f"页面: {suggestion['page']}\n"
                content += f"描述: {suggestion['description']}\n"
                content += f"建议: {suggestion['recommendation']}\n"
                content += f"优先级: {suggestion['priority']}\n"
                content += f"影响度: {suggestion['impact']}/10\n"
                content += f"可自动修复: {'是' if suggestion['auto_fixable'] else '否'}\n"
                content += "-" * 50 + "\n\n"
        
        # 写入文件
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"优化建议已导出到: {file_path}")
        return file_path