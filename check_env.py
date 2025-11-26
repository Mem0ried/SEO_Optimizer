#!/usr/bin/env python
# 检查Python环境和模块路径

import sys
print(f"Python版本: {sys.version}")
print(f"Python可执行文件: {sys.executable}")
print(f"模块搜索路径:")
for path in sys.path:
    print(f"  - {path}")

# 尝试导入nltk
try:
    import nltk
    print(f"\n✅ 成功导入nltk! 版本: {nltk.__version__}")
    print(f"nltk安装路径: {nltk.__file__}")
except ImportError as e:
    print(f"\n❌ 无法导入nltk: {e}")
    print("\n请检查以下内容:")
    print("1. nltk是否已正确安装")
    print("2. Python环境变量设置是否正确")
    print("3. 当前使用的Python是否与安装nltk的Python一致")
