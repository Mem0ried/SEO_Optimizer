# SEO自动化与自优化工具

一个功能全面的SEO工具套件，包含强大的SEO自动化分析功能和智能自优化系统。帮助网站管理员和SEO专员快速评估网站SEO状况，生成详细分析报告，并提供自动化的SEO优化解决方案。

**最新更新**：修复了SEO优化工具无法识别HTML文件并执行优化的问题，优化了参数传递机制，确保元标签等自动修复功能正常工作。

## 功能特性

### 基础SEO分析功能
- **网站爬虫**：自动爬取网站内容，支持单页面和多页面爬取
- **关键词分析**：提取和分析页面关键词，计算关键词密度和分布，已优化支持资源缺失时的降级处理
- **SEO评分系统**：多维度评估网站SEO质量，包括内容、关键词、元标签、性能和技术SEO
- **性能分析**：分析页面加载速度、资源大小等性能指标
- **报告生成**：自动生成HTML和PDF格式的详细分析报告
- **命令行界面**：提供简单易用的命令行工具
- **错误处理增强**：添加超时机制和降级策略，确保工具在各种环境下稳定运行

### SEO自优化功能
- **全面SEO分析**：智能分析网站内容、关键词密度、元标签、标题结构等多个维度
- **智能优化建议**：根据分析结果生成优先级排序的具体优化建议
- **自动执行优化**：自动修改网站文件以实现SEO优化，包括标题、元标签、图片alt等
- **安全保障机制**：自动备份和一键恢复功能，确保优化安全可靠
- **自定义配置**：支持不同网站的个性化优化规则和配置文件
- **详细日志记录**：跟踪所有操作和结果的详细日志
- **多格式报告**：生成直观易懂的优化前后对比报告
- **优化的HTML文件识别**：确保系统能正确识别和处理网站中的HTML文件
- **改进的参数传递机制**：确保优化建议能被正确执行，元标签等自动修复功能正常工作

## 安装

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 安装工具包

```bash
pip install -e .
```

### 3. 可选：安装NLTK资源（推荐）

虽然工具已经优化为在资源缺失时仍能工作，但安装NLTK资源可以获得更好的关键词分析结果：

```bash
python -m nltk.downloader punkt stopwords
```

## 使用方法

### 1. SEO基础分析工具

#### 命令行使用

#### 注意事项
在使用命令行工具前，请确保已正确安装包（见安装部分）。如果安装后直接使用`seo-automation`命令出现错误，也可以使用Python模块方式运行：

```bash
python -m src.seo_automation.cli [命令] [参数]
```

#### 查看帮助信息

```bash
seo-automation --help
# 或使用Python模块方式
python -m src.seo_automation.cli --help
```

#### 爬取网站

```bash
seo-automation crawl https://example.com --depth 2 --output results.json
# 或使用Python模块方式
python -m src.seo_automation.cli crawl https://example.com --depth 2 --output results.json
```

#### 分析网站SEO

```bash
seo-automation analyze https://example.com --output report.html
# 或使用Python模块方式
python -m src.seo_automation.cli analyze https://example.com --output report.html
```

注意：输出格式由文件扩展名决定（.html或.pdf），不需要单独指定格式参数。

#### 查看工具信息

```bash
seo-automation info
# 或使用Python模块方式
python -m src.seo_automation.cli info
```

### 2. SEO自优化工具

SEO自优化程序提供了更高级的功能，可以自动分析、提供建议并执行SEO优化。

#### 直接运行自优化程序

```bash
python seo_auto_optimizer.py
```

#### 命令行参数说明

```bash
# 查看帮助信息
python seo_auto_optimizer.py --help

# 创建新的配置文件
python seo_auto_optimizer.py profile create --name my_site --path /path/to/website

# 列出所有配置文件
python seo_auto_optimizer.py profile list

# 执行网站SEO分析
python seo_auto_optimizer.py analyze --profile my_site

# 生成优化建议
python seo_auto_optimizer.py suggest --profile my_site

# 执行自动优化
python seo_auto_optimizer.py optimize --profile my_site --backup

# 查看备份列表
```bash
python seo_auto_optimizer.py backup list
```
python seo_auto_optimizer.py backup list

# 从备份恢复
python seo_auto_optimizer.py backup restore --latest
```

#### 完整优化流程示例

```bash
# 1. 创建配置文件
python seo_auto_optimizer.py profile create --name my_blog --path C:\\path\\to\\blog

# 2. 执行分析
python seo_auto_optimizer.py analyze --profile my_blog

# 3. 查看优化建议
python seo_auto_optimizer.py suggest --profile my_blog

# 4. 创建备份并执行优化
python seo_auto_optimizer.py optimize --profile my_blog --backup

# 5. 查看生成的报告
python seo_auto_optimizer.py report list
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
# skip_download=True 参数可跳过NLTK资源下载，适用于离线环境或快速分析
analyzer = get_keyword_analyzer(skip_download=True)

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
SEO_Optimizer/
├── src/
│   ├── __init__.py          # src包初始化文件
│   ├── config/              # 配置文件目录
│   │   ├── __init__.py
│   │   └── default_config.py
│   └── seo_automation/      # 主模块目录
│       ├── __init__.py      # 包初始化文件
│       ├── crawler.py       # 网站爬虫模块
│       ├── keyword_analyzer.py  # 关键词分析模块
│       ├── seo_scorer.py    # SEO评分系统
│       ├── performance_analyzer.py  # 性能分析模块
│       ├── report_generator.py     # 报告生成模块
│       ├── cli.py           # 命令行界面
│       └── auto_optimizer/  # SEO自优化模块
│           ├── __init__.py  # 自优化包初始化
│           ├── analyzer.py  # SEO分析器
│           ├── recommendation_generator.py  # 优化建议生成器
│           ├── optimize_executor.py  # 优化执行器
│           ├── backup_manager.py  # 备份管理器
│           ├── profile_manager.py  # 配置文件管理
│           ├── log_manager.py  # 日志管理器
│           ├── report_generator.py  # 自优化报告生成器
│           ├── optimizer.py  # 自优化主框架
│           └── cli.py       # 自优化命令行界面
├── templates/               # 报告模板
├── tests/                   # 测试文件目录
│   ├── test_auto_optimizer.py  # 自优化测试
│   └── ...                  # 其他测试文件
├── seo_auto_optimizer.py    # 自优化程序入口
├── requirements.txt         # 依赖列表
├── setup.py                 # 安装配置
└── README.md                # 项目说明文档
```

## 技术栈

### 基础技术
- Python 3.8+
- Requests - HTTP请求库
- BeautifulSoup4 - HTML解析库
- lxml - XML/HTML处理
- jieba - 中文分词
- NLTK - 自然语言处理
- Click - 命令行接口框架
- Jinja2 - 模板引擎
- WeasyPrint - PDF生成

### 自优化功能增强
- PyYAML - YAML配置文件处理
- GitPython - 可选的版本控制集成
- colorama - 命令行彩色输出
- tqdm - 进度条显示

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

### 通用注意事项
1. 爬取网站时请遵守robots.txt规则，避免对目标网站造成过大负载
2. 对于大型网站，建议设置合理的爬取深度和并发数
3. 生成PDF报告需要安装weasyprint，在某些系统上可能需要额外依赖
4. 中文关键词分析需要确保jieba库正常工作
5. 爬虫已经优化处理中文编码问题，支持正确显示中文网页标题和内容
6. 项目使用Python 3.8+版本开发，建议使用兼容的Python版本
7. 工具已优化为在NLTK资源缺失时仍能工作，但会使用简化的分析方法
8. 关键词分析步骤设置了30秒超时机制，处理大型网页时会自动降级以确保工具稳定运行
9. 在网络环境受限的情况下，可以使用`skip_download=True`参数避免资源下载尝试

### 自优化功能注意事项
1. 在执行自动优化前，请务必创建备份，以防需要恢复
2. 对于重要的生产网站，建议先在测试环境中验证优化结果
3. 默认情况下，内容和关键词优化器是禁用的，因为这些优化可能会改变网站的实际内容
4. 配置文件存储在用户目录下的`.seo_optimizer`文件夹中
5. 日志文件默认保存在`logs`目录中，可以通过配置文件修改
6. 报告文件默认保存在`reports`目录中，可以通过配置文件修改
7. 备份文件默认保存在`backups`目录中，定期清理旧备份以节省空间
8. 优化操作会自动识别网站中的HTML文件并应用相应的SEO优化
9. 元标签自动修复功能已优化，确保正确设置缺失的元描述等重要SEO元素
10. 执行优化后，可以通过再次运行分析命令验证优化效果

## 许可证

MIT License