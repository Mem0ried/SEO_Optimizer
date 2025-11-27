"""配置管理器，负责加载、保存和验证配置"""

import json
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ConfigManager:
    """SEO自优化程序配置管理器"""
    
    # 默认配置
    DEFAULT_CONFIG = {
        # 基础配置
        'site_path': '',  # 网站根目录路径
        'backup_enabled': True,  # 是否启用备份
        'backup_dir': './seo_backups',  # 备份目录
        'report_dir': './seo_reports',  # 报告目录
        
        # 分析配置
        'analysis_config': {
            'max_depth': 2,  # 爬取深度
            'analyze_images': True,  # 是否分析图片
            'analyze_links': True,  # 是否分析链接
            'skip_nltk_download': True,  # 是否跳过NLTK下载
        },
        
        # 优化配置
        'optimization_config': {
            'enable_auto_optimize': True,  # 是否启用自动优化
            'auto_optimize_level': 'medium',  # 自动优化级别: low, medium, high
            'max_suggestions': 10,  # 最大优化建议数量
            
            # 各优化项配置
            'title_optimization': True,  # 标题优化
            'meta_description_optimization': True,  # 描述优化
            'heading_optimization': True,  # 标题标签优化
            'image_optimization': True,  # 图片优化
            'keyword_optimization': True,  # 关键词优化
            'url_optimization': False,  # URL优化(默认关闭，可能影响链接)
            'internal_link_optimization': True,  # 内部链接优化
        },
        
        # 文件类型配置
        'file_types': {
            'html': ['.html', '.htm', '.php', '.asp', '.aspx', '.jsp'],
            'css': ['.css'],
            'js': ['.js'],
            'images': ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        },
        
        # 排除规则
        'exclude_patterns': [
            'node_modules/',
            'venv/',
            'env/',
            '.git/',
            '.svn/',
            'dist/',
            'build/',
            'cache/',
            'tmp/',
            'temp/'
        ]
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认配置
        """
        self.config_path = config_path
        self.config = self.DEFAULT_CONFIG.copy()
        
        # 如果提供了配置文件路径，则加载配置
        if config_path:
            self.load_config(config_path)
    
    def load_config(self, config_path: str) -> bool:
        """
        从文件加载配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            bool: 加载是否成功
        """
        try:
            if not os.path.exists(config_path):
                logger.warning(f"配置文件不存在: {config_path}，将使用默认配置")
                return False
            
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
            
            # 合并用户配置到默认配置
            self._merge_config(self.config, user_config)
            logger.info(f"成功加载配置文件: {config_path}")
            return True
        except Exception as e:
            logger.error(f"加载配置文件失败: {str(e)}")
            return False
    
    def save_config(self, config_path: Optional[str] = None) -> bool:
        """
        保存配置到文件
        
        Args:
            config_path: 配置文件路径，如果为None则使用初始化时的路径
            
        Returns:
            bool: 保存是否成功
        """
        try:
            target_path = config_path or self.config_path
            if not target_path:
                logger.error("未指定保存路径")
                return False
            
            # 确保目录存在
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            
            with open(target_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            
            logger.info(f"成功保存配置到: {target_path}")
            return True
        except Exception as e:
            logger.error(f"保存配置失败: {str(e)}")
            return False
    
    def get_config(self, key_path: Optional[str] = None) -> Any:
        """
        获取配置值
        
        Args:
            key_path: 配置键路径，支持点表示法，如 'optimization_config.title_optimization'
            
        Returns:
            Any: 配置值
        """
        if key_path is None:
            return self.config
        
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                logger.warning(f"配置键不存在: {key_path}")
                return None
        
        return value
    
    def set_config(self, key_path: str, value: Any) -> bool:
        """
        设置配置值
        
        Args:
            key_path: 配置键路径，支持点表示法
            value: 配置值
            
        Returns:
            bool: 设置是否成功
        """
        try:
            # 防止将ConfigManager对象设置为配置值
            if isinstance(value, type(self)):
                logger.error(f"不能将ConfigManager对象设置为配置值: {key_path}")
                return False
            
            keys = key_path.split('.')
            config = self.config
            
            # 导航到目标键的父级
            for key in keys[:-1]:
                if key not in config:
                    config[key] = {}
                config = config[key]
            
            # 设置值
            config[keys[-1]] = value
            logger.info(f"设置配置: {key_path} = {value}")
            return True
        except Exception as e:
            logger.error(f"设置配置失败: {str(e)}")
            return False
    
    def validate_config(self) -> bool:
        """
        验证配置的有效性
        
        Returns:
            bool: 配置是否有效
        """
        try:
            logger.info(f"开始验证配置，配置管理器实例ID: {id(self)}")
            logger.info(f"配置对象类型: {type(self).__name__}")
            logger.info(f"配置内容概览: {type(self.config).__name__}，包含键: {list(self.config.keys())}")
            
            # 检查必要的配置项
            required_keys = ['site_path']
            logger.info(f"检查必要配置项: {required_keys}")
            
            for key in required_keys:
                logger.info(f"检查配置项: {key}")
                value = self.get_config(key)
                logger.info(f"配置项 {key} 的值: {value}，类型: {type(value).__name__}")
                
                # 检查是否存在ConfigManager对象
                if isinstance(value, type(self)):
                    logger.error(f"配置项 {key} 包含ConfigManager对象，这是不允许的")
                    return False
                    
                if not value:
                    logger.error(f"缺少必要配置: {key}")
                    return False
            
            # 验证网站路径
            logger.info("开始验证网站路径")
            site_path = self.get_config('site_path')
            logger.info(f"site_path值: {site_path}，类型: {type(site_path).__name__}")
            
            # 添加类型检查，确保site_path是字符串类型
            if not isinstance(site_path, str):
                logger.error(f"网站路径必须是字符串类型，当前类型: {type(site_path).__name__}")
                return False
            
            try:
                path_exists = os.path.exists(site_path)
                is_dir = os.path.isdir(site_path) if path_exists else False
                logger.info(f"网站路径存在: {path_exists}，是目录: {is_dir}")
                
                if not path_exists or not is_dir:
                    logger.error(f"网站路径不存在或不是目录: {site_path}")
                    return False
            except TypeError as e:
                logger.error(f"检查网站路径时发生类型错误: {str(e)}")
                logger.error(f"site_path的值: {site_path}，类型: {type(site_path).__name__}")
                return False
            except Exception as e:
                logger.error(f"检查网站路径时发生未知错误: {str(e)}")
                return False
            
            # 验证优化级别
            logger.info("开始验证优化级别")
            optimize_level = self.get_config('optimization_config.auto_optimize_level')
            logger.info(f"optimize_level值: {optimize_level}，类型: {type(optimize_level).__name__}")
            
            if optimize_level not in ['low', 'medium', 'high']:
                logger.error(f"无效的优化级别: {optimize_level}，必须是 'low', 'medium' 或 'high'")
                return False
            
            # 验证备份目录配置
            logger.info("验证备份目录配置")
            backup_dir = self.get_config('backup_dir')
            logger.info(f"backup_dir值: {backup_dir}，类型: {type(backup_dir).__name__}")
            
            # 验证报告目录配置
            logger.info("验证报告目录配置")
            report_dir = self.get_config('report_dir')
            logger.info(f"report_dir值: {report_dir}，类型: {type(report_dir).__name__}")
            
            logger.info("配置验证通过")
            return True
        except Exception as e:
            logger.error(f"配置验证过程中发生异常: {str(e)}")
            logger.error(f"异常类型: {type(e).__name__}")
            return False
    
    def _merge_config(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """
        递归合并配置字典
        
        Args:
            base: 基础配置
            override: 覆盖配置
            
        Returns:
            Dict: 合并后的配置
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                # 递归合并嵌套字典
                self._merge_config(base[key], value)
            else:
                # 直接覆盖
                base[key] = value
        
        return base
    
    def create_default_config_file(self, config_path: str) -> bool:
        """
        创建默认配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            bool: 创建是否成功
        """
        return self.save_config(config_path)