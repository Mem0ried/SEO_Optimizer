"""SEO分析器，基于现有SEO_Optimizer工具实现网站分析功能"""

import os
import logging
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup

from src.seo_automation.crawler import WebCrawler
from src.seo_automation.keyword_analyzer import KeywordAnalyzer, get_keyword_analyzer
from src.seo_automation.seo_scorer import SEOScorer
from src.seo_automation.performance_analyzer import PerformanceAnalyzer

from .config_manager import ConfigManager

logger = logging.getLogger(__name__)


class SEOAnalyzer:
    """SEO分析器，集成现有SEO_Optimizer工具进行网站分析"""
    
    def __init__(self, config_manager: ConfigManager):
        """
        初始化SEO分析器
        
        Args:
            config_manager: 配置管理器实例
        """
        self.config_manager = config_manager
        
        # 获取配置值并确保类型正确
        # 添加防御性检查，确保site_path始终是字符串类型
        site_path = config_manager.get_config('site_path')
        logger.info(f"SEOAnalyzer: site_path类型: {type(site_path)}, 值: {site_path}")
        
        # 防止ConfigManager实例被用作路径
        if isinstance(site_path, ConfigManager):
            logger.error("错误：site_path是ConfigManager实例，使用默认值")
            self.site_path = '.'
        elif isinstance(site_path, str):
            self.site_path = site_path
        else:
            logger.error(f"site_path不是字符串类型: {type(site_path)}")
            self.site_path = '.'
        
        logger.info(f"SEOAnalyzer: 最终使用的site_path: {self.site_path}, 类型: {type(self.site_path).__name__}")
        
        # 确保analysis_config是字典类型
        analysis_config = config_manager.get_config('analysis_config')
        self.analysis_config = analysis_config if isinstance(analysis_config, dict) else {}
        
        # 确保file_types是字典类型
        file_types = config_manager.get_config('file_types')
        self.file_types = file_types if isinstance(file_types, dict) else {}
        
        # 确保exclude_patterns是列表类型
        exclude_patterns = config_manager.get_config('exclude_patterns')
        self.exclude_patterns = exclude_patterns if isinstance(exclude_patterns, list) else []
        
        # 初始化分析工具
        self.crawler = None
        self.keyword_analyzer = None
        self.seo_scorer = None
        self.performance_analyzer = None
        
        # 初始化分析结果
        self.raw_pages_data = {}
        self.keyword_analysis_results = {}
        self.seo_scores = {}
        self.performance_results = {}
    
    def analyze_website(self) -> Dict[str, Any]:
        """
        对网站进行全面的SEO分析
        
        Returns:
            Dict: 分析结果汇总
        """
        logger.info(f"开始分析网站: {self.site_path}")
        
        try:
            # 1. 初始化分析工具
            self._initialize_analyzers()
            
            # 2. 爬取网站页面
            logger.info("开始爬取网站页面...")
            self._crawl_website()
            
            # 3. 进行关键词分析
            logger.info("开始关键词分析...")
            self._analyze_keywords()
            
            # 4. 进行SEO评分
            logger.info("开始SEO评分...")
            self._score_seo()
            
            # 5. 进行性能分析
            logger.info("开始性能分析...")
            self._analyze_performance()
            
            # 6. 汇总分析结果
            analysis_results = self._compile_results()
            
            logger.info("网站SEO分析完成")
            return analysis_results
            
        except Exception as e:
            logger.error(f"分析过程中发生错误: {str(e)}")
            raise
    
    def _initialize_analyzers(self):
        """初始化所有分析工具"""
        # 初始化爬虫
        max_depth = self.analysis_config.get('max_depth', 2)
        max_pages = self.analysis_config.get('max_pages', 100)
        delay = self.analysis_config.get('delay', 1)
        
        # 对于本地文件路径，我们可以使用file://前缀
        base_url = self.site_path
        
        # 确保base_url是字符串类型
        if not isinstance(base_url, str):
            logger.warning("网站路径不是有效的字符串，使用默认路径 '.'.")
            base_url = '.'
        
        # 处理本地路径
        if os.path.isdir(base_url) or os.path.isfile(base_url):
            # 如果是本地路径，转换为file://格式
            if not base_url.startswith(('http://', 'https://', 'file://')):
                # 确保使用正确的file://格式
                base_url = f'file:///{os.path.abspath(base_url).replace(chr(92), "/")}'
        
        self.crawler = WebCrawler(
            base_url=base_url,
            depth=max_depth,
            max_pages=max_pages,
            delay=delay
        )
        
        # 初始化关键词分析器
        skip_nltk_download = self.analysis_config.get('skip_nltk_download', True)
        self.keyword_analyzer = get_keyword_analyzer(skip_download=skip_nltk_download)
        
        # 初始化SEO评分器
        self.seo_scorer = SEOScorer()
        
        # 初始化性能分析器
        self.performance_analyzer = PerformanceAnalyzer()
    
    def _crawl_website(self):
        """爬取网站页面数据"""
        logger.critical("CRITICAL: 开始执行网站爬取逻辑...")
        # 对于本地网站，我们需要实现一个文件系统爬虫
        # 这里先实现一个简单版本，遍历HTML文件
        
        # 获取HTML文件类型配置
        file_types_config = self.config_manager.get_config('file_types')
        file_types = file_types_config.get('html', ['.html', '.htm']) if file_types_config else ['.html', '.htm']
        # 获取排除模式配置
        exclude_patterns = self.config_manager.get_config('exclude_patterns') or []
        
        # 确保site_path是字符串类型
        site_path = self.site_path
        if not isinstance(site_path, str):
            logger.warning("网站路径不是有效的字符串，使用默认路径 '.'.")
            site_path = '.'
        
        logger.info(f"开始扫描文件系统，查找HTML文件...")
        logger.info(f"扫描目录: {site_path}")
        logger.info(f"HTML文件类型: {file_types}")
        logger.info(f"排除模式: {exclude_patterns}")
        
        # 检查目录是否存在和可访问
        if not os.path.exists(site_path):
            logger.error(f"目录不存在: {site_path}")
            return
        if not os.path.isdir(site_path):
            logger.error(f"路径不是目录: {site_path}")
            return
            
        # 列出目录中的文件
        try:
            files_in_dir = os.listdir(site_path)
            logger.info(f"目录中的文件: {files_in_dir}")
        except Exception as e:
            logger.error(f"无法列出目录内容: {str(e)}")
            return
        
        html_found = False
        for root, dirs, files in os.walk(site_path):
            logger.info(f"扫描子目录: {root}")
            logger.info(f"找到文件数量: {len(files)}")
            
            # 过滤排除的目录
            dirs[:] = [d for d in dirs if not any(pattern in os.path.join(root, d) for pattern in exclude_patterns)]
            
            for file in files:
                logger.info(f"检查文件: {file}")
                # 检查文件类型
                if any(file.endswith(ext) for ext in file_types):
                    logger.info(f"找到HTML文件: {file}")
                    html_found = True
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, site_path)
                    
                    try:
                        # 读取文件内容
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        # 解析HTML
                        soup = BeautifulSoup(content, 'html.parser')
                        
                        # 提取页面信息
                        title = soup.title.string if soup.title else ''
                        meta_description = ''
                        meta_desc = soup.find('meta', attrs={'name': 'description'})
                        if meta_desc:
                            meta_description = meta_desc.get('content', '')
                        
                        # 提取文本内容
                        text_content = soup.get_text(separator=' ', strip=True)
                        
                        # 提取标题标签
                        headings = {'h1': [], 'h2': [], 'h3': []}
                        for level in headings.keys():
                            for heading in soup.find_all(level):
                                headings[level].append(heading.text.strip())
                        
                        # 提取图片
                        images = []
                        for img in soup.find_all('img'):
                            img_info = {
                                'src': img.get('src', ''),
                                'alt': img.get('alt', ''),
                                'title': img.get('title', '')
                            }
                            images.append(img_info)
                        
                        # 提取链接
                        links = []
                        for link in soup.find_all('a'):
                            link_info = {
                                'href': link.get('href', ''),
                                'text': link.text.strip(),
                                'title': link.get('title', '')
                            }
                            links.append(link_info)
                        
                        # 构建页面数据
                        page_data = {
                            'url': f"file:///{file_path.replace(os.sep, '/')}",
                            'path': relative_path,
                            'title': title,
                            'meta_description': meta_description,
                            'content': text_content,
                            'content_length': len(text_content),
                            'headings': headings,
                            'images': images,
                            'links': links,
                            'status_code': 200,  # 本地文件始终成功
                            'response_time': 0,  # 本地文件没有响应时间
                            'depth': relative_path.count(os.sep)  # 使用目录深度作为爬取深度
                        }
                        
                        self.raw_pages_data[relative_path] = page_data
                        
                    except Exception as e:
                        logger.warning(f"处理文件失败 {file_path}: {str(e)}")
                        # 记录错误页面
                        self.raw_pages_data[relative_path] = {
                            'url': f"file:///{file_path.replace(os.sep, '/')}",
                            'path': relative_path,
                            'error': str(e),
                            'status_code': None,
                            'depth': relative_path.count(os.sep)
                        }
        
        logger.info(f"扫描完成，共发现 {len(self.raw_pages_data)} 个HTML文件")
    
    def _analyze_keywords(self):
        """分析页面关键词"""
        page_analyses = {}
        all_content = []
        
        # 收集所有内容用于整体分析
        for path, page_data in self.raw_pages_data.items():
            if 'error' not in page_data and 'content' in page_data:
                all_content.append(page_data['content'])
        
        # 对每个页面进行关键词分析
        for path, page_data in self.raw_pages_data.items():
            if 'error' in page_data:
                page_analyses[path] = {'error': page_data['error']}
                continue
            
            try:
                # 提取页面文本内容
                text_content = page_data.get('content', '')
                title = page_data.get('title', '')
                
                # 分析关键词密度
                # 由于我们没有预先定义关键词，先使用文本中的高频词
                # 这里简化处理，实际应该从配置或网站内容中提取关键词
                
                # 预处理文本
                processed_text = self.keyword_analyzer._preprocess_text(text_content)
                
                # 简单的关键词分析
                keyword_density = {}
                if processed_text:
                    # 统计词频
                    word_freq = {}
                    for word in processed_text:
                        if len(word) > 2:  # 忽略太短的词
                            word_freq[word] = word_freq.get(word, 0) + 1
                    
                    # 提取前10个高频词作为关键词
                    total_words = len(processed_text)
                    if total_words > 0:
                        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
                        for word, count in sorted_words:
                            keyword_density[word] = (count / total_words) * 100
                
                # 分析标题中的关键词
                title_keyword_analysis = {}
                if title:
                    title_lower = title.lower()
                    for keyword in keyword_density.keys():
                        if keyword in title_lower:
                            title_keyword_analysis[keyword] = {
                                'present': True,
                                'early_in_title': title_lower.index(keyword) < len(title_lower) * 0.3
                            }
                        else:
                            title_keyword_analysis[keyword] = {'present': False}
                
                # 构建页面分析结果
                page_analyses[path] = {
                    'keyword_density': keyword_density,
                    'title_keyword_analysis': title_keyword_analysis,
                    'keyword_recommendations': []  # 后续可以扩展
                }
                
            except Exception as e:
                logger.warning(f"关键词分析失败 {path}: {str(e)}")
                page_analyses[path] = {'error': str(e)}
        
        # 生成整体推荐（简化）
        overall_recommendations = []
        if len(self.raw_pages_data) > 0:
            overall_recommendations.append("基于页面内容进行关键词优化")
        
        self.keyword_analysis_results = {
            'page_analyses': page_analyses,
            'overall_recommendations': overall_recommendations
        }
    
    def _score_seo(self):
        """进行SEO评分"""
        # 使用SEOScorer进行评分
        self.seo_scores = self.seo_scorer.score_multiple_pages(
            self.raw_pages_data,
            self.keyword_analysis_results
        )
    
    def _analyze_performance(self):
        """进行性能分析"""
        # 对于本地文件，性能分析相对简单
        # 主要分析文件大小和资源数量
        
        total_size = 0
        resource_counts = {
            'html': 0,
            'css': 0,
            'js': 0,
            'images': 0,
            'other': 0
        }
        
        # 分析文件大小
        file_types = self.config_manager.get_config('file_types') or {}
        
        for root, dirs, files in os.walk(self.site_path):
            # 过滤排除的目录
            exclude_patterns = self.config_manager.get_config('exclude_patterns') or []
            dirs[:] = [d for d in dirs if not any(pattern in os.path.join(root, d) for pattern in exclude_patterns)]
            
            for file in files:
                file_path = os.path.join(root, file)
                
                try:
                    # 获取文件大小
                    file_size = os.path.getsize(file_path)
                    total_size += file_size
                    
                    # 分类统计
                    file_ext = os.path.splitext(file)[1].lower()
                    
                    if file_ext in file_types.get('html', []):
                        resource_counts['html'] += 1
                    elif file_ext in file_types.get('css', []):
                        resource_counts['css'] += 1
                    elif file_ext in file_types.get('js', []):
                        resource_counts['js'] += 1
                    elif file_ext in file_types.get('images', []):
                        resource_counts['images'] += 1
                    else:
                        resource_counts['other'] += 1
                        
                except Exception as e:
                    logger.warning(f"分析文件大小失败 {file_path}: {str(e)}")
        
        # 构建性能分析结果
        self.performance_results = {
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'resource_counts': resource_counts,
            'page_count': len(self.raw_pages_data),
            'performance_score': self._calculate_performance_score(total_size, resource_counts),
            'optimization_suggestions': self._generate_performance_suggestions(total_size, resource_counts)
        }
    
    def _calculate_performance_score(self, total_size: int, resource_counts: Dict[str, int]) -> float:
        """计算性能得分"""
        # 简单的性能评分算法
        score = 100.0
        
        # 基于总大小的评分（满分40分）
        size_mb = total_size / (1024 * 1024)
        if size_mb > 50:
            score -= 40
        elif size_mb > 30:
            score -= 30
        elif size_mb > 20:
            score -= 20
        elif size_mb > 10:
            score -= 10
        
        # 基于资源数量的评分（满分30分）
        total_resources = sum(resource_counts.values())
        if total_resources > 500:
            score -= 30
        elif total_resources > 300:
            score -= 20
        elif total_resources > 200:
            score -= 10
        
        # 基于图片数量的评分（满分30分）
        image_count = resource_counts.get('images', 0)
        if image_count > 200:
            score -= 30
        elif image_count > 100:
            score -= 20
        elif image_count > 50:
            score -= 10
        
        return max(0, score)
    
    def _generate_performance_suggestions(self, total_size: int, resource_counts: Dict[str, int]) -> List[str]:
        """生成性能优化建议"""
        suggestions = []
        size_mb = total_size / (1024 * 1024)
        
        if size_mb > 20:
            suggestions.append(f"网站总大小为 {size_mb:.2f}MB，建议优化资源大小，目标控制在20MB以内")
        
        if resource_counts.get('images', 0) > 50:
            suggestions.append(f"图片数量较多（{resource_counts['images']}个），建议压缩图片并使用合适的格式")
        
        if resource_counts.get('js', 0) > 20:
            suggestions.append(f"JavaScript文件较多（{resource_counts['js']}个），建议合并和压缩JS文件")
        
        if resource_counts.get('css', 0) > 10:
            suggestions.append(f"CSS文件较多（{resource_counts['css']}个），建议合并和压缩CSS文件")
        
        return suggestions
    
    def _compile_results(self) -> Dict[str, Any]:
        """汇总所有分析结果"""
        return {
            'raw_pages_data': self.raw_pages_data,
            'keyword_analysis': self.keyword_analysis_results,
            'seo_scores': self.seo_scores,
            'performance_analysis': self.performance_results,
            'summary': {
                'total_pages': len(self.raw_pages_data),
                'overall_seo_score': self.seo_scores.get('overall_scores', {}).get('weighted_total', 0),
                'performance_score': self.performance_results.get('performance_score', 0),
                'total_resources': sum(self.performance_results.get('resource_counts', {}).values()),
                'total_size_mb': self.performance_results.get('total_size_mb', 0)
            }
        }
    
    def get_page_analysis(self, page_path: str) -> Optional[Dict[str, Any]]:
        """
        获取单个页面的分析结果
        
        Args:
            page_path: 页面相对路径
            
        Returns:
            Dict: 页面分析结果，如果不存在返回None
        """
        page_data = self.raw_pages_data.get(page_path)
        keyword_analysis = self.keyword_analysis_results.get('page_analyses', {}).get(page_path)
        seo_score = self.seo_scores.get('page_scores', {}).get(page_path)
        
        if not page_data:
            return None
        
        return {
            'page_data': page_data,
            'keyword_analysis': keyword_analysis,
            'seo_score': seo_score
        }
    
    def get_top_issues(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        获取排名靠前的问题
        
        Args:
            limit: 返回问题的数量限制
            
        Returns:
            List: 问题列表
        """
        issues = []
        
        # 从SEO评分中提取问题
        overall_suggestions = self.seo_scores.get('overall_suggestions', [])
        for suggestion in overall_suggestions[:limit]:
            issues.append({
                'type': 'seo',
                'severity': 'high',
                'description': suggestion
            })
        
        # 从性能分析中提取问题
        performance_suggestions = self.performance_results.get('optimization_suggestions', [])
        for suggestion in performance_suggestions[:limit - len(issues)]:
            issues.append({
                'type': 'performance',
                'severity': 'medium',
                'description': suggestion
            })
        
        # 从页面分析中提取问题
        if len(issues) < limit:
            page_scores = self.seo_scores.get('page_scores', {})
            for path, score_data in page_scores.items():
                if len(issues) >= limit:
                    break
                
                suggestions = score_data.get('improvement_suggestions', [])
                for suggestion in suggestions[:1]:  # 每个页面只取一个问题
                    issues.append({
                        'type': 'page',
                        'severity': 'medium',
                        'description': f"页面 {path}: {suggestion}"
                    })
                    if len(issues) >= limit:
                        break
        
        return issues[:limit]