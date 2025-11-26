# SEO自动化工具

一个功能强大的SEO自动化分析工具，帮助网站管理员和SEO专员快速评估网站SEO状况，生成详细的分析报告和优化建议。

## 功能特性

- **网站爬虫**：自动爬取网站内容，支持单页面和多页面爬取
- **关键词分析**：提取和分析页面关键词，计算关键词密度和分布
- **SEO评分系统**：多维度评估网站SEO质量，包括内容、关键词、元标签、性能和技术SEO
- **性能分析**：分析页面加载速度、资源大小等性能指标
- **报告生成**：自动生成HTML和PDF格式的详细分析报告
- **命令行界面**：提供简单易用的命令行工具

## 安装

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 安装工具包

```bash
pip install -e .
```

## 使用方法

### 命令行使用

#### 查看帮助信息

```bash
seo-automation --help
```

#### 爬取网站

```bash
seo-automation crawl https://example.com --depth 2 --output results.json
```

#### 分析网站SEO

```bash
seo-automation analyze https://example.com --format html --output report.html
```

#### 查看工具信息

```bash
seo-automation info
```

### Python API使用

#### 网站爬虫示例

```python
from seo_automation import get_crawler

# 创建爬虫实例
crawler = get_crawler()

# 爬取网站
results = crawler.crawl('https://example.com', max_depth=2)

# 打印结果
for page in results:
    print(f"URL: {page['url']}")
    print(f"标题: {page['title']}")
    print(f"状态码: {page['status_code']}")
    print("-" * 50)
```

#### 关键词分析示例

```python
from seo_automation import get_keyword_analyzer

# 创建关键词分析器实例
analyzer = get_keyword_analyzer()

# 分析页面关键词
results = analyzer.analyze_page('https://example.com')

# 打印关键词密度
print("关键词密度:")
for keyword, density in results['keyword_density'].items():
    if density > 1.0:  # 只显示密度大于1%的关键词
        print(f"{keyword}: {density:.2f}%")
```

#### SEO评分示例

```python
from seo_automation import get_seo_scorer

# 创建SEO评分器实例
scorer = get_seo_scorer()

# 分析网站SEO
results = scorer.score_website('https://example.com')

# 打印总体评分
print(f"网站总体SEO评分: {results['overall_scores']['weighted_total']:.1f}/100")
print(f"评级: {results['site_analysis']['overall_rating']}")

# 打印优化建议
print("\n优化建议:")
for suggestion in results['overall_suggestions']:
    print(f"- {suggestion}")
```

#### 性能分析示例

```python
from seo_automation import get_performance_analyzer

# 创建性能分析器实例
analyzer = get_performance_analyzer()

# 分析页面性能
results = analyzer.analyze_page_performance('https://example.com', analyze_resources=True)

# 打印性能指标
print(f"页面加载时间: {results['load_time_metrics']['page_load_time']:.2f}秒")
print(f"首字节时间(TTFB): {results['load_time_metrics']['ttfb']:.2f}秒")
print(f"页面大小: {results['load_time_metrics']['page_size'] / 1024:.1f} KB")
print(f"性能评分: {results['performance_scores']['weighted_total']:.1f}/100")
```

#### 报告生成示例

```python
from seo_automation import get_seo_scorer, get_report_generator

# 创建评分器和报告生成器
scorer = get_seo_scorer()
report_generator = get_report_generator()

# 分析网站SEO
seo_results = scorer.score_website('https://example.com')

# 生成HTML报告
html_path = report_generator.generate_report(seo_results, format_type='html')
print(f"HTML报告已生成: {html_path}")

# 生成PDF报告（需要安装weasyprint）
pdf_path = report_generator.generate_report(seo_results, format_type='pdf')
print(f"PDF报告已生成: {pdf_path}")
```

## 项目结构

```
seo-automation/
├── src/
│   └── seo_automation/
│       ├── __init__.py      # 包初始化文件
│       ├── crawler.py       # 网站爬虫模块
│       ├── keyword_analyzer.py  # 关键词分析模块
│       ├── seo_scorer.py    # SEO评分系统
│       ├── performance_analyzer.py  # 性能分析模块
│       ├── report_generator.py     # 报告生成模块
│       ├── cli.py           # 命令行界面
│       └── templates/       # 报告模板
├── tests/                   # 测试文件目录
├── requirements.txt         # 依赖列表
├── setup.py                 # 安装配置
└── README.md                # 项目说明文档
```

## 技术栈

- Python 3.7+
- Requests - HTTP请求库
- BeautifulSoup4 - HTML解析库
- lxml - XML/HTML处理
- jieba - 中文分词
- NLTK - 自然语言处理
- Click - 命令行接口框架
- Jinja2 - 模板引擎
- WeasyPrint - PDF生成

## 支持的分析维度

### 内容质量分析
- 内容长度和质量
- 可读性分析
- 内部链接结构
- 内容原创性评估

### 关键词优化分析
- 关键词密度计算
- 关键词分布评估
- 标题、描述中关键词使用
- H标签中关键词使用

### 元标签分析
- 标题标签评估
- 描述标签评估
- 规范标签检查
- 机器人标签检查

### 性能分析
- 页面加载时间
- 首字节时间(TTFB)
- 页面大小
- 资源数量和类型

### 技术SEO分析
- 移动友好性检查
- 索引状态检查
- URL结构评估
- 网站地图检查

## 注意事项

1. 爬取网站时请遵守robots.txt规则，避免对目标网站造成过大负载
2. 对于大型网站，建议设置合理的爬取深度和并发数
3. 生成PDF报告需要安装weasyprint，在某些系统上可能需要额外依赖
4. 中文关键词分析需要确保jieba库正常工作

## 许可证

MIT License