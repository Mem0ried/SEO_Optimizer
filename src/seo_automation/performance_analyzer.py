import time
import requests
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urlparse
import logging
import statistics
from requests.exceptions import RequestException
from bs4 import BeautifulSoup
import re

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PerformanceAnalyzer:
    """
    网站性能分析器，用于分析网站的各种性能指标
    
    支持功能：
    - 页面加载时间分析
    - 资源大小分析（HTML、CSS、JS、图片等）
    - 页面响应时间分析
    - 性能指标评分
    - 性能优化建议
    """
    
    def __init__(self, timeout: int = 30, user_agent: Optional[str] = None):
        """
        初始化性能分析器
        
        Args:
            timeout: 请求超时时间（秒）
            user_agent: 自定义User-Agent
        """
        self.timeout = timeout
        self.user_agent = user_agent or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        self.session = self._create_session()
        
        # 性能评估的阈值（用于评分）
        self.performance_thresholds = {
            'page_load_time': {
                'excellent': 1.0,    # 秒
                'good': 2.0,        
                'fair': 3.0,        
                'poor': 5.0         # 超过5秒为差
            },
            'ttfb': {
                'excellent': 0.3,    # 秒
                'good': 0.5,
                'fair': 0.8,
                'poor': 1.5
            },
            'page_size': {
                'excellent': 500000,   # 500KB
                'good': 1000000,       # 1MB
                'fair': 2000000,       # 2MB
                'poor': 3000000        # 3MB
            },
            'requests_count': {
                'excellent': 20,
                'good': 50,
                'fair': 100,
                'poor': 150
            }
        }
    
    def _create_session(self) -> requests.Session:
        """创建并配置请求会话"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive'
        })
        return session
    
    def analyze_page_performance(self, url: str, analyze_resources: bool = False) -> Dict[str, Any]:
        """
        分析单个页面的性能
        
        Args:
            url: 要分析的页面URL
            analyze_resources: 是否分析页面资源（会增加分析时间）
            
        Returns:
            包含性能分析结果的字典
        """
        try:
            # 基础性能分析
            base_metrics = self._measure_page_load_metrics(url)
            
            # 资源分析（如果需要）
            resources = {}
            if analyze_resources:
                resources = self._analyze_page_resources(url, base_metrics['content'])
            
            # 计算性能评分
            scores = self._calculate_performance_scores(base_metrics, resources)
            
            # 生成优化建议
            suggestions = self._generate_optimization_suggestions(base_metrics, resources, scores)
            
            # 综合分析结果
            results = {
                'url': url,
                'load_time_metrics': base_metrics,
                'resources_analysis': resources,
                'performance_scores': scores,
                'optimization_suggestions': suggestions,
                'analysis_timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            logger.info(f"页面性能分析完成: {url}, 加载时间: {base_metrics['page_load_time']:.2f}秒")
            return results
            
        except RequestException as e:
            logger.error(f"请求失败: {url}, 错误: {str(e)}")
            return {
                'url': url,
                'error': f'请求错误: {str(e)}',
                'analysis_timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
        except Exception as e:
            logger.error(f"分析失败: {url}, 错误: {str(e)}")
            return {
                'url': url,
                'error': f'分析错误: {str(e)}',
                'analysis_timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
    
    def _measure_page_load_metrics(self, url: str) -> Dict[str, Any]:
        """
        测量页面加载的基本指标
        
        Args:
            url: 要测量的页面URL
            
        Returns:
            包含加载时间指标的字典
        """
        # 记录开始时间
        start_time = time.time()
        
        # 发送请求并测量TTFB
        request_start = time.time()
        response = self.session.get(url, timeout=self.timeout, stream=True)
        ttfb = time.time() - request_start
        
        # 读取响应内容
        content = response.content
        page_size = len(content)
        
        # 计算总加载时间
        page_load_time = time.time() - start_time
        
        # 解析响应头信息
        headers_size = len(str(response.headers))
        
        return {
            'url': url,
            'page_load_time': page_load_time,      # 总加载时间
            'ttfb': ttfb,                          # 首字节时间
            'status_code': response.status_code,
            'page_size': page_size,                # 页面大小（字节）
            'headers_size': headers_size,
            'content_type': response.headers.get('Content-Type', ''),
            'content_encoding': response.headers.get('Content-Encoding', ''),
            'content': content.decode('utf-8', errors='ignore')
        }
    
    def _analyze_page_resources(self, url: str, html_content: str) -> Dict[str, Any]:
        """
        分析页面资源（CSS、JS、图片等）
        
        Args:
            url: 页面URL
            html_content: HTML内容
            
        Returns:
            资源分析结果
        """
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        base_path = '/'.join(parsed_url.path.split('/')[:-1]) if '/' in parsed_url.path else ''
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 提取各种资源链接
        resources = {
            'css': self._extract_resources(soup, 'link', 'href', ['stylesheet']),
            'javascript': self._extract_resources(soup, 'script', 'src', []),
            'images': self._extract_resources(soup, 'img', 'src', []),
            'fonts': self._extract_resources(soup, 'link', 'href', ['font']),
            'other': self._extract_other_resources(soup)
        }
        
        # 计算资源数量
        total_resources = sum(len(res_list) for res_list in resources.values())
        
        # 估算资源大小（基于统计平均值）
        estimated_sizes = self._estimate_resources_sizes(resources)
        
        return {
            'total_resources': total_resources,
            'resources_by_type': {k: len(v) for k, v in resources.items()},
            'resource_urls': resources,
            'estimated_total_size': estimated_sizes['total'],
            'estimated_sizes_by_type': estimated_sizes['by_type'],
            'base_url': base_url,
            'has_large_images': self._check_for_large_images(soup),
            'has_inline_css': self._check_for_inline_css(soup),
            'has_inline_js': self._check_for_inline_javascript(soup)
        }
    
    def _extract_resources(self, soup: BeautifulSoup, tag: str, attr: str, rel_values: List[str]) -> List[str]:
        """从HTML中提取特定类型的资源链接"""
        resources = []
        elements = soup.find_all(tag)
        
        for element in elements:
            # 检查rel属性（如果指定）
            if rel_values and 'rel' in element.attrs:
                if not any(r in element['rel'] for r in rel_values):
                    continue
            
            # 获取资源链接
            if attr in element.attrs:
                resource_url = element[attr].strip()
                if resource_url:
                    resources.append(resource_url)
        
        return resources
    
    def _extract_other_resources(self, soup: BeautifulSoup) -> List[str]:
        """提取其他类型的资源"""
        other_resources = []
        
        # 查找可能的视频和音频资源
        media_tags = soup.find_all(['video', 'audio'])
        for tag in media_tags:
            if 'src' in tag.attrs:
                other_resources.append(tag['src'])
            
            # 检查source标签
            sources = tag.find_all('source')
            for source in sources:
                if 'src' in source.attrs:
                    other_resources.append(source['src'])
        
        # 查找iframe
        iframes = soup.find_all('iframe')
        for iframe in iframes:
            if 'src' in iframe.attrs:
                other_resources.append(iframe['src'])
        
        return other_resources
    
    def _estimate_resources_sizes(self, resources: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        估算资源大小（基于统计平均值）
        
        使用平均大小进行估算，实际应用中可以选择性地下载并测量
        """
        # 平均资源大小（字节）
        avg_sizes = {
            'css': 25 * 1024,         # 25KB
            'javascript': 100 * 1024,  # 100KB
            'images': 50 * 1024,       # 50KB
            'fonts': 30 * 1024,        # 30KB
            'other': 150 * 1024        # 150KB
        }
        
        by_type = {}
        total = 0
        
        for res_type, urls in resources.items():
            count = len(urls)
            size = count * avg_sizes.get(res_type, 50 * 1024)
            by_type[res_type] = size
            total += size
        
        return {
            'total': total,
            'by_type': by_type
        }
    
    def _check_for_large_images(self, soup: BeautifulSoup) -> bool:
        """检查页面是否包含可能较大的图片"""
        images = soup.find_all('img')
        for img in images:
            # 检查尺寸属性
            width = img.get('width', '')
            height = img.get('height', '')
            
            # 检查是否有大图（粗略判断）
            try:
                if width and int(width) > 1200:
                    return True
                if height and int(height) > 800:
                    return True
            except ValueError:
                pass
            
            # 检查文件名中是否有large、big等关键词
            src = img.get('src', '')
            if any(keyword in src.lower() for keyword in ['large', 'big', 'full', 'original']):
                return True
        
        return False
    
    def _check_for_inline_css(self, soup: BeautifulSoup) -> bool:
        """检查页面是否包含大量内联CSS"""
        # 查找style标签
        style_tags = soup.find_all('style')
        total_css_size = sum(len(tag.string or '') for tag in style_tags)
        
        # 查找内联style属性
        inline_styles = soup.find_all(style=True)
        inline_style_size = sum(len(elem['style']) for elem in inline_styles)
        
        # 如果内联CSS超过10KB，则认为是大量内联CSS
        return (total_css_size + inline_style_size) > 10 * 1024
    
    def _check_for_inline_javascript(self, soup: BeautifulSoup) -> bool:
        """检查页面是否包含大量内联JavaScript"""
        # 查找不含src属性的script标签（内联脚本）
        inline_scripts = soup.find_all('script', src=False)
        total_js_size = sum(len(script.string or '') for script in inline_scripts)
        
        # 如果内联JS超过20KB，则认为是大量内联JavaScript
        return total_js_size > 20 * 1024
    
    def _calculate_performance_scores(self, metrics: Dict[str, Any], resources: Dict[str, Any]) -> Dict[str, float]:
        """
        计算性能评分（0-100分）
        
        Args:
            metrics: 页面加载指标
            resources: 资源分析结果
            
        Returns:
            各维度的性能评分
        """
        # 页面加载时间评分（权重40%）
        load_time_score = self._calculate_metric_score(
            metrics['page_load_time'],
            self.performance_thresholds['page_load_time']
        )
        
        # TTFB评分（权重20%）
        ttfb_score = self._calculate_metric_score(
            metrics['ttfb'],
            self.performance_thresholds['ttfb']
        )
        
        # 页面大小评分（权重20%）
        page_size = metrics['page_size'] + (resources.get('estimated_total_size', 0) if resources else 0)
        page_size_score = self._calculate_metric_score(
            page_size,
            self.performance_thresholds['page_size']
        )
        
        # 请求数量评分（权重20%）
        requests_count = resources.get('total_resources', 0) + 1  # +1 为HTML页面本身
        requests_score = self._calculate_metric_score(
            requests_count,
            self.performance_thresholds['requests_count']
        )
        
        # 计算加权总分
        weighted_total = (
            load_time_score * 0.4 +
            ttfb_score * 0.2 +
            page_size_score * 0.2 +
            requests_score * 0.2
        )
        
        return {
            'load_time_score': load_time_score,
            'ttfb_score': ttfb_score,
            'page_size_score': page_size_score,
            'requests_count_score': requests_score,
            'weighted_total': weighted_total
        }
    
    def _calculate_metric_score(self, value: float, thresholds: Dict[str, float]) -> float:
        """
        根据指标值和阈值计算分数
        
        Args:
            value: 指标实际值
            thresholds: 评分阈值
            
        Returns:
            0-100的分数
        """
        if value <= thresholds['excellent']:
            return 100.0
        elif value <= thresholds['good']:
            # 从100分到80分
            range_size = thresholds['good'] - thresholds['excellent']
            value_diff = value - thresholds['excellent']
            return 100.0 - (value_diff / range_size) * 20.0
        elif value <= thresholds['fair']:
            # 从80分到60分
            range_size = thresholds['fair'] - thresholds['good']
            value_diff = value - thresholds['good']
            return 80.0 - (value_diff / range_size) * 20.0
        elif value <= thresholds['poor']:
            # 从60分到40分
            range_size = thresholds['poor'] - thresholds['fair']
            value_diff = value - thresholds['fair']
            return 60.0 - (value_diff / range_size) * 20.0
        else:
            # 低于40分
            # 线性递减，每超过阈值1倍，分数减5分，但最低为0分
            excess_factor = value / thresholds['poor']
            score = 40.0 - (excess_factor - 1.0) * 5.0
            return max(0.0, score)
    
    def _generate_optimization_suggestions(self, metrics: Dict[str, Any], 
                                          resources: Dict[str, Any], 
                                          scores: Dict[str, float]) -> List[str]:
        """
        根据性能分析结果生成优化建议
        
        Args:
            metrics: 页面加载指标
            resources: 资源分析结果
            scores: 性能评分
            
        Returns:
            优化建议列表
        """
        suggestions = []
        
        # 根据加载时间生成建议
        if scores['load_time_score'] < 60:
            suggestions.append('优化页面加载时间，考虑服务器响应速度、内容压缩和资源加载优先级')
        
        # 根据TTFB生成建议
        if scores['ttfb_score'] < 60:
            suggestions.append('优化服务器响应时间，考虑使用CDN、服务器缓存和数据库优化')
        
        # 根据页面大小生成建议
        if scores['page_size_score'] < 60:
            suggestions.append('减小页面大小，压缩HTML、CSS和JavaScript，优化图片')
        
        # 根据请求数量生成建议
        if scores['requests_count_score'] < 60:
            suggestions.append('减少HTTP请求数量，合并CSS和JavaScript文件，使用CSS Sprites')
        
        # 针对资源的具体建议
        if resources:
            # 图片优化建议
            if resources.get('resources_by_type', {}).get('images', 0) > 20:
                suggestions.append('优化图片资源，考虑使用现代格式（WebP）、懒加载和响应式图片')
            
            if resources.get('has_large_images', False):
                suggestions.append('检查并优化大尺寸图片，考虑使用适当的尺寸和压缩')
            
            # 内联资源建议
            if resources.get('has_inline_css', False):
                suggestions.append('避免大量内联CSS，将样式移至外部样式表')
            
            if resources.get('has_inline_js', False):
                suggestions.append('避免大量内联JavaScript，将脚本移至外部文件')
        
        # 通用建议
        if metrics['content_encoding'] != 'gzip' and metrics['content_encoding'] != 'br':
            suggestions.append('启用Gzip或Brotli压缩，减小传输数据大小')
        
        # 分数较低时添加更多建议
        if scores['weighted_total'] < 50:
            suggestions.extend([
                '考虑实施前端性能优化技术，如代码分割、资源预加载和缓存策略',
                '检查第三方脚本对页面性能的影响，考虑延迟加载非关键脚本'
            ])
        
        return suggestions
    
    def analyze_multiple_pages(self, urls: List[str], analyze_resources: bool = False) -> Dict[str, Any]:
        """
        分析多个页面的性能并计算平均值
        
        Args:
            urls: 要分析的页面URL列表
            analyze_resources: 是否分析页面资源
            
        Returns:
            综合分析结果
        """
        results = []
        successful_analyses = 0
        failed_analyses = 0
        
        # 分析每个页面
        for url in urls:
            page_result = self.analyze_page_performance(url, analyze_resources)
            results.append(page_result)
            
            if 'error' not in page_result:
                successful_analyses += 1
            else:
                failed_analyses += 1
        
        # 计算平均性能指标
        avg_metrics = self._calculate_average_metrics(results)
        
        return {
            'total_pages_analyzed': len(urls),
            'successful_analyses': successful_analyses,
            'failed_analyses': failed_analyses,
            'page_results': results,
            'average_metrics': avg_metrics,
            'overall_performance_score': avg_metrics.get('average_weighted_score', 0),
            'analysis_timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def _calculate_average_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        计算多个页面的平均性能指标
        
        Args:
            results: 页面分析结果列表
            
        Returns:
            平均性能指标
        """
        valid_results = [r for r in results if 'error' not in r]
        
        if not valid_results:
            return {}
        
        # 收集各项指标
        load_times = [r['load_time_metrics']['page_load_time'] for r in valid_results]
        ttfb_values = [r['load_time_metrics']['ttfb'] for r in valid_results]
        page_sizes = [r['load_time_metrics']['page_size'] for r in valid_results]
        weighted_scores = [r['performance_scores']['weighted_total'] for r in valid_results]
        
        return {
            'average_load_time': statistics.mean(load_times),
            'median_load_time': statistics.median(load_times),
            'average_ttfb': statistics.mean(ttfb_values),
            'median_ttfb': statistics.median(ttfb_values),
            'average_page_size': statistics.mean(page_sizes),
            'median_page_size': statistics.median(page_sizes),
            'average_weighted_score': statistics.mean(weighted_scores),
            'median_weighted_score': statistics.median(weighted_scores),
            'best_page_score': max(weighted_scores),
            'worst_page_score': min(weighted_scores)
        }
    
    def get_performance_grade(self, score: float) -> str:
        """
        根据性能分数返回等级
        
        Args:
            score: 性能分数（0-100）
            
        Returns:
            性能等级
        """
        if score >= 90:
            return '优秀'
        elif score >= 75:
            return '良好'
        elif score >= 60:
            return '一般'
        elif score >= 40:
            return '较差'
        else:
            return '差'


def get_performance_analyzer(timeout: int = 30, user_agent: Optional[str] = None) -> PerformanceAnalyzer:
    """
    获取性能分析器实例的工厂函数
    
    Args:
        timeout: 请求超时时间（秒）
        user_agent: 自定义User-Agent
        
    Returns:
        PerformanceAnalyzer实例
    """
    return PerformanceAnalyzer(timeout=timeout, user_agent=user_agent)


if __name__ == '__main__':
    # 简单示例
    analyzer = PerformanceAnalyzer()
    result = analyzer.analyze_page_performance('https://www.example.com', analyze_resources=True)
    print(f"页面加载时间: {result['load_time_metrics']['page_load_time']:.2f}秒")
    print(f"性能评分: {result['performance_scores']['weighted_total']:.1f}/100")
    print(f"优化建议: {', '.join(result['optimization_suggestions'][:3])}")