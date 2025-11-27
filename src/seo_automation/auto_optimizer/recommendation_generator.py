"""优化建议生成器，根据SEO分析结果提供具体可行的优化建议"""

import logging
from typing import Dict, List, Any, Tuple

from .config_manager import ConfigManager

logger = logging.getLogger(__name__)


class RecommendationGenerator:
    """优化建议生成器，根据SEO分析结果生成具体可行的优化建议"""
    
    def __init__(self, config_manager: ConfigManager):
        """
        初始化优化建议生成器
        
        Args:
            config_manager: 配置管理器实例
        """
        self.config_manager = config_manager
        self.optimization_rules = self._load_optimization_rules()
        
    def _load_optimization_rules(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        加载优化规则配置
        
        Returns:
            Dict: 优化规则字典
        """
        # 从配置中加载优化规则
        # 获取优化配置规则
        try:
            config_rules = self.config_manager.get_config('optimization_config.rules')
            
            # 添加防御性检查，确保不会将ConfigManager对象错误地用作配置值
            if config_rules is None or isinstance(config_rules, type(self.config_manager)):
                logger.warning("获取优化规则配置失败或配置类型错误，使用默认规则")
                config_rules = {}
            elif not isinstance(config_rules, dict):
                logger.warning(f"优化规则配置类型错误，期望dict但得到{type(config_rules).__name__}，使用默认规则")
                config_rules = {}
        except Exception as e:
            logger.error(f"获取优化规则配置时出错: {str(e)}")
            config_rules = {}
        
        # 默认规则，确保基本功能
        default_rules = {
            'content_quality': [
                {
                    'condition': lambda score: score < 20,
                    'recommendation': "提升内容质量，增加文字内容数量至至少300字以上",
                    'severity': 'high'
                },
                {
                    'condition': lambda score: score < 40,
                    'recommendation': "内容略显不足，建议添加更多有价值的信息",
                    'severity': 'medium'
                }
            ],
            'keyword_density': [
                {
                    'condition': lambda density: density < 0.5,
                    'recommendation': "关键词密度过低，考虑在适当位置增加关键词",
                    'severity': 'medium'
                },
                {
                    'condition': lambda density: density > 5,
                    'recommendation': "关键词密度过高，可能被搜索引擎视为关键词堆砌",
                    'severity': 'high'
                }
            ],
            'meta_tags': [
                {
                    'condition': lambda has_tags: not has_tags,
                    'recommendation': "缺少元描述标签，添加描述性的meta description标签",
                    'severity': 'high'
                },
                {
                    'condition': lambda length: length < 50 or length > 160,
                    'recommendation': "元描述长度不合适，建议控制在50-160个字符之间",
                    'severity': 'medium'
                }
            ],
            'headings': [
                {
                    'condition': lambda has_h1: not has_h1,
                    'recommendation': "页面缺少H1标签，确保每个页面有且仅有一个H1标签",
                    'severity': 'high'
                },
                {
                    'condition': lambda structure: structure == 'flat',
                    'recommendation': "标题结构扁平，建议使用H2、H3等多层级标题完善内容结构",
                    'severity': 'medium'
                }
            ],
            'images': [
                {
                    'condition': lambda missing_alt: missing_alt > 0,
                    'recommendation': "图片缺少alt属性，为所有图片添加描述性alt标签",
                    'severity': 'medium'
                },
                {
                    'condition': lambda size: size > 200 * 1024,  # 200KB
                    'recommendation': "图片文件过大，建议压缩图片并优化尺寸",
                    'severity': 'medium'
                }
            ],
            'performance': [
                {
                    'condition': lambda score: score < 50,
                    'recommendation': "网站性能较差，优化资源大小并减少HTTP请求",
                    'severity': 'high'
                },
                {
                    'condition': lambda score: score < 70,
                    'recommendation': "网站性能有待提升，考虑优化JS和CSS文件",
                    'severity': 'medium'
                }
            ],
            'internal_links': [
                {
                    'condition': lambda count: count < 5,
                    'recommendation': "内部链接过少，建议增加相关页面的内部链接",
                    'severity': 'low'
                }
            ],
            'external_links': [
                {
                    'condition': lambda count: count == 0,
                    'recommendation': "没有外部链接，考虑添加一些高质量的外部参考链接",
                    'severity': 'low'
                }
            ],
            'title_tags': [
                {
                    'condition': lambda has_title: not has_title,
                    'recommendation': "页面缺少标题标签，确保每个页面都有明确的title标签",
                    'severity': 'high'
                },
                {
                    'condition': lambda length: length < 10 or length > 60,
                    'recommendation': "标题标签长度不合适，建议控制在10-60个字符之间",
                    'severity': 'medium'
                }
            ]
        }
        
        # 合并配置规则和默认规则
        rules = default_rules.copy()
        rules.update(config_rules)
        
        return rules
    
    def generate_recommendations(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据分析结果生成优化建议
        
        Args:
            analysis_results: SEO分析结果
            
        Returns:
            Dict: 优化建议
        """
        logger.info("开始生成优化建议...")
        
        try:
            # 按页面生成建议
            page_recommendations = self._generate_page_recommendations(analysis_results)
            
            # 生成整体建议
            overall_recommendations = self._generate_overall_recommendations(analysis_results)
            
            # 对建议进行排序和分类
            prioritized_recommendations = self._prioritize_recommendations(
                overall_recommendations, page_recommendations
            )
            
            logger.info(f"成功生成优化建议: {len(prioritized_recommendations)} 项")
            
            return {
                'overall_recommendations': overall_recommendations,
                'page_recommendations': page_recommendations,
                'prioritized_recommendations': prioritized_recommendations,
                'optimization_plan': self._create_optimization_plan(prioritized_recommendations)
            }
            
        except Exception as e:
            logger.error(f"生成优化建议时发生错误: {str(e)}")
            raise
    
    def _generate_page_recommendations(self, analysis_results: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """
        为每个页面生成优化建议
        
        Args:
            analysis_results: SEO分析结果
            
        Returns:
            Dict: 页面优化建议字典
        """
        page_recommendations = {}
        raw_pages_data = analysis_results.get('raw_pages_data', {})
        page_scores = analysis_results.get('seo_scores', {}).get('page_scores', {})
        keyword_analyses = analysis_results.get('keyword_analysis', {}).get('page_analyses', {})
        
        for path, page_data in raw_pages_data.items():
            recommendations = []
            
            # 获取该页面的评分数据
            score_data = page_scores.get(path, {})
            keyword_analysis = keyword_analyses.get(path, {})
            
            # 跳过错误页面
            if 'error' in page_data:
                recommendations.append({
                    'category': 'error',
                    'description': f"页面访问错误: {page_data['error']}",
                    'severity': 'high',
                    'autofixable': False,
                    'priority': 1
                })
                continue
            
            # 标题标签检查
            self._check_title_tag(page_data, recommendations)
            
            # 元标签检查
            self._check_meta_tags(page_data, recommendations)
            
            # 内容质量检查
            content_score = score_data.get('content_quality', 0)
            for rule in self.optimization_rules.get('content_quality', []):
                if rule['condition'](content_score):
                    recommendations.append({
                        'category': 'content_quality',
                        'description': rule['recommendation'],
                        'severity': rule['severity'],
                        'autofixable': False,
                        'priority': self._get_priority(rule['severity'])
                    })
            
            # 关键词分析
            if 'keyword_density' in keyword_analysis:
                self._check_keyword_density(keyword_analysis['keyword_density'], recommendations)
            
            # 标题结构检查
            self._check_heading_structure(page_data.get('headings', {}), recommendations)
            
            # 图片检查
            self._check_images(page_data.get('images', []), recommendations)
            
            # 链接检查
            self._check_links(page_data.get('links', []), recommendations)
            
            if recommendations:
                page_recommendations[path] = recommendations
        
        return page_recommendations
    
    def _generate_overall_recommendations(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        生成整体网站优化建议
        
        Args:
            analysis_results: SEO分析结果
            
        Returns:
            List: 整体优化建议
        """
        overall_recommendations = []
        summary = analysis_results.get('summary', {})
        performance_data = analysis_results.get('performance_analysis', {})
        
        # 整体SEO评分检查
        overall_score = summary.get('overall_seo_score', 0)
        if overall_score < 40:
            overall_recommendations.append({
                'category': 'overall_seo',
                'description': f"网站整体SEO评分较低({overall_score}/100)，需要全面优化",
                'severity': 'high',
                'autofixable': False,
                'priority': 1
            })
        elif overall_score < 70:
            overall_recommendations.append({
                'category': 'overall_seo',
                'description': f"网站整体SEO评分一般({overall_score}/100)，有优化空间",
                'severity': 'medium',
                'autofixable': False,
                'priority': 3
            })
        
        # 性能评分检查
        performance_score = summary.get('performance_score', 0)
        for rule in self.optimization_rules.get('performance', []):
            if rule['condition'](performance_score):
                overall_recommendations.append({
                    'category': 'performance',
                    'description': rule['recommendation'],
                    'severity': rule['severity'],
                    'autofixable': False,
                    'priority': self._get_priority(rule['severity'])
                })
        
        # 资源大小检查
        total_size_mb = summary.get('total_size_mb', 0)
        if total_size_mb > 50:
            overall_recommendations.append({
                'category': 'performance',
                'description': f"网站总大小过大({total_size_mb:.2f}MB)，建议全面压缩和优化资源",
                'severity': 'high',
                'autofixable': False,
                'priority': 1
            })
        elif total_size_mb > 20:
            overall_recommendations.append({
                'category': 'performance',
                'description': f"网站总大小较大({total_size_mb:.2f}MB)，可以考虑进一步优化",
                'severity': 'medium',
                'autofixable': False,
                'priority': 3
            })
        
        # 页面数量检查
        page_count = summary.get('total_pages', 0)
        if page_count == 0:
            overall_recommendations.append({
                'category': 'content',
                'description': "未发现HTML页面，检查网站路径或文件结构是否正确",
                'severity': 'high',
                'autofixable': False,
                'priority': 1
            })
        elif page_count < 5:
            overall_recommendations.append({
                'category': 'content',
                'description': "网站页面数量较少，考虑增加更多相关内容页面",
                'severity': 'medium',
                'autofixable': False,
                'priority': 4
            })
        
        # 图片数量检查
        image_count = performance_data.get('resource_counts', {}).get('images', 0)
        if image_count > 200:
            overall_recommendations.append({
                'category': 'images',
                'description': f"图片数量过多({image_count}个)，考虑使用CSS Sprite或延迟加载",
                'severity': 'medium',
                'autofixable': False,
                'priority': 3
            })
        
        # 合并性能分析的建议
        performance_suggestions = performance_data.get('optimization_suggestions', [])
        for suggestion in performance_suggestions:
            overall_recommendations.append({
                'category': 'performance',
                'description': suggestion,
                'severity': 'medium',
                'autofixable': False,
                'priority': 3
            })
        
        # 合并SEO分析的建议
        seo_suggestions = analysis_results.get('seo_scores', {}).get('overall_suggestions', [])
        for suggestion in seo_suggestions:
            overall_recommendations.append({
                'category': 'seo',
                'description': suggestion,
                'severity': 'medium',
                'autofixable': False,
                'priority': 2
            })
        
        return overall_recommendations
    
    def _prioritize_recommendations(self, 
                                  overall_recommendations: List[Dict[str, Any]],
                                  page_recommendations: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        对优化建议进行排序和优先级排序
        
        Args:
            overall_recommendations: 整体优化建议
            page_recommendations: 页面优化建议
            
        Returns:
            List: 排序后的优化建议列表
        """
        all_recommendations = []
        
        # 添加整体建议
        for rec in overall_recommendations:
            rec['scope'] = 'overall'
            all_recommendations.append(rec)
        
        # 添加页面建议
        for path, recs in page_recommendations.items():
            for rec in recs:
                rec['scope'] = 'page'
                rec['page_path'] = path
                all_recommendations.append(rec)
        
        # 按优先级排序
        all_recommendations.sort(key=lambda x: (x['priority'], x['severity']))
        
        # 限制返回数量，避免过多建议
        return all_recommendations[:50]  # 返回前50个建议
    
    def _create_optimization_plan(self, recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        创建优化计划
        
        Args:
            recommendations: 排序后的优化建议
            
        Returns:
            Dict: 优化计划
        """
        # 按严重程度分类
        high_priority = []
        medium_priority = []
        low_priority = []
        
        for rec in recommendations:
            if rec['severity'] == 'high':
                high_priority.append(rec)
            elif rec['severity'] == 'medium':
                medium_priority.append(rec)
            else:
                low_priority.append(rec)
        
        # 按类别统计
        category_stats = {}
        for rec in recommendations:
            category = rec.get('category', 'unknown')
            category_stats[category] = category_stats.get(category, 0) + 1
        
        return {
            'high_priority_count': len(high_priority),
            'medium_priority_count': len(medium_priority),
            'low_priority_count': len(low_priority),
            'total_recommendations': len(recommendations),
            'category_distribution': category_stats,
            'estimated_effort_hours': self._estimate_effort(recommendations),
            'suggested_implementation_order': self._suggest_implementation_order(recommendations)
        }
    
    def _estimate_effort(self, recommendations: List[Dict[str, Any]]) -> float:
        """
        估算优化所需的工作量（小时）
        
        Args:
            recommendations: 优化建议列表
            
        Returns:
            float: 估算的工作小时数
        """
        effort_hours = 0.0
        
        for rec in recommendations:
            # 根据严重程度估算工作量
            if rec['severity'] == 'high':
                effort_hours += 2.0  # 每个高优先级问题平均需要2小时
            elif rec['severity'] == 'medium':
                effort_hours += 1.0  # 每个中优先级问题平均需要1小时
            else:
                effort_hours += 0.5  # 每个低优先级问题平均需要0.5小时
            
            # 根据类别调整工作量
            if rec.get('category') in ['content_quality', 'keyword_density']:
                effort_hours *= 1.5  # 内容优化通常需要更多时间
            elif rec.get('category') in ['images', 'performance']:
                effort_hours *= 1.2  # 性能优化可能比较复杂
        
        # 增加10%的缓冲时间
        effort_hours *= 1.1
        
        return round(effort_hours, 1)
    
    def _suggest_implementation_order(self, recommendations: List[Dict[str, Any]]) -> List[str]:
        """
        建议实现顺序
        
        Args:
            recommendations: 优化建议列表
            
        Returns:
            List: 按优先级排序的类别列表
        """
        # 基于类别优先级定义建议的实现顺序
        category_priority = {
            'error': 1,
            'title_tags': 2,
            'meta_tags': 3,
            'headings': 4,
            'keyword_density': 5,
            'content_quality': 6,
            'images': 7,
            'performance': 8,
            'internal_links': 9,
            'external_links': 10,
            'seo': 11,
            'overall_seo': 12,
            'content': 13,
            'unknown': 14
        }
        
        # 获取所有涉及的类别
        categories = set()
        for rec in recommendations:
            category = rec.get('category', 'unknown')
            categories.add(category)
        
        # 按优先级排序
        sorted_categories = sorted(categories, key=lambda x: category_priority.get(x, 100))
        
        return sorted_categories
    
    def _check_title_tag(self, page_data: Dict[str, Any], recommendations: List[Dict[str, Any]]):
        """检查标题标签"""
        title = page_data.get('title', '')
        
        # 检查是否有标题
        for rule in self.optimization_rules.get('title_tags', []):
            if 'has_title' in str(rule['condition']):
                if not title:
                    recommendations.append({
                        'category': 'title_tags',
                        'description': "页面缺少标题标签，确保每个页面都有明确的title标签",
                        'severity': 'high',
                        'autofixable': False,
                        'priority': 1
                    })
            elif 'length' in str(rule['condition']):
                if title and (len(title) < 10 or len(title) > 60):
                    recommendations.append({
                        'category': 'title_tags',
                        'description': f"标题标签长度不合适（{len(title)}字符），建议控制在10-60个字符之间",
                        'severity': 'medium',
                        'autofixable': False,
                        'priority': 3
                    })
    
    def _check_meta_tags(self, page_data: Dict[str, Any], recommendations: List[Dict[str, Any]]):
        """检查元标签"""
        meta_description = page_data.get('meta_description', '')
        
        # 检查是否有元描述
        if not meta_description:
            recommendations.append({
                'category': 'meta_tags',
                'description': "缺少元描述标签，添加描述性的meta description标签",
                'severity': 'high',
                'autofixable': False,
                'priority': 2
            })
        # 检查元描述长度
        elif len(meta_description) < 50 or len(meta_description) > 160:
            recommendations.append({
                'category': 'meta_tags',
                'description': f"元描述长度不合适（{len(meta_description)}字符），建议控制在50-160个字符之间",
                'severity': 'medium',
                'autofixable': False,
                'priority': 3
            })
    
    def _check_keyword_density(self, keyword_density: Dict[str, float], recommendations: List[Dict[str, Any]]):
        """检查关键词密度"""
        for keyword, density in keyword_density.items():
            # 跳过太短的关键词
            if len(keyword) <= 2:
                continue
                
            for rule in self.optimization_rules.get('keyword_density', []):
                if rule['condition'](density):
                    recommendations.append({
                        'category': 'keyword_density',
                        'description': f"关键词 '{keyword}' 密度{rule['recommendation']}",
                        'severity': rule['severity'],
                        'autofixable': False,
                        'priority': self._get_priority(rule['severity'])
                    })
                # 每个关键词只添加一条建议
                break
    
    def _check_heading_structure(self, headings: Dict[str, List[str]], recommendations: List[Dict[str, Any]]):
        """检查标题结构"""
        # 检查是否有H1
        if len(headings.get('h1', [])) == 0:
            recommendations.append({
                'category': 'headings',
                'description': "页面缺少H1标签，确保每个页面有且仅有一个H1标签",
                'severity': 'high',
                'autofixable': False,
                'priority': 2
            })
        # 检查H1数量
        elif len(headings.get('h1', [])) > 1:
            recommendations.append({
                'category': 'headings',
                'description': f"页面H1标签过多（{len(headings['h1'])}个），建议每个页面只有一个H1标签",
                'severity': 'medium',
                'autofixable': False,
                'priority': 3
            })
        
        # 检查标题结构深度
        has_h2 = len(headings.get('h2', [])) > 0
        has_h3 = len(headings.get('h3', [])) > 0
        
        if not has_h2 and not has_h3:
            recommendations.append({
                'category': 'headings',
                'description': "标题结构扁平，建议使用H2、H3等多层级标题完善内容结构",
                'severity': 'medium',
                'autofixable': False,
                'priority': 4
            })
    
    def _check_images(self, images: List[Dict[str, Any]], recommendations: List[Dict[str, Any]]):
        """检查图片"""
        missing_alt_count = 0
        
        for img in images:
            if not img.get('alt', '').strip():
                missing_alt_count += 1
        
        if missing_alt_count > 0:
            recommendations.append({
                'category': 'images',
                'description': f"有{missing_alt_count}个图片缺少alt属性，为所有图片添加描述性alt标签",
                'severity': 'medium',
                'autofixable': False,
                'priority': 3
            })
    
    def _check_links(self, links: List[Dict[str, Any]], recommendations: List[Dict[str, Any]]):
        """检查链接"""
        internal_links = 0
        external_links = 0
        empty_links = 0
        
        for link in links:
            href = link.get('href', '').strip()
            text = link.get('text', '').strip()
            
            if not text:
                empty_links += 1
            
            # 简单判断是内部链接还是外部链接
            if href.startswith('http'):
                external_links += 1
            else:
                internal_links += 1
        
        # 检查内部链接数量
        if internal_links < 5:
            recommendations.append({
                'category': 'internal_links',
                'description': f"内部链接过少（{internal_links}个），建议增加相关页面的内部链接",
                'severity': 'low',
                'autofixable': False,
                'priority': 5
            })
        
        # 检查外部链接数量
        if external_links == 0:
            recommendations.append({
                'category': 'external_links',
                'description': "没有外部链接，考虑添加一些高质量的外部参考链接",
                'severity': 'low',
                'autofixable': False,
                'priority': 5
            })
        
        # 检查空链接文本
        if empty_links > 0:
            recommendations.append({
                'category': 'internal_links',
                'description': f"有{empty_links}个链接没有链接文本，确保所有链接都有描述性的文本",
                'severity': 'medium',
                'autofixable': False,
                'priority': 4
            })
    
    def _get_priority(self, severity: str) -> int:
        """根据严重程度获取优先级"""
        priority_map = {
            'high': 2,
            'medium': 3,
            'low': 5
        }
        return priority_map.get(severity, 3)