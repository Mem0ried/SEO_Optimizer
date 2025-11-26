import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.probability import FreqDist
from collections import Counter, defaultdict
import string
import re
from typing import Dict, List, Set, Tuple, Optional
import logging

from ..config.default_config import SEO_CONFIG, NLTK_CONFIG

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class KeywordAnalyzer:
    """关键词分析器，用于提取和分析网页中的关键词"""
    
    def __init__(self):
        self._download_nltk_resources()
        self.stop_words = set(stopwords.words('english'))  # 默认使用英文停用词
        # 添加中文停用词支持
        try:
            self.chinese_stop_words = set(stopwords.words('chinese'))
        except:
            self.chinese_stop_words = set()
            logger.warning('Chinese stopwords not available')
        
        # 扩展停用词列表
        self.extended_stop_words = {
            'a', 'an', 'the', 'and', 'or', 'but', 'if', 'because', 'as', 'what',
            'when', 'where', 'how', 'who', 'which', 'this', 'that', 'these', 'those',
            'then', 'just', 'so', 'than', 'such', 'both', 'through', 'about', 'for',
            'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'having',
            'do', 'does', 'did', 'doing',
            'to', 'from', 'by', 'on', 'in', 'at', 'with', 'of', 'off', 'out',
            'up', 'down', 'over', 'under', 'above', 'below',
            'com', 'www', 'http', 'https', 'html', 'php', 'asp', 'aspx', 'jsp',
            'net', 'org', 'edu', 'gov', 'co', 'uk', 'cn'
        }
        
        self.all_stop_words = self.stop_words.union(self.extended_stop_words).union(self.chinese_stop_words)
    
    def _download_nltk_resources(self):
        """下载NLTK所需资源"""
        try:
            for package in NLTK_CONFIG['DOWNLOAD_PACKAGES']:
                nltk.download(package, quiet=True)
        except Exception as e:
            logger.error(f'Error downloading NLTK resources: {str(e)}')
    
    def _preprocess_text(self, text: str) -> List[str]:
        """预处理文本，包括分词、去除停用词等"""
        if not text or not isinstance(text, str):
            return []
        
        # 转换为小写
        text = text.lower()
        
        # 移除特殊字符和数字（保留中文和英文单词）
        text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z\s]', ' ', text)
        
        # 分词
        tokens = word_tokenize(text)
        
        # 移除停用词、标点和短词
        processed_tokens = [
            token for token in tokens 
            if token not in self.all_stop_words 
            and token not in string.punctuation
            and len(token) > 1
        ]
        
        return processed_tokens
    
    def extract_keywords(self, text: str, top_n: int = 20) -> List[Tuple[str, int]]:
        """从文本中提取关键词，返回(top_n)个最常见的关键词及其频率"""
        tokens = self._preprocess_text(text)
        
        # 计算词频
        freq_dist = FreqDist(tokens)
        
        # 返回最常见的关键词
        return freq_dist.most_common(top_n)
    
    def calculate_keyword_density(self, text: str, keywords: List[str]) -> Dict[str, float]:
        """计算指定关键词在文本中的密度（百分比）"""
        if not text or not keywords:
            return {}
        
        # 预处理文本
        tokens = self._preprocess_text(text)
        if not tokens:
            return {keyword: 0.0 for keyword in keywords}
        
        # 计算每个关键词的密度
        total_tokens = len(tokens)
        token_counter = Counter(tokens)
        
        density = {}
        for keyword in keywords:
            # 对于多词关键词，需要特殊处理
            if ' ' in keyword:
                # 原始文本中查找
                keyword_lower = keyword.lower()
                occurrences = text.lower().count(keyword_lower)
                # 粗略估计：将多词关键词视为一个词
                density[keyword] = (occurrences / (total_tokens + occurrences)) * 100 if total_tokens > 0 else 0.0
            else:
                # 单关键词直接从token中统计
                density[keyword] = (token_counter.get(keyword.lower(), 0) / total_tokens) * 100 if total_tokens > 0 else 0.0
        
        return density
    
    def analyze_page_keywords(self, page_data: Dict) -> Dict:
        """分析单个页面的关键词情况"""
        result = {
            'url': page_data.get('url', ''),
            'extracted_keywords': [],
            'keyword_density': {},
            'meta_keywords_present': False,
            'title_keyword_analysis': {},
            'heading_keyword_analysis': {},
            'keyword_placement': {},
            'keyword_recommendations': []
        }
        
        # 提取页面所有文本内容
        content = page_data.get('content', '')
        title = page_data.get('title', '')
        meta_description = page_data.get('meta_description', '')
        meta_keywords = page_data.get('meta_keywords', '')
        headings = page_data.get('headings', {})
        
        # 检查是否有元关键词
        result['meta_keywords_present'] = bool(meta_keywords)
        
        # 提取关键词
        all_text = ' '.join([content, title, meta_description])
        extracted_keywords = self.extract_keywords(all_text, top_n=15)
        result['extracted_keywords'] = extracted_keywords
        
        # 获取提取的关键词列表
        keywords_list = [kw[0] for kw in extracted_keywords[:10]]
        
        # 计算密度
        result['keyword_density'] = self.calculate_keyword_density(all_text, keywords_list)
        
        # 分析标题中的关键词
        if title:
            title_lower = title.lower()
            for keyword in keywords_list:
                keyword_lower = keyword.lower()
                if keyword_lower in title_lower:
                    result['title_keyword_analysis'][keyword] = {
                        'present': True,
                        'position': title_lower.find(keyword_lower),
                        'early_in_title': title_lower.find(keyword_lower) < len(title_lower) * 0.3
                    }
                else:
                    result['title_keyword_analysis'][keyword] = {'present': False}
        
        # 分析标题标签中的关键词
        for heading_level, heading_list in headings.items():
            result['heading_keyword_analysis'][heading_level] = {}
            for heading in heading_list:
                heading_lower = heading.lower()
                for keyword in keywords_list:
                    keyword_lower = keyword.lower()
                    if keyword_lower in heading_lower:
                        if keyword not in result['heading_keyword_analysis'][heading_level]:
                            result['heading_keyword_analysis'][heading_level][keyword] = {
                                'present': True,
                                'count': 1
                            }
                        else:
                            result['heading_keyword_analysis'][heading_level][keyword]['count'] += 1
        
        # 分析关键词位置（开头、中间、结尾）
        if content:
            content_lower = content.lower()
            content_length = len(content)
            third_length = content_length // 3
            
            for keyword in keywords_list:
                keyword_lower = keyword.lower()
                positions = []
                
                # 查找所有出现位置
                start = 0
                while True:
                    pos = content_lower.find(keyword_lower, start)
                    if pos == -1:
                        break
                    positions.append(pos)
                    start = pos + len(keyword_lower)
                
                if positions:
                    # 分类位置
                    in_early = any(pos < third_length for pos in positions)
                    in_middle = any(third_length <= pos < 2 * third_length for pos in positions)
                    in_end = any(pos >= 2 * third_length for pos in positions)
                    
                    result['keyword_placement'][keyword] = {
                        'total_occurrences': len(positions),
                        'in_early_content': in_early,
                        'in_middle_content': in_middle,
                        'in_end_content': in_end
                    }
        
        # 生成推荐
        self._generate_keyword_recommendations(result)
        
        return result
    
    def _generate_keyword_recommendations(self, analysis_result: Dict):
        """基于分析结果生成关键词优化建议"""
        recommendations = []
        
        # 检查元关键词
        if not analysis_result['meta_keywords_present']:
            recommendations.append("考虑添加meta关键词标签，列出页面主要关键词")
        
        # 检查关键词密度
        for keyword, density in analysis_result['keyword_density'].items():
            min_density = SEO_CONFIG['OPTIMAL_KEYWORD_DENSITY']['min']
            max_density = SEO_CONFIG['OPTIMAL_KEYWORD_DENSITY']['max']
            
            if density < min_density and density > 0:
                recommendations.append(f"关键词 '{keyword}' 的密度 ({density:.2f}%) 低于建议范围 ({min_density}-{max_density}%)，可以适当增加")
            elif density > max_density:
                recommendations.append(f"关键词 '{keyword}' 的密度 ({density:.2f}%) 高于建议范围 ({min_density}-{max_density}%)，可能存在关键词堆砌风险")
        
        # 检查标题中的关键词
        for keyword, analysis in analysis_result['title_keyword_analysis'].items():
            if not analysis['present'] and keyword in analysis_result['keyword_density'] and analysis_result['keyword_density'][keyword] > 0.5:
                recommendations.append(f"考虑在标题中包含关键词 '{keyword}'，这是内容中的重要关键词")
            elif analysis['present'] and not analysis.get('early_in_title', False):
                recommendations.append(f"考虑将关键词 '{keyword}' 放置在标题的前30%位置，以提高SEO效果")
        
        # 检查H1标签中的关键词
        if 'h1' in analysis_result['heading_keyword_analysis']:
            h1_analysis = analysis_result['heading_keyword_analysis']['h1']
            top_keywords = [kw[0] for kw in analysis_result['extracted_keywords'][:5]]
            for keyword in top_keywords:
                if keyword not in h1_analysis:
                    recommendations.append(f"考虑在H1标题中包含关键词 '{keyword}'")
        
        # 检查关键词在内容中的位置
        for keyword, placement in analysis_result.get('keyword_placement', {}).items():
            if not placement.get('in_early_content', False) and placement['total_occurrences'] > 0:
                recommendations.append(f"考虑在内容开头部分包含关键词 '{keyword}'，以提高相关性")
        
        analysis_result['keyword_recommendations'] = recommendations[:10]  # 限制建议数量
    
    def analyze_multiple_pages(self, pages_data: Dict[str, Dict]) -> Dict:
        """分析多个页面的关键词情况，找出整体趋势"""
        results = {
            'page_analyses': {},
            'common_keywords': {},
            'keyword_coverage': {},
            'overall_recommendations': []
        }
        
        # 分析每个页面
        all_keywords = Counter()
        keyword_pages = defaultdict(set)
        
        for url, page_data in pages_data.items():
            page_analysis = self.analyze_page_keywords(page_data)
            results['page_analyses'][url] = page_analysis
            
            # 收集所有关键词
            for keyword, freq in page_analysis['extracted_keywords']:
                all_keywords[keyword] += 1
                keyword_pages[keyword].add(url)
        
        # 找出常见关键词
        total_pages = len(pages_data)
        results['common_keywords'] = [
            (keyword, count) for keyword, count in all_keywords.most_common(20) 
            if count > 1  # 至少出现在2个页面
        ]
        
        # 计算关键词覆盖率
        for keyword, pages in keyword_pages.items():
            if len(pages) > 1:  # 至少出现在2个页面
                results['keyword_coverage'][keyword] = {
                    'pages': list(pages),
                    'coverage_percentage': (len(pages) / total_pages) * 100
                }
        
        # 生成整体建议
        self._generate_overall_recommendations(results, pages_data)
        
        return results
    
    def _generate_overall_recommendations(self, results: Dict, pages_data: Dict[str, Dict]):
        """生成整体关键词优化建议"""
        recommendations = []
        total_pages = len(pages_data)
        
        # 检查关键词一致性
        common_keywords = results['common_keywords']
        if len(common_keywords) < 5:
            recommendations.append("网站各页面的关键词缺乏一致性，建议确定核心关键词并在各相关页面保持一致")
        
        # 检查关键词覆盖率
        for keyword, coverage in results['keyword_coverage'].items():
            if coverage['coverage_percentage'] > 70:  # 超过70%的页面都有这个关键词
                recommendations.append(f"关键词 '{keyword}' 在 {coverage['coverage_percentage']:.1f}% 的页面中出现，可能存在过度使用的情况")
        
        # 检查每个页面的元关键词
        pages_without_meta = sum(1 for analysis in results['page_analyses'].values() 
                               if not analysis['meta_keywords_present'])
        if pages_without_meta > total_pages * 0.5:  # 超过50%的页面没有元关键词
            recommendations.append(f"超过50%的页面没有设置meta关键词标签，建议为重要页面添加相关关键词")
        
        # 检查标题优化情况
        pages_without_keywords_in_title = 0
        for analysis in results['page_analyses'].values():
            top_keywords = [kw[0] for kw in analysis['extracted_keywords'][:3]]
            has_top_keyword_in_title = any(analysis['title_keyword_analysis'].get(kw, {}).get('present', False) 
                                         for kw in top_keywords)
            if not has_top_keyword_in_title:
                pages_without_keywords_in_title += 1
        
        if pages_without_keywords_in_title > total_pages * 0.3:  # 超过30%的页面标题没有包含主要关键词
            recommendations.append(f"超过30%的页面标题没有包含主要关键词，建议优化这些页面的标题")
        
        results['overall_recommendations'] = recommendations


def get_keyword_analyzer() -> KeywordAnalyzer:
    """工厂函数，返回关键词分析器实例"""
    return KeywordAnalyzer()