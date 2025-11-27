import click
import validators
import logging
import os
import json
from datetime import datetime
from typing import Optional, List

from .crawler import get_crawler
from .keyword_analyzer import get_keyword_analyzer
from ..config.default_config import CRAWL_CONFIG

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@click.group()
def main():
    """SEO自动化分析工具"""
    pass


@main.command()
@click.argument('url')
@click.option('--depth', '-d', default=CRAWL_CONFIG['DEFAULT_DEPTH'], help='爬取深度，默认为1')
@click.option('--max-pages', '-m', default=CRAWL_CONFIG['MAX_PAGES'], help='最大爬取页面数')
@click.option('--concurrent', '-c', is_flag=True, help='使用并发爬取')
@click.option('--delay', '-t', default=CRAWL_CONFIG['DELAY'], help='爬取延迟（秒）')
@click.option('--output', '-o', default=None, help='输出JSON文件路径')
def crawl(url: str, depth: int, max_pages: int, concurrent: bool, delay: int, output: Optional[str]):
    """爬取指定网站内容"""
    # 验证URL
    if not validators.url(url):
        click.echo(f"错误: {url} 不是有效的URL")
        return
    
    click.echo(f"开始爬取网站: {url}")
    click.echo(f"配置: 深度={depth}, 最大页面数={max_pages}, 并发={concurrent}, 延迟={delay}秒")
    
    try:
        # 创建爬虫
        crawler = get_crawler(url, concurrent=concurrent, depth=depth, max_pages=max_pages, delay=delay)
        
        # 执行爬取
        pages = crawler.crawl()
        
        # 显示结果统计
        success_count = sum(1 for p in pages.values() if 'error' not in p)
        error_count = len(pages) - success_count
        
        click.echo(f"\n爬取完成！")
        click.echo(f"总页面数: {len(pages)}")
        click.echo(f"成功页面数: {success_count}")
        click.echo(f"失败页面数: {error_count}")
        
        # 保存结果
        if output:
            # 准备导出数据（简化版本，不包含完整内容）
            export_data = {}
            for url, page_data in pages.items():
                if 'error' in page_data:
                    export_data[url] = {
                        'status': 'error',
                        'error': page_data['error'],
                        'depth': page_data.get('depth', 0)
                    }
                else:
                    export_data[url] = {
                        'status': 'success',
                        'title': page_data.get('title', ''),
                        'content_length': page_data.get('content_length', 0),
                        'status_code': page_data.get('status_code', 0),
                        'response_time': page_data.get('response_time', 0),
                        'depth': page_data.get('depth', 0),
                        'link_count': len(page_data.get('links', [])),
                        'image_count': len(page_data.get('images', []))
                    }
            
            # 确保输出目录存在
            output_dir = os.path.dirname(output)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # 保存到文件
            with open(output, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            click.echo(f"\n结果已保存到: {output}")
        
    except Exception as e:
        click.echo(f"\n错误: {str(e)}")
        logger.error(f"Crawl error: {str(e)}", exc_info=True)


@main.command()
@click.argument('url')
@click.option('--depth', '-d', default=CRAWL_CONFIG['DEFAULT_DEPTH'], help='爬取深度，默认为1')
@click.option('--output', '-o', default=None, help='输出文件路径，支持.html或.pdf格式')
@click.option('--keywords', '-k', default=None, help='要分析的特定关键词，用逗号分隔')
@click.option('--concurrent', '-c', is_flag=True, help='使用并发爬取')
def analyze(url: str, depth: int, output: Optional[str], keywords: Optional[str], concurrent: bool):
    """分析网站SEO情况并生成报告"""
    # 验证URL
    if not validators.url(url):
        click.echo(f"错误: {url} 不是有效的URL")
        return
    
    # 验证输出格式
    output_format = 'html'
    if output:
        ext = os.path.splitext(output)[1].lower()
        if ext in ['.html', '.htm']:
            output_format = 'html'
        elif ext == '.pdf':
            output_format = 'pdf'
        else:
            click.echo("警告: 输出格式不支持，将使用默认HTML格式")
            output_format = 'html'
            output = output + '.html' if not output.endswith('.html') else output
    
    # 解析关键词
    target_keywords = []
    if keywords:
        target_keywords = [kw.strip() for kw in keywords.split(',') if kw.strip()]
    
    click.echo(f"开始分析网站SEO: {url}")
    click.echo(f"配置: 深度={depth}, 输出格式={output_format}")
    if target_keywords:
        click.echo(f"目标关键词: {', '.join(target_keywords)}")
    
    try:
        # 步骤1: 爬取网站
        click.echo("\n[1/3] 正在爬取网站内容...")
        crawler = get_crawler(url, concurrent=concurrent, depth=depth)
        pages = crawler.crawl()
        
        # 步骤2: 关键词分析 - 增加超时机制和错误处理
        click.echo("\n[2/3] 正在分析关键词...")
        # 初始化默认的关键词结果，以应对分析失败的情况
        keyword_results = {'common_keywords': [], 'keyword_coverage': {}, 'overall_recommendations': []}
        
        # 创建一个函数用于关键词分析，以便设置超时
        def analyze_keywords_with_timeout():
            try:
                # 使用skip_download参数避免资源下载
                analyzer = get_keyword_analyzer(skip_download=True)
                # 检查并初始化stop_words（如果需要）
                if hasattr(analyzer, 'stop_words') and hasattr(analyzer, 'chinese_stop_words') and not hasattr(analyzer, 'all_stop_words'):
                    analyzer.all_stop_words = analyzer.stop_words.union(analyzer.chinese_stop_words)
                
                return analyzer.analyze_multiple_pages(pages)
            except Exception as e:
                logger.error(f"关键词分析出错: {str(e)}")
                raise
        
        # 使用超时机制执行关键词分析
        try:
            import threading
            
            class TimeoutException(Exception):
                pass
            
            def timeout_function(func, args=(), kwargs={}, timeout_duration=30):
                result = [TimeoutException("关键词分析超时")]
                
                def target():
                    try:
                        result[0] = func(*args, **kwargs)
                    except Exception as e:
                        result[0] = e
                
                thread = threading.Thread(target=target)
                thread.daemon = True
                thread.start()
                thread.join(timeout_duration)
                
                if isinstance(result[0], Exception):
                    raise result[0]
                return result[0]
            
            # 设置30秒超时执行关键词分析
            keyword_results = timeout_function(analyze_keywords_with_timeout, timeout_duration=30)
        except TimeoutException:
            click.echo("警告: 关键词分析超时，可能是因为处理大量文本")
            logger.warning("Keyword analysis timed out")
        except Exception as e:
            click.echo(f"警告: 关键词分析过程中出现错误: {str(e)}")
            click.echo("将继续生成基本报告，不包含关键词分析结果...")
            logger.warning(f"Keyword analysis error: {str(e)}")
        
        # 步骤3: 生成报告
        click.echo("\n[3/3] 正在生成报告...")
        
        # 显示分析结果摘要
        click.echo("\n=== SEO分析摘要 ===")
        click.echo(f"爬取页面数: {len(pages)}")
        
        # 显示共有关键词 - 增加安全检查
        click.echo("\n共有关键词:")
        if 'common_keywords' in keyword_results and keyword_results['common_keywords']:
            for i, (keyword, count) in enumerate(keyword_results['common_keywords'][:5], 1):
                coverage = keyword_results['keyword_coverage'].get(keyword, {})
                percentage = coverage.get('coverage_percentage', 0)
                click.echo(f"  {i}. {keyword} (在{count}个页面出现, 覆盖率: {percentage:.1f}%)")
        else:
            click.echo("  无法获取关键词数据")
        
        # 显示整体建议 - 增加安全检查
        click.echo("\n优化建议:")
        if 'overall_recommendations' in keyword_results and keyword_results['overall_recommendations']:
            for i, recommendation in enumerate(keyword_results['overall_recommendations'], 1):
                click.echo(f"  {i}. {recommendation}")
        else:
            click.echo("  未发现明显问题，继续保持!")
        
        # 如果需要保存报告，这里会调用报告生成模块
        # 注意：报告生成模块还未实现，这里先创建一个简单的HTML报告
        if output:
            try:
                # 修复调用方式 - 这不是一个类方法，不需要self
                _generate_simple_report(output, url, pages, keyword_results, output_format)
                click.echo(f"\n报告已生成: {output}")
            except Exception as e:
                click.echo(f"\n生成报告时出错: {str(e)}")
                logger.error(f"Report generation error: {str(e)}", exc_info=True)
        
    except Exception as e:
        click.echo(f"\n错误: {str(e)}")
        logger.error(f"Analysis error: {str(e)}", exc_info=True)


@main.command()
def info():
    """显示工具信息"""
    from . import __version__
    
    click.echo("=== SEO自动化分析工具 ===")
    click.echo(f"版本: {__version__}")
    click.echo("\n功能:")
    click.echo("  1. 网站内容爬取")
    click.echo("  2. 关键词提取和分析")
    click.echo("  3. SEO评分和优化建议")
    click.echo("  4. 报告生成")
    click.echo("使用示例:")
    click.echo("  爬取网站: seo-automation crawl https://example.com -d 2 -o results.json")
    click.echo("  分析SEO: seo-automation analyze https://example.com -d 1 -o report.html")
    click.echo("  提示: 输出格式由文件扩展名决定(.html或.pdf)，无需额外指定")
    click.echo("\n更多帮助:")
    click.echo("  seo-automation --help")
    click.echo("  seo-automation crawl --help")
    click.echo("  seo-automation analyze --help")


def _generate_simple_report(output_path: str, url: str, pages: dict, keyword_results: dict, format: str):
    """生成简单的HTML报告（临时实现，完整报告生成模块将在后续实现）"""
    # 这里只生成HTML报告，PDF生成需要依赖pdfkit
    
    # 简化报告内容，使其更健壮 - 不依赖复杂的keyword_results结构
    html_content = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>SEO分析报告 - {url}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }}
            h1, h2, h3 {{
                color: #2c3e50;
            }}
            .summary {{
                background-color: #f8f9fa;
                padding: 20px;
                border-radius: 5px;
                margin-bottom: 30px;
            }}
            .page-section {{
                margin-bottom: 30px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 10px;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}
            th {{
                background-color: #f2f2f2;
            }}
            .timestamp {{
                color: #7f8c8d;
                font-size: 0.9em;
                margin-top: 40px;
            }}
        </style>
    </head>
    <body>
        <h1>SEO分析报告</h1>
        <div class="summary">
            <h2>网站概览</h2>
            <p><strong>分析URL:</strong> {url}</p>
            <p><strong>爬取页面数:</strong> {len(pages)}</p>
            <p><strong>分析时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="page-section">
            <h2>页面信息</h2>
            <table>
                <tr>
                    <th>URL</th>
                    <th>标题</th>
                    <th>状态码</th>
                    <th>内容长度</th>
                </tr>
    '''
    
    # 添加页面表格行 - 使用更简单的数据结构
    for page_url, page_data in list(pages.items())[:10]:  # 限制显示前10个页面
        title = page_data.get('title', 'No Title')
        status_code = page_data.get('status_code', 'N/A')
        content_length = page_data.get('content_length', 0)
        html_content += f'''
                <tr>
                    <td>{page_url}</td>
                    <td>{title}</td>
                    <td>{status_code}</td>
                    <td>{content_length}</td>
                </tr>
        '''
    
    html_content += '''
            </table>
        </div>
        
        <div class="timestamp">
            <p>报告由SEO自动化工具 v0.1.0 生成</p>
        </div>
    </body>
    </html>
    '''
    
    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 保存HTML文件
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info(f"成功生成报告: {output_path}")
    except Exception as e:
        logger.error(f"保存报告失败: {str(e)}")
        raise
    
    # 如果需要PDF格式，这里会调用pdfkit，但当前我们只生成HTML


if __name__ == '__main__':
    main()