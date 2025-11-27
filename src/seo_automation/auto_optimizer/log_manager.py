"""日志管理器，负责记录程序运行过程中的各种日志"""

import os
import logging
import logging.handlers
import datetime
import json
import shutil
from typing import Optional, Dict, Any


class LogManager:
    """
    日志管理器类，提供灵活的日志记录功能
    支持文件日志、控制台日志、不同级别的日志记录、日志轮转等
    """
    
    # 日志级别映射
    LOG_LEVELS = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'error': logging.ERROR,
        'critical': logging.CRITICAL
    }
    
    # 默认日志格式化
    DEFAULT_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    def __init__(self, name: str, log_dir: Optional[str] = None, log_level: str = 'info'):
        """
        初始化日志管理器
        
        Args:
            name: 日志名称
            log_dir: 日志文件目录，如果为None则使用默认目录
            log_level: 日志级别，可选值: debug, info, warning, error, critical
        """
        self.name = name
        self.log_dir = self._get_log_directory(log_dir)
        self.log_level = self.LOG_LEVELS.get(log_level, logging.INFO)
        
        # 确保日志目录存在
        os.makedirs(self.log_dir, exist_ok=True)
        
        # 创建日志器
        self.logger = self._create_logger()
        
        # 添加处理器
        self._add_handlers()
    
    def _get_log_directory(self, log_dir: Optional[str]) -> str:
        """
        获取日志文件目录
        
        Args:
            log_dir: 指定的日志目录
            
        Returns:
            str: 日志文件目录路径
        """
        if log_dir:
            return log_dir
        
        # 默认日志目录
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return os.path.join(base_dir, 'logs')
    
    def _create_logger(self) -> logging.Logger:
        """
        创建日志器
        
        Returns:
            logging.Logger: 日志器实例
        """
        logger = logging.getLogger(self.name)
        logger.setLevel(self.log_level)
        
        # 避免重复添加处理器
        if logger.handlers:
            for handler in logger.handlers:
                logger.removeHandler(handler)
        
        return logger
    
    def _add_handlers(self):
        """
        添加日志处理器
        """
        # 添加控制台处理器
        self._add_console_handler()
        
        # 添加文件处理器
        self._add_file_handler()
        
        # 添加错误日志处理器
        self._add_error_handler()
    
    def _add_console_handler(self):
        """
        添加控制台日志处理器
        """
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.log_level)
        
        # 设置控制台日志格式
        formatter = logging.Formatter(self.DEFAULT_FORMAT)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(console_handler)
    
    def _add_file_handler(self):
        """
        添加文件日志处理器，支持日志轮转
        """
        # 日志文件名
        log_filename = os.path.join(self.log_dir, f"{self.name}.log")
        
        # 创建RotatingFileHandler，每个日志文件最大10MB，最多保留10个备份
        file_handler = logging.handlers.RotatingFileHandler(
            log_filename,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=10,
            encoding='utf-8'
        )
        file_handler.setLevel(self.log_level)
        
        # 设置文件日志格式
        formatter = logging.Formatter(self.DEFAULT_FORMAT)
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
    
    def _add_error_handler(self):
        """
        添加错误日志处理器，专门记录错误和关键信息
        """
        # 错误日志文件名
        error_log_filename = os.path.join(self.log_dir, f"{self.name}_error.log")
        
        # 创建RotatingFileHandler，每个日志文件最大5MB，最多保留5个备份
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_filename,
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        
        # 设置错误日志格式，包含更多详细信息
        error_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(process)d - %(message)s'
        )
        error_handler.setFormatter(error_formatter)
        
        self.logger.addHandler(error_handler)
    
    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """
        记录调试级别的日志
        
        Args:
            message: 日志消息
            extra: 额外的上下文信息
        """
        if extra:
            self.logger.debug(message, extra=extra)
        else:
            self.logger.debug(message)
    
    def info(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """
        记录信息级别的日志
        
        Args:
            message: 日志消息
            extra: 额外的上下文信息
        """
        if extra:
            self.logger.info(message, extra=extra)
        else:
            self.logger.info(message)
    
    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """
        记录警告级别的日志
        
        Args:
            message: 日志消息
            extra: 额外的上下文信息
        """
        if extra:
            self.logger.warning(message, extra=extra)
        else:
            self.logger.warning(message)
    
    def error(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """
        记录错误级别的日志
        
        Args:
            message: 日志消息
            extra: 额外的上下文信息
        """
        if extra:
            self.logger.error(message, extra=extra)
        else:
            self.logger.error(message)
    
    def critical(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """
        记录关键级别的日志
        
        Args:
            message: 日志消息
            extra: 额外的上下文信息
        """
        if extra:
            self.logger.critical(message, extra=extra)
        else:
            self.logger.critical(message)
    
    def log_operation(self, operation: str, status: str, details: Optional[Dict[str, Any]] = None):
        """
        记录操作日志
        
        Args:
            operation: 操作名称
            status: 操作状态 (success/failed/started/in_progress)
            details: 操作详情
        """
        if details is None:
            details = {}
        
        # 构建操作日志消息
        log_message = f"Operation: {operation}, Status: {status}"
        
        # 根据状态确定日志级别
        if status == 'failed':
            self.error(log_message, extra={'operation': operation, 'status': status, 'details': details})
        elif status == 'critical':
            self.critical(log_message, extra={'operation': operation, 'status': status, 'details': details})
        elif status == 'warning':
            self.warning(log_message, extra={'operation': operation, 'status': status, 'details': details})
        elif status == 'started':
            self.info(log_message, extra={'operation': operation, 'status': status, 'details': details})
        else:
            self.info(log_message, extra={'operation': operation, 'status': status, 'details': details})
    
    def log_analysis_result(self, result: Dict[str, Any]):
        """
        记录分析结果
        
        Args:
            result: 分析结果
        """
        # 记录总体评分
        if 'overall_score' in result:
            self.info(
                f"Analysis completed. Overall score: {result['overall_score']}/100",
                extra={'analysis_result': result}
            )
        
        # 记录发现的问题数量
        if 'issues' in result:
            issue_count = len(result['issues'])
            self.info(
                f"Found {issue_count} issues during analysis",
                extra={'analysis_result': result, 'issue_count': issue_count}
            )
    
    def log_optimization_result(self, result: Dict[str, Any]):
        """
        记录优化结果
        
        Args:
            result: 优化结果
        """
        status = result.get('status', 'unknown')
        
        if status == 'success':
            # 统计修改数量
            changes = result.get('changes', [])
            total_files = len(changes)
            total_changes = sum(len(file_changes.get('changes', [])) for file_changes in changes)
            
            self.info(
                f"Optimization completed successfully. Modified {total_files} files with {total_changes} changes.",
                extra={'optimization_result': result, 'files_changed': total_files, 'changes_made': total_changes}
            )
        else:
            error = result.get('error', 'Unknown error')
            self.error(
                f"Optimization failed. Error: {error}",
                extra={'optimization_result': result, 'error': error}
            )
    
    def log_backup_operation(self, operation: str, backup_name: str, status: str, details: Optional[Dict[str, Any]] = None):
        """
        记录备份操作日志
        
        Args:
            operation: 备份操作 (create/restore/delete/list)
            backup_name: 备份名称
            status: 操作状态 (success/failed)
            details: 操作详情
        """
        if details is None:
            details = {}
        
        # 构建日志消息
        log_message = f"Backup {operation}: {backup_name}, Status: {status}"
        
        # 根据状态确定日志级别
        if status == 'success':
            self.info(log_message, extra={'backup_operation': operation, 'backup_name': backup_name, 'details': details})
        else:
            error = details.get('error', 'Unknown error')
            self.error(log_message, extra={'backup_operation': operation, 'backup_name': backup_name, 'details': details, 'error': error})
    
    def export_logs(self, export_path: str, days: int = 7):
        """
        导出最近的日志
        
        Args:
            export_path: 导出路径
            days: 导出最近几天的日志，默认7天
            
        Returns:
            Dict: 导出结果
        """
        try:
            # 确保导出目录存在
            export_dir = os.path.dirname(export_path)
            if export_dir and not os.path.exists(export_dir):
                os.makedirs(export_dir, exist_ok=True)
            
            # 获取时间范围
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)
            
            # 收集日志文件
            log_files = []
            for filename in os.listdir(self.log_dir):
                if filename.startswith(self.name) and filename.endswith('.log'):
                    file_path = os.path.join(self.log_dir, filename)
                    file_modified = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    # 只导出指定天数内修改的日志
                    if file_modified >= cutoff_date:
                        log_files.append(file_path)
            
            # 导出日志
            export_content = {}
            for log_file in log_files:
                filename = os.path.basename(log_file)
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    export_content[filename] = f.readlines()
            
            # 保存导出的日志
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_content, f, ensure_ascii=False, indent=2)
            
            self.info(f"Logs exported successfully to {export_path}", extra={'export_path': export_path, 'days': days})
            
            return {
                'status': 'success',
                'export_path': export_path,
                'log_files_count': len(log_files)
            }
            
        except Exception as e:
            self.error(f"Failed to export logs: {str(e)}", extra={'export_path': export_path, 'days': days, 'error': str(e)})
            
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def rotate_logs(self):
        """
        手动触发日志轮转
        
        Returns:
            Dict: 轮转结果
        """
        try:
            for handler in self.logger.handlers:
                if isinstance(handler, logging.handlers.RotatingFileHandler):
                    handler.doRollover()
            
            self.info("Logs rotated successfully")
            
            return {
                'status': 'success'
            }
            
        except Exception as e:
            self.error(f"Failed to rotate logs: {str(e)}", extra={'error': str(e)})
            
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def archive_old_logs(self, days: int = 30):
        """
        归档旧日志
        
        Args:
            days: 归档多少天前的日志，默认30天
            
        Returns:
            Dict: 归档结果
        """
        try:
            # 确保归档目录存在
            archive_dir = os.path.join(self.log_dir, 'archive')
            os.makedirs(archive_dir, exist_ok=True)
            
            # 获取时间范围
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)
            
            # 查找并归档旧日志
            archived_files = []
            for filename in os.listdir(self.log_dir):
                if filename.startswith(self.name) and (filename.endswith('.log') or filename.endswith('.log.')):
                    file_path = os.path.join(self.log_dir, filename)
                    file_modified = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    # 只归档指定天数前的日志
                    if file_modified < cutoff_date:
                        # 创建归档文件名（添加日期前缀）
                        date_prefix = file_modified.strftime('%Y%m%d')
                        archive_filename = f"{date_prefix}_{filename}"
                        archive_path = os.path.join(archive_dir, archive_filename)
                        
                        # 移动文件到归档目录
                        shutil.move(file_path, archive_path)
                        archived_files.append(archive_filename)
            
            self.info(f"Archived {len(archived_files)} old log files", extra={'archived_count': len(archived_files), 'days': days})
            
            return {
                'status': 'success',
                'archived_count': len(archived_files),
                'archived_files': archived_files
            }
            
        except Exception as e:
            self.error(f"Failed to archive old logs: {str(e)}", extra={'days': days, 'error': str(e)})
            
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def set_level(self, level: str):
        """
        设置日志级别
        
        Args:
            level: 日志级别，可选值: debug, info, warning, error, critical
        """
        new_level = self.LOG_LEVELS.get(level, logging.INFO)
        
        # 更新日志器级别
        self.logger.setLevel(new_level)
        
        # 更新所有处理器级别
        for handler in self.logger.handlers:
            handler.setLevel(new_level)
        
        self.log_level = new_level
        self.info(f"Log level changed to {level}", extra={'new_level': level})
    
    def get_logger(self) -> logging.Logger:
        """
        获取底层的logging.Logger实例
        
        Returns:
            logging.Logger: 日志器实例
        """
        return self.logger


# 全局日志管理器实例
_global_log_manager = None


def get_logger(name: str = 'seo_auto_optimizer') -> LogManager:
    """
    获取全局日志管理器实例
    
    Args:
        name: 日志名称
        
    Returns:
        LogManager: 日志管理器实例
    """
    global _global_log_manager
    
    if _global_log_manager is None:
        _global_log_manager = LogManager(name)
    
    return _global_log_manager