import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Set, Optional
import logging

from ..config.default_config import CRAWL_CONFIG

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class WebCrawler:
    """网站爬虫基类，用于爬取网站内容"""
    
    def __init__(self, base_url: str, depth: int = CRAWL_CONFIG['DEFAULT_DEPTH'], 
                 max_pages: int = CRAWL_CONFIG['MAX_PAGES'], delay: int = CRAWL_CONFIG['DELAY']):
        self.base_url = base_url
        self.base_domain = urlparse(base_url).netloc
        self.depth = depth
        self.max_pages = max_pages
        self.delay = delay
        self.visited_urls: Set[str] = set()
        self.pages: Dict[str, Dict] = {}
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """创建请求会话"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': CRAWL_CONFIG['USER_AGENT'],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
        session.timeout = CRAWL_CONFIG['TIMEOUT']
        session.verify = True  # 验证SSL证书
        return session
    
    def _is_valid_url(self, url: str) -> bool:
        """检查URL是否有效且属于当前域名"""
        parsed = urlparse(url)
        # 确保URL有scheme和netloc
        if not parsed.scheme or not parsed.netloc:
            return False
        # 确保URL属于当前域名
        if parsed.netloc != self.base_domain and not parsed.netloc.endswith(f'.{self.base_domain}'):
            return False
        # 跳过特定文件类型
        ignore_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.zip', '.rar', '.exe']
        path_lower = parsed.path.lower()
        for ext in ignore_extensions:
            if path_lower.endswith(ext):
                return False
        return True
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """从页面中提取链接"""
        links = []
        for link_tag in soup.find_all('a', href=True):
            href = link_tag['href']
            absolute_url = urljoin(base_url, href)
            if self._is_valid_url(absolute_url):
                links.append(absolute_url)
        return links
    
    def _crawl_page(self, url: str, current_depth: int) -> None:
        """爬取单个页面"""
        if url in self.visited_urls or current_depth > self.depth or len(self.visited_urls) >= self.max_pages:
            return
        
        self.visited_urls.add(url)
        logger.info(f'Crawling: {url} (Depth: {current_depth}, Pages: {len(self.visited_urls)})')
        
        try:
            response = self.session.get(url, allow_redirects=CRAWL_CONFIG['FOLLOW_REDIRECTS'])
            response.raise_for_status()  # 抛出HTTP错误
            
            # 检查内容类型
            content_type = response.headers.get('Content-Type', '')
            if 'text/html' not in content_type:
                logger.warning(f'Skipping non-HTML content: {url}')
                return
            
            # 解析页面
            soup = BeautifulSoup(response.text, 'lxml')
            
            # 提取基本信息
            title = soup.title.string if soup.title else 'No Title'
            meta_description = ''
            meta_keywords = ''
            
            # 提取元描述
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                meta_description = meta_desc['content']
            
            # 提取元关键词
            meta_kw = soup.find('meta', attrs={'name': 'keywords'})
            if meta_kw and meta_kw.get('content'):
                meta_keywords = meta_kw['content']
            
            # 提取H1-H6标签
            headings = {}
            for level in range(1, 7):
                tag = f'h{level}'
                headings[tag] = [h.text.strip() for h in soup.find_all(tag)]
            
            # 提取正文内容（去除脚本和样式）
            for script in soup(['script', 'style']):
                script.decompose()
            text_content = soup.get_text(separator=' ', strip=True)
            
            # 提取所有链接
            all_links = self._extract_links(soup, url)
            
            # 提取图片信息
            images = []
            for img in soup.find_all('img'):
                img_info = {
                    'src': urljoin(url, img.get('src', '')),
                    'alt': img.get('alt', ''),
                    'title': img.get('title', '')
                }
                images.append(img_info)
            
            # 保存页面信息
            self.pages[url] = {
                'url': url,
                'title': title,
                'meta_description': meta_description,
                'meta_keywords': meta_keywords,
                'headings': headings,
                'content': text_content,
                'content_length': len(text_content),
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds(),
                'links': all_links,
                'images': images,
                'depth': current_depth
            }
            
            # 递归爬取下一层
            if current_depth < self.depth:
                time.sleep(self.delay)  # 避免爬取过快
                for link in all_links:
                    self._crawl_page(link, current_depth + 1)
                    if len(self.visited_urls) >= self.max_pages:
                        break
        
        except requests.RequestException as e:
            logger.error(f'Error crawling {url}: {str(e)}')
            # 记录失败的页面
            self.pages[url] = {
                'url': url,
                'error': str(e),
                'status_code': None,
                'depth': current_depth
            }
    
    def crawl(self) -> Dict[str, Dict]:
        """开始爬取网站"""
        logger.info(f'Starting crawl of {self.base_url} with depth {self.depth}')
        self._crawl_page(self.base_url, 0)
        logger.info(f'Crawl completed. Visited {len(self.visited_urls)} pages.')
        return self.pages


class ConcurrentWebCrawler(WebCrawler):
    """并发爬虫，使用多线程提高爬取速度"""
    
    def __init__(self, base_url: str, depth: int = CRAWL_CONFIG['DEFAULT_DEPTH'],
                 max_pages: int = CRAWL_CONFIG['MAX_PAGES'], delay: int = CRAWL_CONFIG['DELAY'],
                 max_workers: int = 5):
        super().__init__(base_url, depth, max_pages, delay)
        self.max_workers = max_workers
    
    def _process_page_concurrently(self, url: str, current_depth: int) -> None:
        """并发处理单个页面"""
        if url in self.visited_urls or current_depth > self.depth or len(self.visited_urls) >= self.max_pages:
            return
        
        with self._lock:
            if url in self.visited_urls:
                return
            self.visited_urls.add(url)
        
        # 调用父类的页面爬取方法
        try:
            response = self.session.get(url, allow_redirects=CRAWL_CONFIG['FOLLOW_REDIRECTS'])
            response.raise_for_status()
            
            content_type = response.headers.get('Content-Type', '')
            if 'text/html' not in content_type:
                return
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # 提取基本信息（与父类相同）
            title = soup.title.string if soup.title else 'No Title'
            meta_description = ''
            meta_keywords = ''
            
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                meta_description = meta_desc['content']
            
            meta_kw = soup.find('meta', attrs={'name': 'keywords'})
            if meta_kw and meta_kw.get('content'):
                meta_keywords = meta_kw['content']
            
            headings = {}
            for level in range(1, 7):
                tag = f'h{level}'
                headings[tag] = [h.text.strip() for h in soup.find_all(tag)]
            
            for script in soup(['script', 'style']):
                script.decompose()
            text_content = soup.get_text(separator=' ', strip=True)
            
            all_links = self._extract_links(soup, url)
            
            images = []
            for img in soup.find_all('img'):
                img_info = {
                    'src': urljoin(url, img.get('src', '')),
                    'alt': img.get('alt', ''),
                    'title': img.get('title', '')
                }
                images.append(img_info)
            
            # 保存页面信息
            self.pages[url] = {
                'url': url,
                'title': title,
                'meta_description': meta_description,
                'meta_keywords': meta_keywords,
                'headings': headings,
                'content': text_content,
                'content_length': len(text_content),
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds(),
                'links': all_links,
                'images': images,
                'depth': current_depth
            }
            
            # 如果深度未达到，添加到下一轮处理
            if current_depth < self.depth:
                for link in all_links:
                    if len(self.visited_urls) < self.max_pages:
                        self._next_level_links.append((link, current_depth + 1))
        
        except requests.RequestException as e:
            self.pages[url] = {
                'url': url,
                'error': str(e),
                'status_code': None,
                'depth': current_depth
            }
    
    def crawl(self) -> Dict[str, Dict]:
        """并发爬取网站"""
        import threading
        self._lock = threading.Lock()
        self._next_level_links = []
        
        logger.info(f'Starting concurrent crawl of {self.base_url} with {self.max_workers} workers')
        
        # 初始页面
        self._process_page_concurrently(self.base_url, 0)
        
        # 按深度层次进行爬取
        current_depth = 1
        while current_depth <= self.depth and self._next_level_links and len(self.visited_urls) < self.max_pages:
            level_links = self._next_level_links.copy()
            self._next_level_links = []
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = [executor.submit(self._process_page_concurrently, url, depth) 
                          for url, depth in level_links if url not in self.visited_urls]
                
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        logger.error(f'Error in concurrent processing: {str(e)}')
            
            current_depth += 1
            time.sleep(self.delay)  # 每层之间的延迟
        
        logger.info(f'Concurrent crawl completed. Visited {len(self.visited_urls)} pages.')
        return self.pages


def get_crawler(base_url: str, concurrent: bool = False, **kwargs) -> WebCrawler:
    """工厂函数，根据配置返回合适的爬虫实例"""
    if concurrent:
        return ConcurrentWebCrawler(base_url, **kwargs)
    else:
        return WebCrawler(base_url, **kwargs)