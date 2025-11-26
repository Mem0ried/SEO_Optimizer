#!/usr/bin/env python
# 简单测试脚本来验证项目功能

print("开始测试SEO项目...")

# 尝试导入主要模块
try:
    # 导入项目版本信息
    import src.seo_automation
    print(f"成功导入项目模块! 版本: {src.seo_automation.__version__}")
    
    # 验证命令行模块是否可导入
    from src.seo_automation import cli
    print("成功导入CLI模块!")
    
    # 显示导入成功信息
    print("\n✅ 项目核心模块已成功导入!")
    print("\n项目现在可以通过以下方式使用:")
    print("1. 直接运行Python模块: python -m src.seo_automation.cli <命令>")
    print("2. 通过安装的命令行工具: seo-automation <命令>")
    
except ImportError as e:
    print(f"导入错误: {e}")
    print("\n❌ 请检查依赖安装和导入路径")

print("\n测试完成。")
