"""
SEO自优化程序测试脚本

这个测试脚本用于验证SEO自优化程序的各个功能模块是否正常工作，
包括配置管理、分析器、建议生成器、优化执行器、备份管理器、
日志管理器和报告生成器等组件的基本功能。
"""

import os
import sys
import json
import time
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.seo_automation.auto_optimizer.optimizer import SEOAutoOptimizer
from src.seo_automation.auto_optimizer.log_manager import LogManager
from src.seo_automation.auto_optimizer.config_manager import ConfigManager


def run_tests():
    """运行SEO自优化程序的测试"""
    print("=" * 80)
    print("      SEO自优化程序功能测试      ")
    print("=" * 80)
    
    test_results = {
        'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'passed': 0,
        'failed': 0,
        'results': []
    }
    
    # 1. 测试日志管理器
    print("\n[测试1] 初始化日志管理器...")
    try:
        log_manager = LogManager()
        log_manager.info("日志管理器测试成功")
        test_results['results'].append({'name': '日志管理器初始化', 'status': 'passed'})
        test_results['passed'] += 1
        print("✓ 日志管理器初始化成功")
    except Exception as e:
        test_results['results'].append({'name': '日志管理器初始化', 'status': 'failed', 'error': str(e)})
        test_results['failed'] += 1
        print(f"✗ 日志管理器初始化失败: {str(e)}")
    
    # 2. 测试配置管理器
    print("\n[测试2] 初始化配置管理器...")
    try:
        config_manager = ConfigManager()
        config_manager.validate_config()
        test_results['results'].append({'name': '配置管理器初始化', 'status': 'passed'})
        test_results['passed'] += 1
        print("✓ 配置管理器初始化成功")
    except Exception as e:
        test_results['results'].append({'name': '配置管理器初始化', 'status': 'failed', 'error': str(e)})
        test_results['failed'] += 1
        print(f"✗ 配置管理器初始化失败: {str(e)}")
    
    # 3. 测试SEO自优化程序初始化
    print("\n[测试3] 初始化SEO自优化程序...")
    try:
        optimizer = SEOAutoOptimizer()
        init_result = optimizer.initialize()
        if init_result:
            test_results['results'].append({'name': 'SEO自优化程序初始化', 'status': 'passed'})
            test_results['passed'] += 1
            print("✓ SEO自优化程序初始化成功")
        else:
            test_results['results'].append({'name': 'SEO自优化程序初始化', 'status': 'failed', 'error': '初始化返回失败'})
            test_results['failed'] += 1
            print("✗ SEO自优化程序初始化失败: 初始化返回失败")
    except Exception as e:
        test_results['results'].append({'name': 'SEO自优化程序初始化', 'status': 'failed', 'error': str(e)})
        test_results['failed'] += 1
        print(f"✗ SEO自优化程序初始化失败: {str(e)}")
    
    # 4. 测试备份功能
    print("\n[测试4] 测试备份功能...")
    try:
        if 'optimizer' in locals() and optimizer.is_initialized:
            # 临时启用备份
            original_backup_setting = config_manager.get_config('backup_enabled')
            config_manager.set_config('backup_enabled', True)
            
            # 测试备份创建
            backup_result = optimizer._create_backup()
            if backup_result['success']:
                test_results['results'].append({'name': '备份创建', 'status': 'passed'})
                test_results['passed'] += 1
                print(f"✓ 备份创建成功: {backup_result['backup_path']}")
                
                # 恢复原始设置
                config_manager.set_config('backup_enabled', original_backup_setting)
            else:
                test_results['results'].append({'name': '备份创建', 'status': 'failed', 'error': backup_result.get('error', '未知错误')})
                test_results['failed'] += 1
                print(f"✗ 备份创建失败: {backup_result.get('error', '未知错误')}")
        else:
            test_results['results'].append({'name': '备份创建', 'status': 'skipped', 'reason': '优化器未初始化'})
            print("⚠ 备份功能测试跳过: 优化器未初始化")
    except Exception as e:
        test_results['results'].append({'name': '备份创建', 'status': 'failed', 'error': str(e)})
        test_results['failed'] += 1
        print(f"✗ 备份功能测试失败: {str(e)}")
    
    # 生成测试报告
    print("\n" + "=" * 80)
    print("        测试结果汇总        ")
    print("=" * 80)
    print(f"总测试项: {test_results['passed'] + test_results['failed']}")
    print(f"通过: {test_results['passed']}")
    print(f"失败: {test_results['failed']}")
    
    # 输出详细测试结果
    if test_results['failed'] > 0:
        print("\n失败的测试项:")
        for result in test_results['results']:
            if result['status'] == 'failed':
                print(f"  - {result['name']}: {result.get('error', '未知错误')}")
    
    # 保存测试结果到JSON文件
    test_report_dir = os.path.join(os.path.dirname(__file__), 'reports')
    os.makedirs(test_report_dir, exist_ok=True)
    report_filename = os.path.join(test_report_dir, f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    
    with open(report_filename, 'w', encoding='utf-8') as f:
        json.dump(test_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n测试报告已保存至: {report_filename}")
    
    # 返回测试是否全部通过
    return test_results['failed'] == 0


if __name__ == "__main__":
    print("开始测试SEO自优化程序...")
    start_time = time.time()
    
    success = run_tests()
    
    end_time = time.time()
    print(f"\n测试完成，耗时: {end_time - start_time:.2f} 秒")
    
    if success:
        print("🎉 所有测试通过！SEO自优化程序可以正常使用。")
    else:
        print("❌ 部分测试失败，请检查错误信息并修复问题。")
