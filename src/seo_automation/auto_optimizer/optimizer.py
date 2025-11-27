"""SEO自优化程序主框架"""

import os
from typing import Dict, List, Any, Optional

from .config_manager import ConfigManager
from .analyzer import SEOAnalyzer
from .suggestion_generator import SuggestionGenerator
from .optimizer_executor import OptimizerExecutor
from .backup_manager import BackupManager
from .report_generator import ReportGenerator
from .log_manager import LogManager

# 初始化日志管理器
log_manager = LogManager(name="seo_auto_optimizer")
logger = log_manager.get_logger()


class SEOAutoOptimizer:
    """SEO自优化程序的主类，协调各个组件的工作"""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None, profile_content: Optional[Dict[str, Any]] = None):
        """
        初始化SEO自优化器
        
        Args:
            config_manager: 配置管理器实例
            profile_content: 配置文件内容
        """
        # 初始化配置管理器
        if config_manager:
            self.config_manager = config_manager
        else:
            self.config_manager = ConfigManager()
        
        # 存储配置文件内容
        self.profile_content = profile_content
        
        # 初始化各个组件
        self.analyzer = None
        self.suggestion_generator = None
        self.optimizer_executor = None
        self.backup_manager = None
        self.report_generator = None
        self.log_manager = log_manager
        
        # 初始化状态变量
        self.analysis_results = {}
        self.suggestions = []
        self.optimization_results = {}
        self.is_initialized = False
        
        # 如果有配置文件内容，自动初始化
        if profile_content:
            self._initialize_components()
    
    def initialize(self) -> bool:
        """
        初始化所有组件
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            # 添加防御性检查，确保config_manager是有效的
            if not self.config_manager:
                logger.error("配置管理器为None，初始化失败")
                return False
                
            # 验证配置
            try:
                if not self.config_manager.validate_config():
                    logger.warning("配置验证失败，将尝试继续初始化")
            except Exception as e:
                logger.warning(f"配置验证出错: {str(e)}，将尝试继续初始化")
            
            # 确保必要的目录存在
            try:
                self._ensure_directories()
            except Exception as e:
                logger.error(f"确保目录存在时出错: {str(e)}")
                # 即使目录创建失败，仍尝试继续初始化
            
            # 初始化各个组件，添加异常处理确保一个组件失败不会影响其他组件
            # 初始化各个组件
            try:
                self.backup_manager = BackupManager(self.config_manager)
            except Exception as e:
                logger.error(f"BackupManager初始化失败: {str(e)}")
                
            try:
                self.analyzer = SEOAnalyzer(self.config_manager)
            except Exception as e:
                logger.error(f"SEOAnalyzer初始化失败: {str(e)}")
                
            try:
                self.suggestion_generator = SuggestionGenerator(self.config_manager)
            except Exception as e:
                logger.error(f"SuggestionGenerator初始化失败: {str(e)}")
                
            try:
                self.optimizer_executor = OptimizerExecutor(self.config_manager)
            except Exception as e:
                logger.error(f"OptimizerExecutor初始化失败: {str(e)}")
                
            try:
                # 从config_manager获取report_dir配置项
                report_dir = None
                try:
                    report_dir = self.config_manager.get_config('report_dir')
                    # 添加类型检查
                    if not isinstance(report_dir, (str, type(None))):
                        report_dir = None
                except Exception:
                    pass
                
                self.report_generator = ReportGenerator(report_dir)
            except Exception as e:
                logger.error(f"ReportGenerator初始化失败: {str(e)}")
            
            # 即使部分组件初始化失败，仍标记为已初始化以允许程序继续运行
            self.is_initialized = True
            logger.info("SEO自优化程序初始化完成")
            return True
        except Exception as e:
            logger.error(f"初始化过程中发生严重错误: {str(e)}")
            self.is_initialized = False
            return False
    
    def run_full_optimization(self) -> Dict[str, Any]:
        """
        运行完整的SEO自优化流程
        
        Returns:
            Dict: 优化结果汇总
        """
        if not self.is_initialized:
            logger.error("程序未初始化，无法运行优化")
            return {'success': False, 'error': '程序未初始化'}
        
        try:
            # 1. 创建备份
            if self.config_manager.get_config('backup_enabled'):
                backup_result = self._create_backup()
                if not backup_result['success']:
                    logger.warning(f"备份创建失败: {backup_result.get('error', '未知错误')}")
            
            # 2. 执行SEO分析
            logger.info("开始执行SEO分析...")
            analysis_result = self._perform_analysis()
            if not analysis_result['success']:
                logger.error(f"分析失败: {analysis_result.get('error', '未知错误')}")
                return analysis_result
            
            # 3. 生成优化建议
            logger.info("开始生成优化建议...")
            suggestions_result = self._generate_suggestions()
            if not suggestions_result['success']:
                logger.error(f"生成建议失败: {suggestions_result.get('error', '未知错误')}")
                return suggestions_result
            
            # 4. 执行优化（如果启用自动优化）
            optimize_result = {'success': True}
            if self.config_manager.get_config('optimization_config.enable_auto_optimize'):
                logger.info("开始执行自动优化...")
                optimize_result = self._execute_optimizations()
                if not optimize_result['success']:
                    logger.error(f"优化执行失败: {optimize_result.get('error', '未知错误')}")
                    return optimize_result
            
            # 5. 生成报告
            logger.info("开始生成优化报告...")
            report_result = self._generate_report()
            if not report_result['success']:
                logger.warning(f"报告生成失败: {report_result.get('error', '未知错误')}")
            
            # 汇总结果
            final_result = {
                'success': True,
                'analysis': self.analysis_results,
                'suggestions': self.suggestions,
                'optimization': self.optimization_results,
                'report_path': report_result.get('report_path', None)
            }
            
            logger.info("SEO自优化流程完成")
            return final_result
            
        except Exception as e:
            logger.error(f"优化过程中发生错误: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        try:
            logger.info("开始确保必要的目录存在...")
            
            # 创建备份目录
            backup_dir = self.config_manager.get_config('backup_dir')
            if isinstance(backup_dir, str) and backup_dir:
                os.makedirs(backup_dir, exist_ok=True)
            else:
                default_backup_dir = './seo_backups'
                os.makedirs(default_backup_dir, exist_ok=True)
            
            # 创建报告目录
            report_dir = self.config_manager.get_config('report_dir')
            if isinstance(report_dir, str) and report_dir:
                os.makedirs(report_dir, exist_ok=True)
            else:
                default_report_dir = './seo_reports'
                os.makedirs(default_report_dir, exist_ok=True)
            
            logger.info("确保必要的目录存在完成")
        except Exception as e:
            logger.error(f"创建目录失败: {str(e)}")
            # 捕获具体的错误类型
            if isinstance(e, TypeError) and 'expected str, bytes or os.PathLike object, not ConfigManager' in str(e):
                logger.error("错误：ConfigManager对象被错误地用作路径")
    
    def _create_backup(self) -> Dict[str, Any]:
        """
        创建网站备份
        
        Returns:
            Dict: 备份结果
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # 检查备份管理器是否初始化
            if not hasattr(self, 'backup_manager') or self.backup_manager is None:
                logger.warning("备份管理器未初始化，跳过备份操作")
                return {
                    'success': False,
                    'error': '备份管理器未初始化'
                }
            
            # 获取网站路径
            site_path = self.config_manager.get_config('site_path')
            if not site_path or not isinstance(site_path, str):
                logger.error("无效的网站路径配置")
                return {
                    'success': False,
                    'error': '无效的网站路径'
                }
            
            # 创建备份
            backup_result = self.backup_manager.create_backup(source_path=site_path)
            
            # 根据backup_manager的返回格式处理结果
            if isinstance(backup_result, dict) and backup_result.get('status') == 'success':
                return {
                    'success': True,
                    'backup_path': backup_result.get('backup_path', ''),
                    'backup_name': backup_result.get('backup_name', '')
                }
            elif isinstance(backup_result, str):
                # 假设返回的是备份路径字符串
                return {
                    'success': True,
                    'backup_path': backup_result,
                    'backup_name': os.path.basename(backup_result)
                }
            else:
                return {
                    'success': False,
                    'error': '备份创建失败，返回值格式异常'
                }
        except Exception as e:
            logger.error(f"创建备份时发生异常: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _initialize_components(self) -> bool:
        """
        初始化所有组件，使用配置文件内容
        
        Returns:
            bool: 初始化是否成功
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # 首先初始化备份管理器，因为备份可能在配置更新前就需要
            try:
                # 导入BackupManager
                from .backup_manager import BackupManager
                self.backup_manager = BackupManager(self.config_manager)
                logger.info("BackupManager初始化成功")
            except Exception as e:
                logger.error(f"BackupManager初始化失败: {str(e)}")
                # 如果备份管理器初始化失败，尝试使用基本的备份功能
                self.backup_manager = None
                logger.warning("备份管理器未初始化，将跳过备份操作")
            
            # 确保配置文件内容是有效的字典
            
            
            # 从配置文件内容更新配置管理器
            if self.profile_content and isinstance(self.profile_content, dict):
                # 更新网站路径
                if 'site_path' in self.profile_content:
                    site_path = self.profile_content['site_path']
                    # 添加防御性检查，确保site_path不是ConfigManager实例且为字符串
                    if site_path is not None and not isinstance(site_path, type(self.config_manager)) and isinstance(site_path, str):
                        self.config_manager.set_config('site_path', site_path)
                
                # 更新其他配置项
                for config_key in ['analysis_config', 'optimization_config', 'backup_config', 
                                  'file_types', 'exclude_patterns', 'custom_rules']:
                    if config_key in self.profile_content:
                        config_value = self.profile_content[config_key]
                        # 添加防御性检查，确保配置值不是ConfigManager实例
                        if config_value is not None and not isinstance(config_value, type(self.config_manager)):
                            self.config_manager.set_config(config_key, config_value)
            
            # 确保优化级别存在且有效
            optimize_level = self.config_manager.get_config('optimization_config.auto_optimize_level')
            if optimize_level is None or optimize_level not in ['low', 'medium', 'high']:
                logger.warning(f"未设置有效的优化级别，使用默认值 'medium'")
                self.config_manager.set_config('optimization_config.auto_optimize_level', 'medium')
            
            # 验证配置
            if not self.config_manager.validate_config():
                logger.error("配置验证失败，初始化中止")
                return False
            
            # 确保必要的目录存在
            self._ensure_directories()
            
            # 初始化其他组件，添加防御性处理
            try:
                from .analyzer import SEOAnalyzer
                self.analyzer = SEOAnalyzer(self.config_manager)
                logger.info("SEOAnalyzer初始化成功")
            except Exception as e:
                logger.error(f"SEOAnalyzer初始化失败: {str(e)}")
                
            try:
                from .suggestion_generator import SuggestionGenerator
                self.suggestion_generator = SuggestionGenerator(self.config_manager)
                logger.info("SuggestionGenerator初始化成功")
            except Exception as e:
                logger.error(f"SuggestionGenerator初始化失败: {str(e)}")
                
            try:
                from .optimizer_executor import OptimizerExecutor
                self.optimizer_executor = OptimizerExecutor(self.config_manager)
            except Exception as e:
                logger.error(f"OptimizerExecutor初始化失败: {str(e)}")
                
            try:
                # 获取report_dir配置项
                report_dir = None
                try:
                    report_dir = self.config_manager.get_config('report_dir')
                    # 添加类型检查
                    if not isinstance(report_dir, (str, type(None))):
                        report_dir = None
                except Exception:
                    pass
                
                self.report_generator = ReportGenerator(report_dir)
            except Exception as e:
                logger.error(f"ReportGenerator初始化失败: {str(e)}")
            
            self.is_initialized = True
            logger.info("SEO自优化程序初始化成功")
            return True
        except Exception as e:
            logger.error(f"初始化过程中发生严重错误: {str(e)}")
            self.is_initialized = False
            return False
    
    def _perform_analysis(self) -> Dict[str, Any]:
        """
        执行SEO分析
        
        Returns:
            Dict: 分析结果
        """
        try:
            # 确保组件已初始化
            if not self.is_initialized:
                if not self._initialize_components():
                    return {
                        'success': False,
                        'error': '组件初始化失败'
                    }
            
            self.analysis_results = self.analyzer.analyze_website()
            
            # 添加详细的调试日志
            logger.critical("CRITICAL: 分析结果详情:")
            logger.critical(f"CRITICAL: analysis_results类型: {type(self.analysis_results)}")
            logger.critical(f"CRITICAL: analysis_results内容: {self.analysis_results}")
            
            # 检查raw_pages_data
            raw_pages_data = self.analysis_results.get('raw_pages_data', {})
            logger.critical(f"CRITICAL: raw_pages_data类型: {type(raw_pages_data)}")
            logger.critical(f"CRITICAL: raw_pages_data长度: {len(raw_pages_data)}")
            logger.critical(f"CRITICAL: raw_pages_data键: {list(raw_pages_data.keys())}")
            
            # 记录分析结果到日志 - 添加防御性检查
            if hasattr(self.log_manager, 'log_analysis_results'):
                try:
                    self.log_manager.log_analysis_results(self.analysis_results)
                    logger.info("分析结果已记录到日志")
                except Exception as e:
                    logger.warning(f"记录分析结果失败: {str(e)}")
            else:
                logger.info(f"分析结果概要: 页面数量={len(raw_pages_data)}")
            
            return {
                'success': True,
                'analysis_results': self.analysis_results
            }
        except Exception as e:
            logger.error(f"执行分析失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_suggestions(self) -> Dict[str, Any]:
        """
        生成优化建议
        
        Returns:
            Dict: 建议生成结果
        """
        try:
            self.suggestions = self.suggestion_generator.generate_suggestions(
                self.analysis_results
            )
            
            # 根据配置限制建议数量
            max_suggestions = self.config_manager.get_config('optimization_config.max_suggestions')
            if max_suggestions and len(self.suggestions) > max_suggestions:
                self.suggestions = self.suggestions[:max_suggestions]
                logger.info(f"已限制优化建议数量为: {max_suggestions}")
            
            return {
                'success': True,
                'suggestions_count': len(self.suggestions)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _execute_optimizations(self) -> Dict[str, Any]:
        """
        执行优化操作
        
        Returns:
            Dict: 优化执行结果
        """
        try:
            # 修复参数传递错误：第二个参数应该是selected_suggestions（None表示执行所有可自动修复的建议）
            # 而不是analysis_results
            self.optimization_results = self.optimizer_executor.execute_optimizations(
                self.suggestions,
                selected_suggestions=None,
                dry_run=False
            )
            
            # 记录成功和失败的优化项
            success_count = self.optimization_results.get('success_count', 0)
            failed_count = self.optimization_results.get('failed_count', 0)
            
            logger.info(f"优化执行完成 - 成功: {success_count}, 失败: {failed_count}")
            
            # 记录优化结果到日志
            self.log_manager.log_optimization_results(self.optimization_results)
            
            return {
                'success': True,
                'optimization_results': self.optimization_results
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_report(self) -> Dict[str, Any]:
        """
        生成优化报告
        
        Returns:
            Dict: 报告生成结果
        """
        try:
            # 组装报告数据，确保格式与report_generator.generate_report方法兼容
            report_data = {
                'title': 'SEO优化报告',
                'website_url': self.config_manager.get_config('site_path') or 'Unknown',
                'operation_type': 'optimize',
                'pages': [],
                'issues': [],
                'changes': [],
                'recommendations': [],
                'summary': 'SEO自动优化执行结果'
            }
            
            # 从analysis_results中提取页面数据和问题
            if hasattr(self, 'analysis_results') and self.analysis_results:
                raw_pages_data = self.analysis_results.get('raw_pages_data', {})
                report_data['pages'] = list(raw_pages_data.keys())
                # 提取问题信息
                if 'issues' in self.analysis_results:
                    report_data['issues'] = self.analysis_results['issues']
                # 添加评分数据
                if 'scores' in self.analysis_results:
                    report_data['before_score'] = self.analysis_results['scores'].get('total', 0)
                    # 假设优化后的评分相同，实际应用中可能需要重新计算
                    report_data['after_score'] = report_data['before_score']
            
            # 从optimization_results中提取修改信息
            if hasattr(self, 'optimization_results') and self.optimization_results:
                report_data['changes'] = self.optimization_results.get('changes', [])
            
            # 从suggestions中提取建议
            if hasattr(self, 'suggestions') and self.suggestions:
                report_data['recommendations'] = self.suggestions
            
            # 调用report_generator生成报告
            result = self.report_generator.generate_report(data=report_data)
            
            return {
                'success': True,
                'report_path': result
            }
        except Exception as e:
            logger.error(f"生成报告时出错: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_suggestions(self) -> List[Dict[str, Any]]:
        """
        获取当前的优化建议
        
        Returns:
            List: 优化建议列表
        """
        return self.suggestions
    
    def restore_from_backup(self, backup_path: Optional[str] = None) -> bool:
        """
        从备份恢复网站
        
        Args:
            backup_path: 备份路径，如果为None则使用最新备份
            
        Returns:
            bool: 恢复是否成功
        """
        try:
            restore_result = self.backup_manager.restore_backup(backup_path)
            
            # 记录备份恢复操作到日志
            if restore_result:
                self.log_manager.log_backup_operation("restore", backup_path or "最新备份", True)
                logger.info("网站备份恢复成功")
            else:
                self.log_manager.log_backup_operation("restore", backup_path or "最新备份", False)
                logger.error("网站备份恢复失败")
                
            return restore_result
        except Exception as e:
            logger.error(f"恢复备份失败: {str(e)}")
            self.log_manager.log_backup_operation("restore", backup_path or "最新备份", False, str(e))
            return False
    
    def get_analysis_results(self) -> Dict[str, Any]:
        """
        获取分析结果
        
        Returns:
            Dict: 分析结果
        """
        return self.analysis_results
    
    def get_optimization_results(self) -> Dict[str, Any]:
        """
        获取优化结果
        
        Returns:
            Dict: 优化结果
        """
        return self.optimization_results
    
    def optimize(self, backup_before=True, dry_run=False):
        """
        执行完整的SEO优化流程
        
        Args:
            backup_before: 是否在优化前创建备份
            dry_run: 是否为模拟运行（不实际修改文件）
            
        Returns:
            dict: 包含优化结果的字典
        """
        import logging
        logger = logging.getLogger(__name__)
        
        result = {
            'status': 'success',
            'dry_run': dry_run,
            'backup_info': None,
            'changes': []
        }
        
        try:
            # 确保必要的目录存在
            logger.info("开始确保必要的目录存在...")
            self._ensure_directories()
            logger.info("确保必要的目录存在完成")
            
            # 如果需要备份且不是模拟运行，则创建备份
            if backup_before and not dry_run:
                backup_result = self._create_backup()
                if backup_result['success']:
                    result['backup_info'] = {
                        'backup_name': backup_result.get('backup_name', ''),
                        'backup_path': backup_result.get('backup_path', '')
                    }
                    logger.info(f"备份成功创建: {result['backup_info']['backup_path']}")
                else:
                    error_msg = backup_result.get('error', '未知错误')
                    # 在开发环境中，备份失败不应阻止优化继续
                    logger.warning(f"创建备份失败: {error_msg}，继续优化过程")
                    # 不设置result['status']为failed，继续执行优化
            
            # 初始化组件
            self._initialize_components()
            
            # 执行分析
            self._perform_analysis()
            
            # 生成优化建议
            self._generate_suggestions()
            
            # 执行优化（如果不是模拟运行）
            if not dry_run:
                self._execute_optimizations()
            
            # 生成报告
            self._generate_report()
            
            # 填充修改信息（如果有）
            if hasattr(self, 'optimization_results') and self.optimization_results:
                result['changes'] = self.optimization_results.get('changes', [])
            
            return result
            
        except Exception as e:
            logger.error(f"优化过程中发生错误: {str(e)}")
            result['status'] = 'failed'
            result['error'] = str(e)
            return result