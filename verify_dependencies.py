#!/usr/bin/env python
# 验证项目所有依赖是否正确安装

import sys
print(f"Python版本: {sys.version}")
print("\n开始验证依赖安装...")

# 定义需要验证的依赖包
required_packages = [
    # 核心包
    'requests',
    'beautifulsoup4',
    'lxml',
    'nltk',
    'pandas', 
    'matplotlib',
    'scikit-learn',
    'jinja2',
    'pdfkit',
    'click',
    'validators',
    'python-dotenv',
    'pytest',
    'weasyprint'
]

# 安装状态统计
success_count = 0
failed_count = 0
failed_packages = []

# 逐个验证包的安装和导入
print("\n依赖验证结果:")
print("=" * 50)

for package in required_packages:
    try:
        # 尝试导入包
        __import__(package)
        # 获取包的版本信息
        pkg = __import__(package)
        version = getattr(pkg, '__version__', '未知版本')
        print(f"✅ {package}: {version}")
        success_count += 1
    except ImportError:
        print(f"❌ {package}: 导入失败")
        failed_count += 1
        failed_packages.append(package)

print("=" * 50)
print(f"\n验证统计: 成功 {success_count}, 失败 {failed_count}")

# 如果有失败的包，提供安装建议
if failed_packages:
    print("\n以下包安装失败:")
    for pkg in failed_packages:
        print(f"  - {pkg}")
    
    print("\n安装建议:")
    print("1. 尝试使用预编译wheel安装:")
    print(f"   pip install {' '.join(failed_packages)} --only-binary=:all: --user")
    print("\n2. 或者，您可以安装Microsoft Visual C++ Build Tools后重新安装:")
    print("   https://visualstudio.microsoft.com/visual-cpp-build-tools/")
    print("\n3. 对于特定包的问题，请参考项目requirements.txt文件")
else:
    print("\n🎉 所有依赖验证成功!")
    print("\n您现在可以尝试重新安装项目:")
    print("pip install -e .")
    print("\n然后测试项目功能:")
    print("python -m src.seo_automation.cli info")
