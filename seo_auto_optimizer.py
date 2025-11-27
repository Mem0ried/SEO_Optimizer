#!/usr/bin/env python3
"""
SEO自优化程序入口脚本
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.seo_automation.auto_optimizer.cli import main

if __name__ == '__main__':
    main()