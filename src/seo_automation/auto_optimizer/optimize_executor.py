"""自动优化执行器，针对不同类型的优化项实现自动修改"""

import os
import logging
import re
import shutil
from typing import Dict, List, Any, Tuple, Optional
from bs4 import BeautifulSoup, Comment, Tag

from .config_manager import ConfigManager

logger = logging.getLogger(__name__)


class OptimizeExecutor:
    """自动优化执行器，负责根据优化建议自动修改网站文件"""
    
    def __init__(self, config_manager: ConfigManager):
        """
        初始化优化执行器
        
        Args:
            config_manager: 配置管理器实例
        """
        self.config_manager = config_manager
        self.site_path = config_manager.get_config('site_path')
        # 获取配置项
        self.optimization_config = config_manager.get_config('optimization_config') or {}
        self.file_types = config_manager.get_config('file_types') or {}
        self.exclude_patterns = config_manager.get_config('exclude_patterns') or []
        
        # 优化操作的历史记录
        self.optimization_history = []
        
        # 加载优化器配置
        self.enabled_optimizers = self._load_enabled_optimizers()
    
    def _load_enabled_optimizers(self) -> Dict[str, bool]:
        """
        加载启用的优化器配置
        
        Returns:
            Dict: 优化器启用状态
        """
        default_optimizers = {
            'meta_tags_optimizer': True,
            'title_tags_optimizer': True,
            'image_alt_optimizer': True,
            'heading_structure_optimizer': True,
            'link_optimizer': True,
            'content_optimizer': False,  # 内容优化默认禁用，因为可能改变语义
            'keyword_optimizer': False,  # 关键词优化默认禁用，需要人工审核
            'performance_optimizer': False  # 性能优化默认禁用，可能涉及文件压缩等复杂操作
        }
        
        # 从配置中加载
        config_optimizers = self.optimization_config.get('enabled_optimizers', {})
        default_optimizers.update(config_optimizers)
        
        return default_optimizers
    
    def execute_optimization(self, recommendations: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行优化建议
        
        Args:
            recommendations: 优化建议
            
        Returns:
            Dict: 优化执行结果
        """
        logger.info("开始执行自动优化...")
        
        # 清空历史记录
        self.optimization_history = []
        
        # 统计信息
        stats = {
            'total_recommendations': 0,
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'by_category': {},
            'optimization_details': []
        }
        
        try:
            # 获取优先级建议列表
            prioritized = recommendations.get('prioritized_recommendations', [])
            stats['total_recommendations'] = len(prioritized)
            
            # 按页面分组处理建议
            recommendations_by_page = {}
            for rec in prioritized:
                if rec['scope'] == 'page' and 'page_path' in rec:
                    page_path = rec['page_path']
                    if page_path not in recommendations_by_page:
                        recommendations_by_page[page_path] = []
                    recommendations_by_page[page_path].append(rec)
                elif rec['scope'] == 'overall':
                    # 整体优化建议，需要特殊处理
                    logger.info(f"跳过整体优化建议: {rec['description']}")
                    stats['skipped'] += 1
            
            # 处理每个页面的优化建议
            for page_path, page_recs in recommendations_by_page.items():
                # 按类别分组，确保优化的顺序性
                recs_by_category = self._group_recommendations_by_category(page_recs)
                
                # 执行页面优化
                page_stats = self._optimize_page(page_path, recs_by_category)
                
                # 更新统计信息
                stats['processed'] += page_stats['processed']
                stats['successful'] += page_stats['successful']
                stats['failed'] += page_stats['failed']
                stats['skipped'] += page_stats['skipped']
                
                # 更新分类统计
                for category, count in page_stats.get('by_category', {}).items():
                    if category not in stats['by_category']:
                        stats['by_category'][category] = {}
                    for status, status_count in count.items():
                        stats['by_category'][category][status] = stats['by_category'][category].get(status, 0) + status_count
                
                # 添加优化详情
                stats['optimization_details'].extend(page_stats['optimization_details'])
            
            logger.info(f"优化执行完成。成功: {stats['successful']}, 失败: {stats['failed']}, 跳过: {stats['skipped']}")
            
            return {
                'status': 'completed',
                'stats': stats,
                'optimization_history': self.optimization_history
            }
            
        except Exception as e:
            logger.error(f"执行优化时发生错误: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'stats': stats
            }
    
    def _group_recommendations_by_category(self, recommendations: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        按类别分组优化建议
        
        Args:
            recommendations: 优化建议列表
            
        Returns:
            Dict: 按类别分组的优化建议
        """
        grouped = {}
        
        # 建议的优化顺序
        recommended_order = ['title_tags', 'meta_tags', 'headings', 'images', 
                           'internal_links', 'external_links', 'keyword_density', 
                           'content_quality', 'performance']
        
        # 初始化分组
        for category in recommended_order:
            grouped[category] = []
        grouped['other'] = []
        
        # 分组建议
        for rec in recommendations:
            category = rec.get('category', 'other')
            if category in grouped:
                grouped[category].append(rec)
            else:
                grouped['other'].append(rec)
        
        return grouped
    
    def _optimize_page(self, page_path: str, recs_by_category: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        优化单个页面
        
        Args:
            page_path: 页面相对路径
            recs_by_category: 按类别分组的优化建议
            
        Returns:
            Dict: 页面优化统计
        """
        stats = {
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'by_category': {},
            'optimization_details': []
        }
        
        # 构建完整文件路径
        full_path = os.path.join(self.site_path, page_path)
        
        # 检查文件是否存在
        if not os.path.exists(full_path):
            logger.warning(f"页面文件不存在: {full_path}")
            return stats
        
        # 检查文件类型
        file_ext = os.path.splitext(full_path)[1].lower()
        html_exts = self.file_types.get('html', ['.html', '.htm'])
        if file_ext not in html_exts:
            logger.warning(f"不支持的文件类型: {full_path}")
            return stats
        
        # 读取文件内容
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                original_content = f.read()
            
            # 解析HTML
            soup = BeautifulSoup(original_content, 'html.parser')
            
            # 备份原始内容
            self.optimization_history.append({
                'file_path': page_path,
                'original_content': original_content
            })
            
            # 按顺序执行各类优化
            for category, recommendations in recs_by_category.items():
                if not recommendations:
                    continue
                
                # 初始化类别统计
                if category not in stats['by_category']:
                    stats['by_category'][category] = {'processed': 0, 'successful': 0, 'failed': 0, 'skipped': 0}
                
                # 根据类别执行优化
                if category == 'title_tags' and self.enabled_optimizers.get('title_tags_optimizer', True):
                    cat_stats, details = self._optimize_title_tags(soup, recommendations, page_path)
                elif category == 'meta_tags' and self.enabled_optimizers.get('meta_tags_optimizer', True):
                    cat_stats, details = self._optimize_meta_tags(soup, recommendations, page_path)
                elif category == 'headings' and self.enabled_optimizers.get('heading_structure_optimizer', True):
                    cat_stats, details = self._optimize_headings(soup, recommendations, page_path)
                elif category in ['images', 'image_alt'] and self.enabled_optimizers.get('image_alt_optimizer', True):
                    cat_stats, details = self._optimize_images(soup, recommendations, page_path)
                elif category in ['internal_links', 'external_links'] and self.enabled_optimizers.get('link_optimizer', True):
                    cat_stats, details = self._optimize_links(soup, recommendations, page_path)
                elif category == 'keyword_density' and self.enabled_optimizers.get('keyword_optimizer', False):
                    cat_stats, details = self._optimize_keywords(soup, recommendations, page_path)
                elif category == 'content_quality' and self.enabled_optimizers.get('content_optimizer', False):
                    cat_stats, details = self._optimize_content(soup, recommendations, page_path)
                else:
                    # 跳过未启用或不支持的优化器
                    cat_stats = {'processed': len(recommendations), 'successful': 0, 'failed': 0, 'skipped': len(recommendations)}
                    details = []
                    for rec in recommendations:
                        details.append({
                            'page_path': page_path,
                            'category': category,
                            'description': rec['description'],
                            'status': 'skipped',
                            'reason': 'optimizer_disabled_or_not_supported'
                        })
                
                # 更新统计
                stats['processed'] += cat_stats['processed']
                stats['successful'] += cat_stats['successful']
                stats['failed'] += cat_stats['failed']
                stats['skipped'] += cat_stats['skipped']
                
                stats['by_category'][category]['processed'] += cat_stats['processed']
                stats['by_category'][category]['successful'] += cat_stats['successful']
                stats['by_category'][category]['failed'] += cat_stats['failed']
                stats['by_category'][category]['skipped'] += cat_stats['skipped']
                
                stats['optimization_details'].extend(details)
            
            # 保存修改后的内容
            modified_content = str(soup)
            
            # 只有当内容发生变化时才保存
            if modified_content != original_content:
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(modified_content)
                
                # 更新历史记录
                for i, history in enumerate(self.optimization_history):
                    if history['file_path'] == page_path:
                        self.optimization_history[i]['modified_content'] = modified_content
                        break
            
        except Exception as e:
            logger.error(f"优化页面失败 {page_path}: {str(e)}")
            
            # 记录失败的详情
            stats['optimization_details'].append({
                'page_path': page_path,
                'category': 'general',
                'description': '页面优化过程中发生错误',
                'status': 'error',
                'error': str(e)
            })
            stats['failed'] += 1
        
        return stats
    
    def _optimize_title_tags(self, soup: BeautifulSoup, recommendations: List[Dict[str, Any]], page_path: str) -> Tuple[Dict[str, int], List[Dict[str, Any]]]:
        """
        优化标题标签
        
        Args:
            soup: BeautifulSoup对象
            recommendations: 优化建议
            page_path: 页面路径
            
        Returns:
            Tuple: (统计信息, 详细信息)
        """
        stats = {'processed': 0, 'successful': 0, 'failed': 0, 'skipped': 0}
        details = []
        
        for rec in recommendations:
            stats['processed'] += 1
            detail = {
                'page_path': page_path,
                'category': 'title_tags',
                'description': rec['description'],
                'status': 'failed'
            }
            
            try:
                # 检查是否缺少标题
                if '缺少标题标签' in rec['description']:
                    # 创建标题标签
                    if not soup.title:
                        if soup.head:
                            title_tag = soup.new_tag('title')
                            # 基于页面路径生成简单标题
                            page_name = os.path.splitext(os.path.basename(page_path))[0]
                            title_text = page_name.replace('_', ' ').replace('-', ' ').title()
                            title_tag.string = title_text
                            soup.head.append(title_tag)
                            
                            detail['status'] = 'successful'
                            detail['action'] = f'添加了标题标签: {title_text}'
                            stats['successful'] += 1
                        else:
                            # 如果没有head标签，创建一个
                            head_tag = soup.new_tag('head')
                            title_tag = soup.new_tag('title')
                            page_name = os.path.splitext(os.path.basename(page_path))[0]
                            title_text = page_name.replace('_', ' ').replace('-', ' ').title()
                            title_tag.string = title_text
                            head_tag.append(title_tag)
                            
                            # 插入到body之前或文档开头
                            if soup.body:
                                soup.body.insert_before(head_tag)
                            else:
                                soup.insert(0, head_tag)
                            
                            detail['status'] = 'successful'
                            detail['action'] = f'创建了head和title标签: {title_text}'
                            stats['successful'] += 1
                    else:
                        # 已有标题，更新内容
                        page_name = os.path.splitext(os.path.basename(page_path))[0]
                        title_text = page_name.replace('_', ' ').replace('-', ' ').title()
                        soup.title.string = title_text
                        
                        detail['status'] = 'successful'
                        detail['action'] = f'更新了标题标签: {title_text}'
                        stats['successful'] += 1
                
                # 检查标题长度
                elif '标题标签长度不合适' in rec['description'] and soup.title:
                    current_title = soup.title.string or ''
                    if len(current_title) < 10:
                        # 太短，补充内容
                        page_name = os.path.splitext(os.path.basename(page_path))[0]
                        supplement = page_name.replace('_', ' ').replace('-', ' ').title()
                        if supplement not in current_title:
                            new_title = f"{current_title} - {supplement}"
                            # 确保不超过60个字符
                            if len(new_title) > 60:
                                new_title = new_title[:57] + '...'
                            soup.title.string = new_title
                            detail['status'] = 'successful'
                            detail['action'] = f'补充了标题内容: {new_title}'
                            stats['successful'] += 1
                    elif len(current_title) > 60:
                        # 太长，截断
                        new_title = current_title[:57] + '...'
                        soup.title.string = new_title
                        detail['status'] = 'successful'
                        detail['action'] = f'截断了过长的标题，从 {len(current_title)} 字符到 60 字符'
                        stats['successful'] += 1
                
            except Exception as e:
                detail['error'] = str(e)
                stats['failed'] += 1
            
            details.append(detail)
        
        return stats, details
    
    def _optimize_meta_tags(self, soup: BeautifulSoup, recommendations: List[Dict[str, Any]], page_path: str) -> Tuple[Dict[str, int], List[Dict[str, Any]]]:
        """
        优化元标签
        
        Args:
            soup: BeautifulSoup对象
            recommendations: 优化建议
            page_path: 页面路径
            
        Returns:
            Tuple: (统计信息, 详细信息)
        """
        stats = {'processed': 0, 'successful': 0, 'failed': 0, 'skipped': 0}
        details = []
        
        for rec in recommendations:
            stats['processed'] += 1
            detail = {
                'page_path': page_path,
                'category': 'meta_tags',
                'description': rec['description'],
                'status': 'failed'
            }
            
            try:
                # 检查是否缺少元描述
                if '缺少元描述标签' in rec['description']:
                    # 确保有head标签
                    if not soup.head:
                        head_tag = soup.new_tag('head')
                        if soup.body:
                            soup.body.insert_before(head_tag)
                        else:
                            soup.insert(0, head_tag)
                    
                    # 检查是否已有meta description
                    existing_meta_desc = soup.find('meta', attrs={'name': 'description'})
                    if not existing_meta_desc:
                        # 创建meta description标签
                        meta_tag = soup.new_tag('meta')
                        meta_tag['name'] = 'description'
                        
                        # 生成简单的描述
                        page_name = os.path.splitext(os.path.basename(page_path))[0]
                        description = f"{page_name.replace('_', ' ').replace('-', ' ').title()}页面 - 提供详细的相关信息和内容。"
                        meta_tag['content'] = description
                        
                        # 插入到head中
                        soup.head.append(meta_tag)
                        
                        detail['status'] = 'successful'
                        detail['action'] = f'添加了元描述标签'
                        stats['successful'] += 1
                    else:
                        # 已有meta description但可能为空
                        if not existing_meta_desc.get('content', '').strip():
                            page_name = os.path.splitext(os.path.basename(page_path))[0]
                            description = f"{page_name.replace('_', ' ').replace('-', ' ').title()}页面 - 提供详细的相关信息和内容。"
                            existing_meta_desc['content'] = description
                            
                            detail['status'] = 'successful'
                            detail['action'] = f'填充了空的元描述标签'
                            stats['successful'] += 1
                
                # 检查元描述长度
                elif '元描述长度不合适' in rec['description']:
                    meta_desc = soup.find('meta', attrs={'name': 'description'})
                    if meta_desc:
                        current_content = meta_desc.get('content', '')
                        if len(current_content) < 50:
                            # 太短，补充内容
                            page_name = os.path.splitext(os.path.basename(page_path))[0]
                            supplement = f" 这是{page_name.replace('_', ' ').replace('-', ' ')}页面，包含相关的详细信息和资源。"
                            new_content = current_content + supplement
                            # 确保不超过160个字符
                            if len(new_content) > 160:
                                new_content = new_content[:157] + '...'
                            meta_desc['content'] = new_content
                            
                            detail['status'] = 'successful'
                            detail['action'] = f'补充了元描述内容，从 {len(current_content)} 字符增加到 {len(new_content)} 字符'
                            stats['successful'] += 1
                        elif len(current_content) > 160:
                            # 太长，截断
                            new_content = current_content[:157] + '...'
                            meta_desc['content'] = new_content
                            
                            detail['status'] = 'successful'
                            detail['action'] = f'截断了过长的元描述，从 {len(current_content)} 字符到 160 字符'
                            stats['successful'] += 1
                
            except Exception as e:
                detail['error'] = str(e)
                stats['failed'] += 1
            
            details.append(detail)
        
        return stats, details
    
    def _optimize_headings(self, soup: BeautifulSoup, recommendations: List[Dict[str, Any]], page_path: str) -> Tuple[Dict[str, int], List[Dict[str, Any]]]:
        """
        优化标题结构
        
        Args:
            soup: BeautifulSoup对象
            recommendations: 优化建议
            page_path: 页面路径
            
        Returns:
            Tuple: (统计信息, 详细信息)
        """
        stats = {'processed': 0, 'successful': 0, 'failed': 0, 'skipped': 0}
        details = []
        
        for rec in recommendations:
            stats['processed'] += 1
            detail = {
                'page_path': page_path,
                'category': 'headings',
                'description': rec['description'],
                'status': 'failed'
            }
            
            try:
                # 检查是否缺少H1
                if '页面缺少H1标签' in rec['description']:
                    # 查找所有H1标签
                    h1_tags = soup.find_all('h1')
                    if len(h1_tags) == 0:
                        # 尝试从页面中找一个合适的文本作为H1
                        potential_headings = []
                        
                        # 检查title
                        if soup.title:
                            potential_headings.append(soup.title.string)
                        
                        # 检查其他标题
                        for level in ['h2', 'h3']:
                            for heading in soup.find_all(level):
                                if heading.get_text(strip=True):
                                    potential_headings.append(heading.get_text(strip=True))
                        
                        # 检查strong或b标签
                        for strong_tag in soup.find_all(['strong', 'b']):
                            text = strong_tag.get_text(strip=True)
                            if text and len(text) > 10 and len(text) < 100:  # 合理长度
                                potential_headings.append(text)
                        
                        # 如果没有找到，使用页面名
                        if not potential_headings:
                            page_name = os.path.splitext(os.path.basename(page_path))[0]
                            potential_headings.append(page_name.replace('_', ' ').replace('-', ' ').title())
                        
                        # 创建H1标签
                        h1_tag = soup.new_tag('h1')
                        h1_tag.string = potential_headings[0]
                        
                        # 插入到body的开头或第一个段落之前
                        if soup.body:
                            first_element = soup.body.find()
                            if first_element:
                                first_element.insert_before(h1_tag)
                            else:
                                soup.body.append(h1_tag)
                            
                            detail['status'] = 'successful'
                            detail['action'] = f'添加了H1标签: {h1_tag.string}'
                            stats['successful'] += 1
                
                # 检查H1数量过多
                elif '页面H1标签过多' in rec['description']:
                    h1_tags = soup.find_all('h1')
                    if len(h1_tags) > 1:
                        # 保留第一个H1，将其他降级为H2
                        for h1 in h1_tags[1:]:
                            # 创建新的H2标签
                            h2_tag = soup.new_tag('h2')
                            h2_tag.string = h1.string
                            # 替换H1为H2
                            h1.replace_with(h2_tag)
                        
                        detail['status'] = 'successful'
                        detail['action'] = f'将 {len(h1_tags) - 1} 个H1标签降级为H2标签'
                        stats['successful'] += 1
                
            except Exception as e:
                detail['error'] = str(e)
                stats['failed'] += 1
            
            details.append(detail)
        
        return stats, details
    
    def _optimize_images(self, soup: BeautifulSoup, recommendations: List[Dict[str, Any]], page_path: str) -> Tuple[Dict[str, int], List[Dict[str, Any]]]:
        """
        优化图片
        
        Args:
            soup: BeautifulSoup对象
            recommendations: 优化建议
            page_path: 页面路径
            
        Returns:
            Tuple: (统计信息, 详细信息)
        """
        stats = {'processed': 0, 'successful': 0, 'failed': 0, 'skipped': 0}
        details = []
        
        for rec in recommendations:
            stats['processed'] += 1
            detail = {
                'page_path': page_path,
                'category': 'images',
                'description': rec['description'],
                'status': 'failed'
            }
            
            try:
                # 检查缺少alt属性的图片
                if '缺少alt属性' in rec['description']:
                    images = soup.find_all('img')
                    missing_alt_count = 0
                    
                    for img in images:
                        if not img.get('alt', '').strip():
                            # 生成alt文本
                            alt_text = ''
                            
                            # 从文件名生成
                            src = img.get('src', '')
                            if src:
                                # 提取文件名
                                filename = os.path.basename(src)
                                # 移除扩展名
                                name_without_ext = os.path.splitext(filename)[0]
                                # 格式化
                                alt_text = name_without_ext.replace('_', ' ').replace('-', ' ').replace('%20', ' ')
                                
                                # 移除文件路径中的数字和特殊字符
                                alt_text = re.sub(r'\d+', '', alt_text)
                                alt_text = re.sub(r'[\\/:*?"<>|]', ' ', alt_text)
                                alt_text = alt_text.strip()
                            
                            # 如果从文件名得不到好的描述，使用通用描述
                            if not alt_text or len(alt_text) < 3:
                                # 检查父元素是否有标题
                                parent = img.find_parent()
                                if parent and parent.get('title', ''):
                                    alt_text = parent['title']
                                elif parent and parent.get('class'):
                                    # 使用父元素的类名
                                    classes = ' '.join(parent.get('class', []))
                                    if 'banner' in classes.lower():
                                        alt_text = '网站横幅图片'
                                    elif 'logo' in classes.lower():
                                        alt_text = '网站标志'
                                    elif 'product' in classes.lower():
                                        alt_text = '产品图片'
                                    else:
                                        alt_text = '网站图片'
                                else:
                                    alt_text = '网站图片'
                            
                            # 设置alt属性
                            img['alt'] = alt_text
                            missing_alt_count += 1
                    
                    if missing_alt_count > 0:
                        detail['status'] = 'successful'
                        detail['action'] = f'为 {missing_alt_count} 个图片添加了alt属性'
                        stats['successful'] += 1
                    else:
                        detail['status'] = 'skipped'
                        detail['reason'] = '没有发现缺少alt属性的图片'
                        stats['skipped'] += 1
                
            except Exception as e:
                detail['error'] = str(e)
                stats['failed'] += 1
            
            details.append(detail)
        
        return stats, details
    
    def _optimize_links(self, soup: BeautifulSoup, recommendations: List[Dict[str, Any]], page_path: str) -> Tuple[Dict[str, int], List[Dict[str, Any]]]:
        """
        优化链接
        
        Args:
            soup: BeautifulSoup对象
            recommendations: 优化建议
            page_path: 页面路径
            
        Returns:
            Tuple: (统计信息, 详细信息)
        """
        stats = {'processed': 0, 'successful': 0, 'failed': 0, 'skipped': 0}
        details = []
        
        for rec in recommendations:
            stats['processed'] += 1
            detail = {
                'page_path': page_path,
                'category': 'links',
                'description': rec['description'],
                'status': 'failed'
            }
            
            try:
                # 检查空链接文本
                if '有.*个链接没有链接文本' in rec['description']:
                    links = soup.find_all('a')
                    empty_text_count = 0
                    
                    for link in links:
                        link_text = link.get_text(strip=True)
                        href = link.get('href', '')
                        
                        if not link_text and href:
                            # 生成链接文本
                            link_text = ''
                            
                            # 检查title属性
                            if link.get('title', ''):
                                link_text = link['title']
                            else:
                                # 从href生成
                                if href.startswith('#'):
                                    # 锚点链接
                                    target_id = href[1:]
                                    target = soup.find(id=target_id)
                                    if target:
                                        # 获取目标元素的文本
                                        target_text = target.get_text(strip=True)
                                        if target_text:
                                            link_text = target_text[:30] + ('...' if len(target_text) > 30 else '')
                                    if not link_text:
                                        link_text = f'跳转到页面内锚点'
                                elif href.startswith('http'):
                                    # 外部链接
                                    # 提取域名
                                    from urllib.parse import urlparse
                                    parsed = urlparse(href)
                                    if parsed.netloc:
                                        link_text = parsed.netloc
                                    else:
                                        link_text = '外部链接'
                                else:
                                    # 内部链接
                                    # 提取文件名
                                    filename = os.path.basename(href)
                                    name_without_ext = os.path.splitext(filename)[0]
                                    if name_without_ext:
                                        link_text = name_without_ext.replace('_', ' ').replace('-', ' ').title()
                                    else:
                                        link_text = '内部链接'
                            
                            # 设置链接文本
                            link.string = link_text
                            empty_text_count += 1
                    
                    if empty_text_count > 0:
                        detail['status'] = 'successful'
                        detail['action'] = f'为 {empty_text_count} 个空链接添加了描述性文本'
                        stats['successful'] += 1
                    else:
                        detail['status'] = 'skipped'
                        detail['reason'] = '没有发现空链接文本'
                        stats['skipped'] += 1
                
            except Exception as e:
                detail['error'] = str(e)
                stats['failed'] += 1
            
            details.append(detail)
        
        return stats, details
    
    def _optimize_keywords(self, soup: BeautifulSoup, recommendations: List[Dict[str, Any]], page_path: str) -> Tuple[Dict[str, int], List[Dict[str, Any]]]:
        """
        优化关键词（默认禁用）
        
        Args:
            soup: BeautifulSoup对象
            recommendations: 优化建议
            page_path: 页面路径
            
        Returns:
            Tuple: (统计信息, 详细信息)
        """
        # 关键词优化默认禁用，返回跳过状态
        stats = {'processed': len(recommendations), 'successful': 0, 'failed': 0, 'skipped': len(recommendations)}
        details = []
        
        for rec in recommendations:
            details.append({
                'page_path': page_path,
                'category': 'keyword_density',
                'description': rec['description'],
                'status': 'skipped',
                'reason': 'keyword_optimizer_disabled_by_default'
            })
        
        return stats, details
    
    def _optimize_content(self, soup: BeautifulSoup, recommendations: List[Dict[str, Any]], page_path: str) -> Tuple[Dict[str, int], List[Dict[str, Any]]]:
        """
        优化内容（默认禁用）
        
        Args:
            soup: BeautifulSoup对象
            recommendations: 优化建议
            page_path: 页面路径
            
        Returns:
            Tuple: (统计信息, 详细信息)
        """
        # 内容优化默认禁用，返回跳过状态
        stats = {'processed': len(recommendations), 'successful': 0, 'failed': 0, 'skipped': len(recommendations)}
        details = []
        
        for rec in recommendations:
            details.append({
                'page_path': page_path,
                'category': 'content_quality',
                'description': rec['description'],
                'status': 'skipped',
                'reason': 'content_optimizer_disabled_by_default'
            })
        
        return stats, details
    
    def undo_last_optimization(self) -> Dict[str, Any]:
        """
        撤销上一次优化操作
        
        Returns:
            Dict: 撤销结果
        """
        logger.info("开始撤销上一次优化...")
        
        if not self.optimization_history:
            return {
                'status': 'no_changes',
                'message': '没有可撤销的优化操作'
            }
        
        undo_stats = {
            'total_files': len(self.optimization_history),
            'successfully_restored': 0,
            'failed_to_restore': 0
        }
        
        for history in self.optimization_history:
            file_path = history['file_path']
            full_path = os.path.join(self.site_path, file_path)
            
            try:
                if os.path.exists(full_path):
                    # 恢复原始内容
                    with open(full_path, 'w', encoding='utf-8') as f:
                        f.write(history['original_content'])
                    undo_stats['successfully_restored'] += 1
                    logger.info(f"成功恢复文件: {file_path}")
            except Exception as e:
                undo_stats['failed_to_restore'] += 1
                logger.error(f"恢复文件失败 {file_path}: {str(e)}")
        
        # 清空历史记录
        self.optimization_history = []
        
        return {
            'status': 'completed',
            'stats': undo_stats
        }
    
    def get_optimization_history(self) -> List[Dict[str, Any]]:
        """
        获取优化历史记录
        
        Returns:
            List: 优化历史记录
        """
        return self.optimization_history