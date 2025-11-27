"""配置文件管理器，支持不同网站的自定义优化规则"""

import os
import json
import logging
import shutil
import datetime
from typing import Dict, List, Optional, Any
import jsonschema
from jsonschema import validate

from .config_manager import ConfigManager

logger = logging.getLogger(__name__)


class ProfileManager:
    """配置文件管理器，负责管理不同网站的SEO优化配置"""
    
    def __init__(self, config_manager: ConfigManager):
        """
        初始化配置文件管理器
        
        Args:
            config_manager: 配置管理器实例
        """
        self.config_manager = config_manager
        self.profiles_dir = self._get_profiles_directory()
        self.current_profile = None
        
        # 确保配置文件目录存在
        os.makedirs(self.profiles_dir, exist_ok=True)
        
        # 定义配置文件的JSON模式
        self.profile_schema = self._get_profile_schema()
    
    def _get_profiles_directory(self) -> str:
        """
        获取配置文件存储目录
        
        Returns:
            str: 配置文件目录路径
        """
        # 从配置中获取目录，如果没有则使用默认路径
        try:
            profiles_dir = self.config_manager.get_config('profiles_directory')
            
            # 添加防御性检查，确保profiles_dir不会是ConfigManager对象
            if profiles_dir is None or isinstance(profiles_dir, type(self.config_manager)):
                logger.warning("获取配置文件目录失败或目录类型错误，使用默认路径")
                profiles_dir = None
            elif not isinstance(profiles_dir, str):
                logger.warning(f"配置文件目录类型错误，期望str但得到{type(profiles_dir).__name__}，使用默认路径")
                profiles_dir = None
        except Exception as e:
            logger.error(f"获取配置文件目录时出错: {str(e)}")
            profiles_dir = None
        
        if not profiles_dir:
            # 默认配置文件路径
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            profiles_dir = os.path.join(base_dir, 'profiles')
        
        return profiles_dir
    
    def _get_profile_schema(self) -> Dict[str, Any]:
        """
        获取配置文件的JSON模式定义
        
        Returns:
            Dict: JSON模式定义
        """
        return {
            "type": "object",
            "required": ["profile_name", "site_path", "created_at"],
            "properties": {
                "profile_name": {
                    "type": "string",
                    "description": "配置文件名称"
                },
                "site_path": {
                    "type": "string",
                    "description": "网站根目录路径"
                },
                "description": {
                    "type": "string",
                    "description": "配置文件描述"
                },
                "created_at": {
                    "type": "string",
                    "description": "创建时间"
                },
                "updated_at": {
                    "type": "string",
                    "description": "最后更新时间"
                },
                "base_config": {
                    "type": "object",
                    "properties": {
                        "max_pages": {"type": "integer", "minimum": 1},
                        "timeout": {"type": "integer", "minimum": 1},
                        "user_agent": {"type": "string"}
                    }
                },
                "analysis_config": {
                    "type": "object",
                    "properties": {
                        "analyze_content": {"type": "boolean"},
                        "analyze_keywords": {"type": "boolean"},
                        "analyze_performance": {"type": "boolean"},
                        "keywords": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "competitors": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    }
                },
                "optimization_config": {
                    "type": "object",
                    "properties": {
                        "enabled_optimizers": {
                            "type": "object",
                            "patternProperties": {
                                ".*": {"type": "boolean"}
                            }
                        },
                        "optimization_level": {
                            "type": "string",
                            "enum": ["basic", "moderate", "advanced"],
                            "default": "moderate"
                        },
                        "auto_apply": {
                            "type": "boolean",
                            "default": False
                        },
                        "max_changes_per_file": {
                            "type": "integer",
                            "minimum": 1
                        }
                    }
                },
                "backup_config": {
                    "type": "object",
                    "properties": {
                        "enabled": {"type": "boolean", "default": True},
                        "backup_directory": {"type": "string"},
                        "keep_backups": {"type": "integer", "minimum": 1, "maximum": 100},
                        "compress": {"type": "boolean", "default": True}
                    }
                },
                "file_types": {
                    "type": "object",
                    "properties": {
                        "html": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "css": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "javascript": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    }
                },
                "exclude_patterns": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "custom_rules": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["name", "description", "pattern"],
                        "properties": {
                            "name": {"type": "string"},
                            "description": {"type": "string"},
                            "pattern": {"type": "string"},
                            "severity": {
                                "type": "string",
                                "enum": ["low", "medium", "high", "critical"],
                                "default": "medium"
                            },
                            "auto_fix": {"type": "boolean", "default": False}
                        }
                    }
                }
            }
        }
    
    def create_profile(self, profile_name: str, site_path: str, description: str = "") -> Dict[str, Any]:
        """
        创建新的配置文件
        
        Args:
            profile_name: 配置文件名称
            site_path: 网站根目录路径
            description: 配置文件描述
            
        Returns:
            Dict: 创建结果
        """
        logger.info(f"创建新配置文件: {profile_name}, 网站路径: {site_path}")
        
        # 检查配置文件是否已存在
        if self._profile_exists(profile_name):
            return {
                'status': 'error',
                'error': f"配置文件已存在: {profile_name}"
            }
        
        # 检查网站路径是否存在
        if not os.path.exists(site_path):
            return {
                'status': 'error',
                'error': f"网站路径不存在: {site_path}"
            }
        
        try:
            # 创建配置文件内容
            profile_content = self._create_profile_template()
            profile_content['profile_name'] = profile_name
            profile_content['site_path'] = site_path
            profile_content['description'] = description
            profile_content['created_at'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            profile_content['updated_at'] = profile_content['created_at']
            
            # 验证配置文件
            self._validate_profile(profile_content)
            
            # 保存配置文件
            self._save_profile(profile_name, profile_content)
            
            logger.info(f"配置文件创建成功: {profile_name}")
            
            return {
                'status': 'success',
                'profile_name': profile_name,
                'profile_path': self._get_profile_path(profile_name)
            }
            
        except Exception as e:
            logger.error(f"创建配置文件失败: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def load_profile(self, profile_name: str) -> Dict[str, Any]:
        """
        加载配置文件
        
        Args:
            profile_name: 配置文件名称、路径或配置文件名（不带扩展名）
            
        Returns:
            Dict: 加载结果，包含配置内容
        """
        logger.info(f"加载配置文件: {profile_name}")
        
        # 1. 首先尝试直接使用用户提供的路径（如果是完整的JSON文件路径）
        if profile_name.endswith('.json') and os.path.exists(profile_name) and os.path.isfile(profile_name):
            profile_path = profile_name
        else:
            # 2. 从输入中提取配置文件名称（忽略路径部分）
            # 移除可能的.json扩展名
            name_part = profile_name
            if name_part.endswith('.json'):
                name_part = name_part[:-5]
            
            # 提取文件名部分（不包含路径）
            name_part = os.path.basename(name_part)
            logger.info(f"提取的配置文件名: {name_part}")
            
            # 3. 尝试在多个位置查找配置文件
            # 3.1 尝试在src/profiles目录中查找
            src_profiles_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "src", "profiles")
            src_profiles_path = os.path.join(src_profiles_dir, f"{name_part}.json")
            
            # 直接检查src/profiles目录
            if os.path.exists(src_profiles_path) and os.path.isfile(src_profiles_path):
                profile_path = src_profiles_path
                logger.info(f"在src/profiles目录中找到配置文件: {profile_path}")
            # 3.2 尝试在当前工作目录查找
            elif os.path.exists(os.path.join(os.getcwd(), f"{name_part}.json")):
                profile_path = os.path.join(os.getcwd(), f"{name_part}.json")
                logger.info(f"在当前目录中找到配置文件: {profile_path}")
            # 3.3 尝试使用默认配置目录
            elif self._profile_exists(name_part):
                profile_path = self._get_profile_path(name_part)
            else:
                # 3.4 尝试用户提供的路径（如果是目录，在其中查找）
                if os.path.isdir(profile_name):
                    potential_path = os.path.join(profile_name, f"{name_part}.json")
                    if os.path.exists(potential_path) and os.path.isfile(potential_path):
                        profile_path = potential_path
                    else:
                        return {
                            'status': 'error',
                            'error': f"在目录中未找到配置文件: {profile_name}"
                        }
                else:
                    return {
                        'status': 'error',
                        'error': f"配置文件不存在: {profile_name}"
                    }
        
        try:
            # 确保路径是文件而不是目录
            if not os.path.isfile(profile_path):
                return {
                    'status': 'error',
                    'error': f"指定的路径不是文件: {profile_path}"
                }
            
            # 读取配置文件
            with open(profile_path, 'r', encoding='utf-8') as f:
                profile_content = json.load(f)
            
            # 验证配置文件
            self._validate_profile(profile_content)
            
            # 更新当前配置文件
            self.current_profile = profile_name
            
            # 更新配置管理器
            self._update_config_manager(profile_content)
            
            logger.info(f"配置文件加载成功: {profile_name}")
            
            return {
                'status': 'success',
                'profile_name': profile_name,
                'profile_content': profile_content
            }
            
        except Exception as e:
            logger.error(f"加载配置文件失败: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def save_profile(self, profile_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        保存配置文件
        
        Args:
            profile_content: 配置内容
            
        Returns:
            Dict: 保存结果
        """
        # 检查是否有配置名称
        profile_name = profile_content.get('profile_name')
        if not profile_name:
            return {
                'status': 'error',
                'error': '配置文件缺少名称'
            }
        
        logger.info(f"保存配置文件: {profile_name}")
        
        try:
            # 更新时间戳
            profile_content['updated_at'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 验证配置文件
            self._validate_profile(profile_content)
            
            # 保存配置文件
            self._save_profile(profile_name, profile_content)
            
            # 更新当前配置文件
            self.current_profile = profile_name
            
            logger.info(f"配置文件保存成功: {profile_name}")
            
            return {
                'status': 'success',
                'profile_name': profile_name,
                'profile_path': self._get_profile_path(profile_name)
            }
            
        except Exception as e:
            logger.error(f"保存配置文件失败: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def delete_profile(self, profile_name: str) -> Dict[str, Any]:
        """
        删除配置文件
        
        Args:
            profile_name: 配置文件名称
            
        Returns:
            Dict: 删除结果
        """
        logger.info(f"删除配置文件: {profile_name}")
        
        # 检查配置文件是否存在
        if not self._profile_exists(profile_name):
            return {
                'status': 'error',
                'error': f"配置文件不存在: {profile_name}"
            }
        
        try:
            # 删除配置文件
            profile_path = self._get_profile_path(profile_name)
            os.remove(profile_path)
            
            # 如果删除的是当前配置文件，清除当前配置
            if self.current_profile == profile_name:
                self.current_profile = None
            
            logger.info(f"配置文件删除成功: {profile_name}")
            
            return {
                'status': 'success',
                'profile_name': profile_name
            }
            
        except Exception as e:
            logger.error(f"删除配置文件失败: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def list_profiles(self) -> List[Dict[str, Any]]:
        """
        列出所有配置文件
        
        Returns:
            List: 配置文件信息列表
        """
        profiles = []
        
        # 遍历配置文件目录
        for file in os.listdir(self.profiles_dir):
            if file.endswith('.json'):
                profile_name = file[:-5]  # 移除.json扩展名
                
                try:
                    # 读取配置文件信息
                    profile_content = self._load_profile_content(profile_name)
                    
                    # 收集基本信息
                    profile_info = {
                        'profile_name': profile_name,
                        'description': profile_content.get('description', ''),
                        'site_path': profile_content.get('site_path', ''),
                        'created_at': profile_content.get('created_at', ''),
                        'updated_at': profile_content.get('updated_at', ''),
                        'optimization_level': profile_content.get('optimization_config', {}).get('optimization_level', 'moderate'),
                        'file_path': self._get_profile_path(profile_name)
                    }
                    
                    profiles.append(profile_info)
                except Exception as e:
                    logger.error(f"读取配置文件信息失败 {profile_name}: {str(e)}")
        
        # 按更新时间排序
        profiles.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
        
        return profiles
    
    def get_profile(self, profile_name: str) -> Optional[Dict[str, Any]]:
        """
        获取配置文件内容
        
        Args:
            profile_name: 配置文件名称
            
        Returns:
            Dict: 配置文件内容，如果不存在则返回None
        """
        if not self._profile_exists(profile_name):
            return None
        
        try:
            return self._load_profile_content(profile_name)
        except Exception as e:
            logger.error(f"获取配置文件内容失败 {profile_name}: {str(e)}")
            return None
    
    def export_profile(self, profile_name: str, export_path: str) -> Dict[str, Any]:
        """
        导出配置文件
        
        Args:
            profile_name: 配置文件名称
            export_path: 导出路径
            
        Returns:
            Dict: 导出结果
        """
        logger.info(f"导出配置文件: {profile_name} 到 {export_path}")
        
        # 检查配置文件是否存在
        if not self._profile_exists(profile_name):
            return {
                'status': 'error',
                'error': f"配置文件不存在: {profile_name}"
            }
        
        try:
            # 获取配置文件路径
            profile_path = self._get_profile_path(profile_name)
            
            # 确保导出目录存在
            export_dir = os.path.dirname(export_path)
            if export_dir and not os.path.exists(export_dir):
                os.makedirs(export_dir, exist_ok=True)
            
            # 复制配置文件
            shutil.copy2(profile_path, export_path)
            
            logger.info(f"配置文件导出成功: {profile_name}")
            
            return {
                'status': 'success',
                'export_path': export_path
            }
            
        except Exception as e:
            logger.error(f"导出配置文件失败: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def import_profile(self, import_path: str, new_name: str = None) -> Dict[str, Any]:
        """
        导入配置文件
        
        Args:
            import_path: 导入路径
            new_name: 新的配置文件名称，如果为None则使用原文件名
            
        Returns:
            Dict: 导入结果
        """
        logger.info(f"导入配置文件: {import_path}")
        
        # 检查导入文件是否存在
        if not os.path.exists(import_path):
            return {
                'status': 'error',
                'error': f"导入文件不存在: {import_path}"
            }
        
        try:
            # 读取导入的配置文件
            with open(import_path, 'r', encoding='utf-8') as f:
                profile_content = json.load(f)
            
            # 验证配置文件
            self._validate_profile(profile_content)
            
            # 确定配置文件名称
            if new_name:
                profile_name = new_name
                profile_content['profile_name'] = new_name
            else:
                # 使用文件中的profile_name或从导入文件名提取
                profile_name = profile_content.get('profile_name')
                if not profile_name:
                    # 从文件名提取
                    base_name = os.path.basename(import_path)
                    profile_name = os.path.splitext(base_name)[0]
                    profile_content['profile_name'] = profile_name
            
            # 检查配置文件是否已存在
            if self._profile_exists(profile_name):
                # 添加时间戳避免覆盖
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                profile_name = f"{profile_name}_{timestamp}"
                profile_content['profile_name'] = profile_name
            
            # 更新时间戳
            profile_content['imported_at'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            profile_content['updated_at'] = profile_content['imported_at']
            
            # 保存配置文件
            self._save_profile(profile_name, profile_content)
            
            logger.info(f"配置文件导入成功: {profile_name}")
            
            return {
                'status': 'success',
                'profile_name': profile_name,
                'profile_path': self._get_profile_path(profile_name)
            }
            
        except Exception as e:
            logger.error(f"导入配置文件失败: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def update_profile_site_path(self, profile_name: str, new_site_path: str) -> Dict[str, Any]:
        """
        更新配置文件中的网站路径
        
        Args:
            profile_name: 配置文件名称
            new_site_path: 新的网站路径
            
        Returns:
            Dict: 更新结果
        """
        logger.info(f"更新配置文件网站路径: {profile_name} -> {new_site_path}")
        
        # 检查配置文件是否存在
        if not self._profile_exists(profile_name):
            return {
                'status': 'error',
                'error': f"配置文件不存在: {profile_name}"
            }
        
        # 检查新网站路径是否存在
        if not os.path.exists(new_site_path):
            return {
                'status': 'error',
                'error': f"新网站路径不存在: {new_site_path}"
            }
        
        try:
            # 读取配置文件
            profile_content = self._load_profile_content(profile_name)
            
            # 更新网站路径
            profile_content['site_path'] = new_site_path
            profile_content['updated_at'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 保存配置文件
            self._save_profile(profile_name, profile_content)
            
            # 如果是当前配置文件，更新配置管理器
            if self.current_profile == profile_name:
                self._update_config_manager(profile_content)
            
            logger.info(f"配置文件网站路径更新成功: {profile_name}")
            
            return {
                'status': 'success',
                'profile_name': profile_name,
                'new_site_path': new_site_path
            }
            
        except Exception as e:
            logger.error(f"更新配置文件网站路径失败: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _create_profile_template(self) -> Dict[str, Any]:
        """
        创建配置文件模板
        
        Returns:
            Dict: 配置文件模板内容
        """
        return {
            "profile_name": "",
            "site_path": "",
            "description": "",
            "created_at": "",
            "updated_at": "",
            "base_config": {
                "max_pages": 100,
                "timeout": 30,
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 SEO Optimizer Bot"
            },
            "analysis_config": {
                "analyze_content": True,
                "analyze_keywords": True,
                "analyze_performance": False,
                "keywords": [],
                "competitors": []
            },
            "optimization_config": {
                "enabled_optimizers": {
                    "meta_tags_optimizer": True,
                    "title_tags_optimizer": True,
                    "image_alt_optimizer": True,
                    "heading_structure_optimizer": True,
                    "link_optimizer": True,
                    "content_optimizer": False,
                    "keyword_optimizer": False,
                    "performance_optimizer": False
                },
                "optimization_level": "moderate",
                "auto_apply": False,
                "max_changes_per_file": 10
            },
            "backup_config": {
                "enabled": True,
                "backup_directory": "",
                "keep_backups": 5,
                "compress": True
            },
            "file_types": {
                "html": [".html", ".htm", ".php", ".asp", ".aspx", ".jsp"],
                "css": [".css"],
                "javascript": [".js"]
            },
            "exclude_patterns": [
                "node_modules/**",
                "__pycache__/**",
                ".git/**",
                ".svn/**",
                ".hg/**",
                "vendor/**",
                "dist/**",
                "build/**",
                "*.min.js",
                "*.min.css",
                "*.zip",
                "*.tar.gz",
                "*.bak",
                ".DS_Store"
            ],
            "custom_rules": []
        }
    
    def _profile_exists(self, profile_name: str) -> bool:
        """
        检查配置文件是否存在
        
        Args:
            profile_name: 配置文件名称
            
        Returns:
            bool: 配置文件是否存在
        """
        try:
            # 添加防御性检查
            if not profile_name or not isinstance(profile_name, str):
                return False
            
            profile_path = self._get_profile_path(profile_name)
            return os.path.exists(profile_path) and os.path.isfile(profile_path)
        except (TypeError, ValueError, OSError) as e:
            logger.warning(f"检查配置文件是否存在时出错: {e}")
            return False
    
    def _get_profile_path(self, profile_name: str) -> str:
        """
        获取配置文件路径
        
        Args:
            profile_name: 配置文件名称（不包含.json扩展名）
            
        Returns:
            str: 配置文件路径
        """
        # 添加防御性检查，确保profile_name是字符串
        if not isinstance(profile_name, str):
            raise TypeError(f"配置文件名称必须是字符串类型，收到: {type(profile_name).__name__}")
        
        # 避免重复添加.json扩展名
        if profile_name.endswith('.json'):
            profile_name = profile_name[:-5]
        
        return os.path.join(self.profiles_dir, f"{profile_name}.json")
    
    def _load_profile_content(self, profile_name: str) -> Dict[str, Any]:
        """
        加载配置文件内容
        
        Args:
            profile_name: 配置文件名称
            
        Returns:
            Dict[str, Any]: 配置文件内容
        
        Raises:
            ValueError: 当配置文件不存在或内容无效时
        """
        try:
            # 添加防御性检查
            if not profile_name or not isinstance(profile_name, str):
                raise ValueError("配置文件名称必须是有效的字符串")
            
            profile_path = self._get_profile_path(profile_name)
            
            # 确保文件存在且是文件类型
            if not os.path.exists(profile_path):
                raise ValueError(f"配置文件不存在: {profile_path}")
            
            if not os.path.isfile(profile_path):
                raise ValueError(f"指定的路径不是文件: {profile_path}")
            
            # 读取配置文件
            with open(profile_path, 'r', encoding='utf-8') as f:
                profile_content = json.load(f)
            
            # 确保加载的内容是字典类型
            if not isinstance(profile_content, dict):
                raise ValueError(f"配置文件内容必须是字典类型，收到: {type(profile_content).__name__}")
            
            # 返回配置内容的副本，防止意外修改
            return profile_content.copy()
        except json.JSONDecodeError as e:
            logger.error(f"解析配置文件失败: {e}")
            raise ValueError(f"配置文件格式错误: {e}")
        except Exception as e:
            logger.error(f"加载配置文件内容时出错: {e}")
            raise ValueError(f"加载配置文件失败: {e}")
    
    def _save_profile(self, profile_name: str, profile_content: Dict[str, Any]):
        """
        保存配置文件
        
        Args:
            profile_name: 配置文件名称
            profile_content: 配置内容
        """
        profile_path = self._get_profile_path(profile_name)
        
        with open(profile_path, 'w', encoding='utf-8') as f:
            json.dump(profile_content, f, ensure_ascii=False, indent=2)
    
    def _validate_profile(self, profile_content: Dict[str, Any]):
        """
        验证配置文件的有效性
        
        Args:
            profile_content: 配置内容
            
        Raises:
            jsonschema.ValidationError: 如果配置文件无效
        """
        validate(instance=profile_content, schema=self.profile_schema)
    
    def _update_config_manager(self, profile_content: Dict[str, Any]):
        """
        更新配置管理器
        
        Args:
            profile_content: 配置内容
        """
        # 更新基本配置
        for key, value in profile_content.items():
            if key not in ['profile_name', 'description', 'created_at', 'updated_at', 'imported_at']:
                self.config_manager.set_config(key, value)