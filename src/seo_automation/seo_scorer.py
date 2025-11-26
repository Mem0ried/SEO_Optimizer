from typing import Dict, List, Tuple
import logging

from ..config.default_config import SEO_CONFIG, SCORE_WEIGHTS

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SEOScorer:
    """SEO评分器，用于评估网站的SEO质量"""
    
    def __init__(self):
        self.scores = {
            'content': 0.0,      # 内容质量得分
            'keywords': 0.0,     # 关键词优化得分
            'meta_tags': 0.0,    # 元标签得分
            'performance': 0.0,  # 性能得分
            'technical': 0.0     # 技术SEO得分
        }
        self.weighted_scores = {}
        self.overall_score = 0.0
        self.detailed_analysis = {}
    
    def score_page(self, page_data: Dict, keyword_analysis: Dict = None) -> Dict:
        """对单个页面进行SEO评分"""
        page_scores = {
            'url': page_data.get('url', ''),
            'scores': {
                'content': 0.0,
                'keywords': 0.0,
                'meta_tags': 0.0,
                'performance': 0.0,
                'technical': 0.0
            },
            'overall_score': 0.0,
            'detailed_analysis': {},
            'improvement_suggestions': []
        }
        
        # 评分各项指标
        page_scores['scores']['content'] = self._score_content(page_data)
        page_scores['detailed_analysis']['content'] = self.detailed_analysis.get('content', {})
        
        if keyword_analysis:
            page_scores['scores']['keywords'] = self._score_keywords(page_data, keyword_analysis)
            page_scores['detailed_analysis']['keywords'] = self.detailed_analysis.get('keywords', {})
        
        page_scores['scores']['meta_tags'] = self._score_meta_tags(page_data)
        page_scores['detailed_analysis']['meta_tags'] = self.detailed_analysis.get('meta_tags', {})
        
        page_scores['scores']['performance'] = self._score_performance(page_data)
        page_scores['detailed_analysis']['performance'] = self.detailed_analysis.get('performance', {})
        
        page_scores['scores']['technical'] = self._score_technical(page_data)
        page_scores['detailed_analysis']['technical'] = self.detailed_analysis.get('technical', {})
        
        # 计算加权总分
        page_scores['overall_score'] = self._calculate_weighted_score(page_scores['scores'])
        
        # 生成改进建议
        page_scores['improvement_suggestions'] = self._generate_improvement_suggestions(
            page_data, keyword_analysis, page_scores['scores']
        )
        
        return page_scores
    
    def score_multiple_pages(self, pages_data: Dict[str, Dict], keyword_results: Dict) -> Dict:
        """对多个页面进行SEO评分，并计算整体得分"""
        results = {
            'page_scores': {},
            'overall_scores': {
                'content': 0.0,
                'keywords': 0.0,
                'meta_tags': 0.0,
                'performance': 0.0,
                'technical': 0.0,
                'weighted_total': 0.0
            },
            'site_analysis': {},
            'overall_suggestions': []
        }
        
        # 对每个页面评分
        valid_pages = 0
        category_scores = {
            'content': [],
            'keywords': [],
            'meta_tags': [],
            'performance': [],
            'technical': []
        }
        
        for url, page_data in pages_data.items():
            # 跳过错误页面
            if 'error' in page_data:
                continue
            
            # 获取该页面的关键词分析结果
            page_keyword_analysis = keyword_results['page_analyses'].get(url, {})
            
            # 评分
            page_score = self.score_page(page_data, page_keyword_analysis)
            results['page_scores'][url] = page_score
            
            # 收集各类别得分
            for category, score in page_score['scores'].items():
                category_scores[category].append(score)
            
            valid_pages += 1
        
        # 计算平均得分
        if valid_pages > 0:
            for category, scores in category_scores.items():
                if scores:  # 避免空列表
                    results['overall_scores'][category] = sum(scores) / len(scores)
            
            # 计算加权总分
            results['overall_scores']['weighted_total'] = self._calculate_weighted_score(results['overall_scores'])
        
        # 生成网站整体分析
        results['site_analysis'] = self._generate_site_analysis(pages_data, keyword_results, results['overall_scores'])
        
        # 生成整体建议
        results['overall_suggestions'] = self._generate_overall_suggestions(
            pages_data, keyword_results, results['overall_scores']
        )
        
        return results
    
    def _score_content(self, page_data: Dict) -> float:
        """评估内容质量"""
        self.detailed_analysis['content'] = {}
        score = 0.0
        max_score = 100
        
        # 内容长度评分 (30分)
        content_length = page_data.get('content_length', 0)
        min_length = SEO_CONFIG['MIN_CONTENT_LENGTH']
        
        if content_length >= min_length * 2:  # 超过最小长度的2倍
            length_score = 30
        elif content_length >= min_length:
            length_score = 20 + (content_length - min_length) / min_length * 10
        elif content_length >= min_length * 0.5:
            length_score = 10 + (content_length - min_length * 0.5) / (min_length * 0.5) * 10
        else:
            length_score = (content_length / (min_length * 0.5)) * 10
        
        self.detailed_analysis['content']['length'] = {
            'score': length_score,
            'actual': content_length,
            'min_recommended': min_length
        }
        
        # 标题评分 (20分)
        title = page_data.get('title', '')
        if len(title) > 0:
            if 50 <= len(title) <= 60:  # 理想标题长度
                title_score = 20
            elif 30 <= len(title) < 50 or 60 < len(title) <= 70:
                title_score = 15
            elif len(title) < 30:
                title_score = 10
            else:
                title_score = 5
        else:
            title_score = 0
        
        self.detailed_analysis['content']['title'] = {
            'score': title_score,
            'length': len(title),
            'ideal_length': '50-60 characters'
        }
        
        # 标题标签评分 (25分)
        headings = page_data.get('headings', {})
        heading_score = 0
        
        # 检查H1标签
        if headings.get('h1', []):
            h1_count = len(headings['h1'])
            if h1_count == 1:  # 一个H1标签是最佳实践
                heading_score += 10
            elif h1_count > 1:
                heading_score += 5
        
        # 检查标题层次结构
        has_h2 = bool(headings.get('h2', []))
        has_h3 = bool(headings.get('h3', []))
        
        if has_h2:
            heading_score += 8
        if has_h3 and has_h2:
            heading_score += 7
        
        self.detailed_analysis['content']['headings'] = {
            'score': heading_score,
            'h1_count': len(headings.get('h1', [])),
            'has_h2': has_h2,
            'has_h3': has_h3
        }
        
        # 图片alt属性评分 (25分)
        images = page_data.get('images', [])
        if images:
            images_with_alt = sum(1 for img in images if img.get('alt', '').strip())
            alt_ratio = images_with_alt / len(images)
            
            if alt_ratio >= SEO_CONFIG['OPTIMAL_IMAGE_ALT_RATIO']:
                image_score = 25
            elif alt_ratio >= 0.5:
                image_score = 15 + (alt_ratio - 0.5) / 0.3 * 10
            else:
                image_score = alt_ratio * 30
        else:
            image_score = 25  # 如果没有图片，得满分
        
        self.detailed_analysis['content']['images'] = {
            'score': image_score,
            'total_images': len(images),
            'images_with_alt': images_with_alt if images else 0,
            'alt_ratio': alt_ratio if images else 1.0
        }
        
        # 计算总分
        score = length_score + title_score + heading_score + image_score
        
        # 确保分数在0-100之间
        return min(max(score, 0), max_score)
    
    def _score_keywords(self, page_data: Dict, keyword_analysis: Dict) -> float:
        """评估关键词优化情况"""
        self.detailed_analysis['keywords'] = {}
        score = 0.0
        max_score = 100
        
        # 关键词密度评分 (35分)
        density_score = 0
        keyword_densities = keyword_analysis.get('keyword_density', {})
        
        if keyword_densities:
            good_density_count = 0
            total_keywords = len(keyword_densities)
            min_density = SEO_CONFIG['OPTIMAL_KEYWORD_DENSITY']['min']
            max_density = SEO_CONFIG['OPTIMAL_KEYWORD_DENSITY']['max']
            
            for keyword, density in keyword_densities.items():
                if min_density <= density <= max_density:
                    good_density_count += 1
            
            density_ratio = good_density_count / total_keywords if total_keywords > 0 else 0
            density_score = density_ratio * 35
        
        self.detailed_analysis['keywords']['density'] = {
            'score': density_score,
            'optimal_range': f"{min_density}%-{max_density}%"
        }
        
        # 标题关键词评分 (25分)
        title_keyword_analysis = keyword_analysis.get('title_keyword_analysis', {})
        title_keyword_score = 0
        
        if title_keyword_analysis:
            keywords_in_title = sum(1 for analysis in title_keyword_analysis.values() 
                                  if analysis.get('present', False))
            early_in_title = sum(1 for analysis in title_keyword_analysis.values() 
                                if analysis.get('early_in_title', False))
            
            # 关键词在标题中的数量得分 (最多10分)
            if keywords_in_title > 0:
                count_score = min(keywords_in_title * 5, 10)
            else:
                count_score = 0
            
            # 关键词在标题前部的得分 (最多15分)
            if early_in_title > 0:
                early_score = min(early_in_title * 7.5, 15)
            else:
                early_score = 0
            
            title_keyword_score = count_score + early_score
        
        self.detailed_analysis['keywords']['title'] = {
            'score': title_keyword_score,
            'keywords_in_title': keywords_in_title if title_keyword_analysis else 0
        }
        
        # 标题标签关键词评分 (20分)
        heading_keyword_analysis = keyword_analysis.get('heading_keyword_analysis', {})
        heading_keyword_score = 0
        
        # 检查H1中的关键词
        if 'h1' in heading_keyword_analysis:
            h1_keywords = len(heading_keyword_analysis['h1'])
            heading_keyword_score += min(h1_keywords * 10, 10)
        
        # 检查H2-H3中的关键词
        for level in ['h2', 'h3']:
            if level in heading_keyword_analysis and heading_keyword_analysis[level]:
                heading_keyword_score += 5
        
        self.detailed_analysis['keywords']['headings'] = {
            'score': heading_keyword_score,
            'has_h1_keywords': 'h1' in heading_keyword_analysis and bool(heading_keyword_analysis['h1'])
        }
        
        # 内容中关键词位置评分 (20分)
        keyword_placement = keyword_analysis.get('keyword_placement', {})
        placement_score = 0
        
        if keyword_placement:
            keywords_with_good_placement = 0
            total_placements = len(keyword_placement)
            
            for keyword, placement in keyword_placement.items():
                if placement.get('in_early_content', False):
                    keywords_with_good_placement += 1
            
            placement_ratio = keywords_with_good_placement / total_placements if total_placements > 0 else 0
            placement_score = placement_ratio * 20
        
        self.detailed_analysis['keywords']['placement'] = {
            'score': placement_score
        }
        
        # 计算总分
        score = density_score + title_keyword_score + heading_keyword_score + placement_score
        
        return min(max(score, 0), max_score)
    
    def _score_meta_tags(self, page_data: Dict) -> float:
        """评估元标签"""
        self.detailed_analysis['meta_tags'] = {}
        score = 0.0
        max_score = 100
        
        # 标题标签评分 (40分)
        title = page_data.get('title', '')
        if title:
            if 50 <= len(title) <= 60:  # 理想长度
                title_score = 40
            elif 30 <= len(title) < 50 or 60 < len(title) <= 70:
                title_score = 30
            elif len(title) < 30:
                title_score = 20
            else:
                title_score = 10
        else:
            title_score = 0
        
        self.detailed_analysis['meta_tags']['title'] = {
            'score': title_score,
            'present': bool(title),
            'length': len(title)
        }
        
        # 元描述评分 (30分)
        meta_description = page_data.get('meta_description', '')
        if meta_description:
            if 120 <= len(meta_description) <= 160:  # 理想长度
                description_score = 30
            elif 80 <= len(meta_description) < 120 or 160 < len(meta_description) <= 200:
                description_score = 20
            elif len(meta_description) < 80:
                description_score = 10
            else:
                description_score = 5
        else:
            description_score = 0
        
        self.detailed_analysis['meta_tags']['description'] = {
            'score': description_score,
            'present': bool(meta_description),
            'length': len(meta_description)
        }
        
        # 元关键词评分 (15分)
        meta_keywords = page_data.get('meta_keywords', '')
        if meta_keywords:
            # 检查关键词数量
            keywords = [kw.strip() for kw in meta_keywords.split(',') if kw.strip()]
            if 5 <= len(keywords) <= 10:  # 理想数量
                keywords_score = 15
            elif 3 <= len(keywords) < 5 or 10 < len(keywords) <= 15:
                keywords_score = 10
            else:
                keywords_score = 5
        else:
            keywords_score = 5  # 现代搜索引擎不那么重视元关键词，所以给一点基础分
        
        self.detailed_analysis['meta_tags']['keywords'] = {
            'score': keywords_score,
            'present': bool(meta_keywords)
        }
        
        # 其他技术元标签评分 (15分)
        # 这里可以检查其他重要的meta标签，如viewport等
        # 由于我们的爬虫没有提取这些，这里给一个默认分数
        technical_meta_score = 10  # 基础分
        
        self.detailed_analysis['meta_tags']['technical'] = {
            'score': technical_meta_score
        }
        
        # 计算总分
        score = title_score + description_score + keywords_score + technical_meta_score
        
        return min(max(score, 0), max_score)
    
    def _score_performance(self, page_data: Dict) -> float:
        """评估性能相关指标"""
        self.detailed_analysis['performance'] = {}
        score = 0.0
        max_score = 100
        
        # 响应时间评分 (40分)
        response_time = page_data.get('response_time', 5.0)  # 默认5秒
        if response_time < 1:
            response_score = 40
        elif response_time < 2:
            response_score = 35
        elif response_time < 3:
            response_score = 30
        elif response_time < 4:
            response_score = 20
        elif response_time < 5:
            response_score = 10
        else:
            response_score = 0
        
        self.detailed_analysis['performance']['response_time'] = {
            'score': response_score,
            'actual': response_time,
            'unit': 'seconds'
        }
        
        # 状态码评分 (30分)
        status_code = page_data.get('status_code', 500)
        if status_code == 200:
            status_score = 30
        elif status_code == 301 or status_code == 302:
            status_score = 15
        else:
            status_score = 0
        
        self.detailed_analysis['performance']['status_code'] = {
            'score': status_score,
            'actual': status_code
        }
        
        # 内容大小评分 (30分)
        # 注意：我们只有文本内容长度，没有完整的页面大小
        content_length = page_data.get('content_length', 0)
        # 假设文本内容长度与页面大小有一定相关性
        if content_length < 10000:  # 小于10KB的文本内容
            size_score = 30
        elif content_length < 20000:
            size_score = 25
        elif content_length < 50000:
            size_score = 20
        else:
            size_score = 10
        
        self.detailed_analysis['performance']['content_size'] = {
            'score': size_score,
            'actual': content_length,
            'unit': 'characters'
        }
        
        # 计算总分
        score = response_score + status_score + size_score
        
        return min(max(score, 0), max_score)
    
    def _score_technical(self, page_data: Dict) -> float:
        """评估技术SEO指标"""
        self.detailed_analysis['technical'] = {}
        score = 0.0
        max_score = 100
        
        # URL结构评分 (25分)
        url = page_data.get('url', '')
        url_score = 0
        
        # 检查URL长度
        if len(url) < 100:
            url_score += 10
        elif len(url) < 150:
            url_score += 5
        
        # 检查URL是否包含关键词（简单检查，不做严格匹配）
        content = page_data.get('content', '').lower()
        url_lower = url.lower()
        
        # 检查URL是否友好（不含特殊字符，使用连字符）
        unfriendly_chars = ['&', '=', '+', '%', '$', '#', '@']
        has_unfriendly = any(char in url for char in unfriendly_chars)
        
        if not has_unfriendly:
            url_score += 10
        
        # 检查URL是否以/结尾
        if url.endswith('/'):
            url_score += 5
        
        self.detailed_analysis['technical']['url_structure'] = {
            'score': url_score,
            'length': len(url)
        }
        
        # 内部链接评分 (30分)
        links = page_data.get('links', [])
        if links:
            # 检查是否有内部链接
            internal_links = len(links)
            if internal_links >= 10:
                links_score = 30
            elif internal_links >= 5:
                links_score = 20
            elif internal_links >= 1:
                links_score = 10
            else:
                links_score = 0
        else:
            links_score = 0
        
        self.detailed_analysis['technical']['internal_links'] = {
            'score': links_score,
            'count': len(links)
        }
        
        # 图片优化评分 (25分)
        images = page_data.get('images', [])
        if images:
            # 检查alt属性覆盖率
            images_with_alt = sum(1 for img in images if img.get('alt', '').strip())
            alt_coverage = images_with_alt / len(images)
            
            if alt_coverage >= 0.9:
                images_score = 25
            elif alt_coverage >= 0.7:
                images_score = 20
            elif alt_coverage >= 0.5:
                images_score = 15
            else:
                images_score = 10
        else:
            images_score = 25  # 没有图片得满分
        
        self.detailed_analysis['technical']['images'] = {
            'score': images_score,
            'total_images': len(images),
            'alt_coverage': alt_coverage if images else 1.0
        }
        
        # 移动友好性基础评分 (20分)
        # 由于我们没有实际检测移动友好性，给一个基础分
        # 完整实现应该使用移动检测库或API
        mobile_score = 10  # 基础分
        
        # 简单检查内容是否可能对移动设备友好
        content_length = page_data.get('content_length', 0)
        if content_length < 50000:  # 内容不过长
            mobile_score += 5
        
        if len(url) < 100:  # URL不太长
            mobile_score += 5
        
        self.detailed_analysis['technical']['mobile_friendly'] = {
            'score': mobile_score
        }
        
        # 计算总分
        score = url_score + links_score + images_score + mobile_score
        
        return min(max(score, 0), max_score)
    
    def _calculate_weighted_score(self, scores: Dict) -> float:
        """根据权重计算加权总分"""
        weighted_score = 0.0
        total_weight = sum(SCORE_WEIGHTS.values())
        
        for category, weight in SCORE_WEIGHTS.items():
            if category in scores:
                weighted_score += scores[category] * (weight / total_weight)
        
        return weighted_score
    
    def _generate_improvement_suggestions(self, page_data: Dict, keyword_analysis: Dict, scores: Dict) -> List[str]:
        """生成页面级别的改进建议"""
        suggestions = []
        
        # 基于内容得分的建议
        if scores['content'] < 70:
            content_analysis = self.detailed_analysis.get('content', {})
            
            # 内容长度建议
            if content_analysis.get('length', {}).get('score', 0) < 20:
                min_length = SEO_CONFIG['MIN_CONTENT_LENGTH']
                current_length = page_data.get('content_length', 0)
                suggestions.append(f"增加页面内容长度，建议至少达到{min_length}个字符（当前约{current_length}个字符）")
            
            # 标题建议
            if content_analysis.get('title', {}).get('score', 0) < 15:
                title_length = len(page_data.get('title', ''))
                if title_length < 30:
                    suggestions.append("扩展页面标题，建议长度在50-60个字符之间")
                elif title_length > 70:
                    suggestions.append("缩短页面标题，建议长度在50-60个字符之间")
            
            # 标题标签建议
            if content_analysis.get('headings', {}).get('score', 0) < 15:
                h1_count = len(page_data.get('headings', {}).get('h1', []))
                if h1_count == 0:
                    suggestions.append("添加H1标题标签，每个页面应该有一个主标题")
                elif h1_count > 1:
                    suggestions.append("减少H1标题标签数量，每个页面最好只有一个主标题")
                
                if not page_data.get('headings', {}).get('h2', []):
                    suggestions.append("添加H2副标题，使内容结构更清晰")
        
        # 基于关键词得分的建议
        if keyword_analysis and scores['keywords'] < 70:
            # 这里可以从keyword_analysis中提取更具体的建议
            if keyword_analysis.get('keyword_recommendations', []):
                suggestions.extend(keyword_analysis['keyword_recommendations'][:3])
        
        # 基于元标签得分的建议
        if scores['meta_tags'] < 70:
            if not page_data.get('title', ''):
                suggestions.append("添加标题标签(title)")
            
            if not page_data.get('meta_description', ''):
                suggestions.append("添加元描述标签(meta description)")
        
        # 基于性能得分的建议
        if scores['performance'] < 70:
            performance_analysis = self.detailed_analysis.get('performance', {})
            
            if performance_analysis.get('response_time', {}).get('score', 0) < 20:
                response_time = page_data.get('response_time', 0)
                suggestions.append(f"优化页面加载速度，当前响应时间为{response_time:.2f}秒，建议控制在3秒以内")
        
        # 基于技术得分的建议
        if scores['technical'] < 70:
            technical_analysis = self.detailed_analysis.get('technical', {})
            
            # 图片优化建议
            if technical_analysis.get('images', {}).get('score', 0) < 15:
                images = page_data.get('images', [])
                if images:
                    images_with_alt = sum(1 for img in images if img.get('alt', '').strip())
                    suggestions.append(f"为更多图片添加alt属性，当前覆盖率为{(images_with_alt/len(images)*100):.1f}%")
        
        return suggestions[:5]  # 限制建议数量
    
    def _generate_site_analysis(self, pages_data: Dict, keyword_results: Dict, scores: Dict) -> Dict:
        """生成网站整体分析"""
        analysis = {
            'total_pages': len(pages_data),
            'category_scores': {},
            'strengths': [],
            'weaknesses': []
        }
        
        # 复制类别得分
        for category in ['content', 'keywords', 'meta_tags', 'performance', 'technical']:
            analysis['category_scores'][category] = scores.get(category, 0)
        
        # 找出优势和劣势
        for category, score in scores.items():
            if category != 'weighted_total':
                if score >= 80:
                    analysis['strengths'].append(f"{self._get_category_name(category)} (得分: {score:.1f})")
                elif score < 60:
                    analysis['weaknesses'].append(f"{self._get_category_name(category)} (得分: {score:.1f})")
        
        # 添加整体评价
        overall_score = scores.get('weighted_total', 0)
        if overall_score >= 90:
            analysis['overall_rating'] = "优秀"
            analysis['overall_comment'] = "您的网站SEO状况非常好，继续保持！"
        elif overall_score >= 80:
            analysis['overall_rating'] = "良好"
            analysis['overall_comment'] = "您的网站SEO状况良好，有小部分可以优化的空间。"
        elif overall_score >= 70:
            analysis['overall_rating'] = "一般"
            analysis['overall_comment'] = "您的网站SEO状况一般，有较大的优化空间。"
        elif overall_score >= 60:
            analysis['overall_rating'] = "较差"
            analysis['overall_comment'] = "您的网站SEO状况较差，建议进行全面优化。"
        else:
            analysis['overall_rating'] = "很差"
            analysis['overall_comment'] = "您的网站SEO状况很差，需要立即进行全面优化。"
        
        return analysis
    
    def _generate_overall_suggestions(self, pages_data: Dict, keyword_results: Dict, scores: Dict) -> List[str]:
        """生成网站整体改进建议"""
        suggestions = []
        
        # 基于类别得分的建议
        for category, score in scores.items():
            if category == 'weighted_total':
                continue
                
            if score < 60:
                if category == 'content':
                    suggestions.append("提高网站内容质量，增加内容长度，优化标题结构，为图片添加alt属性")
                elif category == 'keywords':
                    suggestions.append("优化关键词策略，确保关键词密度在合理范围，在标题和内容中正确放置关键词")
                elif category == 'meta_tags':
                    suggestions.append("完善所有页面的元标签，包括title、meta description等")
                elif category == 'performance':
                    suggestions.append("优化网站加载速度，减少页面大小，提高服务器响应时间")
                elif category == 'technical':
                    suggestions.append("改进技术SEO，优化URL结构，增加内部链接，确保移动友好性")
        
        # 从关键词分析中提取建议
        if keyword_results.get('overall_recommendations', []):
            suggestions.extend(keyword_results['overall_recommendations'][:2])
        
        # 添加一些通用建议
        if len(suggestions) < 5:
            common_suggestions = [
                "定期更新网站内容，保持内容的新鲜度",
                "增加高质量的外部链接指向您的网站",
                "确保网站在移动设备上有良好的显示效果",
                "使用Google Analytics等工具监控网站性能",
                "创建XML站点地图，帮助搜索引擎更好地索引您的网站"
            ]
            
            for suggestion in common_suggestions:
                if suggestion not in suggestions and len(suggestions) < 5:
                    suggestions.append(suggestion)
        
        return suggestions
    
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


def get_seo_scorer() -> SEOScorer:
    """工厂函数，返回SEO评分器实例"""
    return SEOScorer()