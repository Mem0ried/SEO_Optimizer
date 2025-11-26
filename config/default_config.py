# 默认配置文件

# 爬虫配置
CRAWL_CONFIG = {
    'DEFAULT_DEPTH': 1,  # 默认爬取深度
    'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'TIMEOUT': 30,  # 请求超时时间（秒）
    'FOLLOW_REDIRECTS': True,
    'MAX_PAGES': 100,  # 最大爬取页面数
    'DELAY': 1,  # 请求间隔（秒），避免爬取过快
}

# SEO配置
SEO_CONFIG = {
    'META_TAGS_WEIGHT': {
        'title': 10,
        'description': 8,
        'h1': 7,
        'h2': 5,
        'h3': 3,
        'keywords': 6,
    },
    'OPTIMAL_KEYWORD_DENSITY': {
        'min': 1,  # 最小关键词密度百分比
        'max': 3,  # 最大关键词密度百分比
    },
    'MIN_CONTENT_LENGTH': 300,  # 最小内容长度
    'OPTIMAL_IMAGE_ALT_RATIO': 0.8,  # 最优图片alt属性覆盖率
}

# 性能分析配置
PERFORMANCE_CONFIG = {
    'MAX_PAGE_SIZE': 5 * 1024 * 1024,  # 最大页面大小（5MB）
    'MAX_REDIRECTS': 3,  # 最大重定向次数
    'OPTIMAL_LOAD_TIME': 3,  # 最优加载时间（秒）
    'MAX_EXTERNAL_RESOURCES': 50,  # 最大外部资源数
}

# 报告配置
REPORT_CONFIG = {
    'DEFAULT_OUTPUT_FORMAT': 'html',
    'PDF_OPTIONS': {
        'page-size': 'Letter',
        'margin-top': '15mm',
        'margin-right': '15mm',
        'margin-bottom': '15mm',
        'margin-left': '15mm',
    },
}

# 评分权重
SCORE_WEIGHTS = {
    'content': 0.3,  # 内容质量权重
    'keywords': 0.25,  # 关键词权重
    'meta_tags': 0.2,  # 元标签权重
    'performance': 0.15,  # 性能权重
    'technical': 0.1,  # 技术SEO权重
}

# NLTK配置
NLTK_CONFIG = {
    'DOWNLOAD_PACKAGES': ['punkt', 'stopwords'],
}