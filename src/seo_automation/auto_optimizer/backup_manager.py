"""备份和恢复管理器，用于在优化前备份网站文件并支持恢复操作"""

import os
import shutil
import logging
import datetime
import zipfile
import json
from typing import Dict, List, Optional, Any
import hashlib

from .config_manager import ConfigManager

logger = logging.getLogger(__name__)


class BackupManager:
    """备份和恢复管理器，负责网站文件的备份和恢复操作"""
    
    def __init__(self, config_manager: ConfigManager):
        """
        初始化备份管理器
        
        Args:
            config_manager: 配置管理器实例
        """
        logger.info("开始初始化BackupManager")
        logger.info(f"传入的config_manager类型: {type(config_manager)}")
        
        # 防御性检查：确保传入的是ConfigManager实例
        if not isinstance(config_manager, ConfigManager):
            logger.error(f"传入的参数不是ConfigManager实例: {type(config_manager)}")
            # 创建一个默认的ConfigManager实例作为后备
            config_manager = ConfigManager()
        
        self.config_manager = config_manager
        
        # 获取配置项 - 添加严格的类型检查
        try:
            # 获取网站路径
            site_path = config_manager.get_config('site_path')
            logger.info(f"从配置获取site_path: {site_path}, 类型: {type(site_path).__name__ if site_path is not None else 'None'}")
            
            # 确保site_path是字符串
            if site_path is None or not isinstance(site_path, str):
                logger.warning(f"网站路径无效或不是字符串类型，使用当前目录")
                self.site_path = '.'
            else:
                self.site_path = site_path
            
            logger.info(f"最终使用的site_path: {self.site_path}, 类型: {type(self.site_path).__name__}")
            
            # 获取备份配置
            backup_config = config_manager.get_config('backup_config')
            logger.info(f"从配置获取backup_config: {backup_config}, 类型: {type(backup_config).__name__ if backup_config is not None else 'None'}")
            
            # 确保backup_config是字典类型
            if isinstance(backup_config, ConfigManager):
                logger.error("错误：backup_config是ConfigManager实例，这是不允许的")
                self.backup_config = {}
            else:
                self.backup_config = backup_config if isinstance(backup_config, dict) else {}
            
            logger.info(f"最终使用的backup_config: {self.backup_config}, 类型: {type(self.backup_config).__name__}")
            
            # 获取其他配置项，同样进行防御性检查
            file_types = config_manager.get_config('file_types')
            self.file_types = {}
            if file_types is not None and isinstance(file_types, dict) and not isinstance(file_types, ConfigManager):
                self.file_types = file_types
                
            exclude_patterns = config_manager.get_config('exclude_patterns')
            self.exclude_patterns = []
            if exclude_patterns is not None and isinstance(exclude_patterns, list) and not isinstance(exclude_patterns, ConfigManager):
                self.exclude_patterns = exclude_patterns
        except Exception as e:
            logger.error(f"获取配置项时发生错误: {str(e)}")
            # 设置默认值
            self.site_path = '.'
            self.backup_config = {}
            self.file_types = {}
            self.exclude_patterns = []
        
        # 备份存储路径 - 确保返回的是字符串
        try:
            self.backup_dir = self._get_backup_directory()
            # 额外检查backup_dir是否为字符串
            if not isinstance(self.backup_dir, str):
                logger.error(f"_get_backup_directory返回非字符串类型: {type(self.backup_dir)}")
                self.backup_dir = './seo_backups'
        except Exception as e:
            logger.error(f"获取备份目录时发生错误: {str(e)}")
            self.backup_dir = './seo_backups'
        
        logger.info(f"最终使用的backup_dir: {self.backup_dir}, 类型: {type(self.backup_dir).__name__}")
        
        # 最近一次备份信息
        self.last_backup_info = None
        
        # 确保备份目录存在 - 添加严格的类型检查
        try:
            logger.info(f"开始创建备份目录: {self.backup_dir}")
            
            # 双重确保backup_dir是字符串
            if isinstance(self.backup_dir, str):
                # 再次检查路径参数，确保不是ConfigManager对象
                if 'ConfigManager' in str(type(self.backup_dir)):
                    raise TypeError("路径不能是ConfigManager对象")
                
                os.makedirs(self.backup_dir, exist_ok=True)
                logger.info(f"备份目录创建成功: {self.backup_dir}")
            else:
                logger.error(f"备份目录不是字符串类型: {type(self.backup_dir)}")
                # 使用当前目录作为备份目录
                self.backup_dir = './seo_backups'
                os.makedirs(self.backup_dir, exist_ok=True)
                logger.info(f"使用默认备份目录: {self.backup_dir}")
        except TypeError as e:
            logger.error(f"创建备份目录时发生类型错误: {str(e)}")
            # 特别处理ConfigManager相关的错误
            if 'ConfigManager' in str(e):
                logger.error("错误：ConfigManager对象被错误地用作路径")
                logger.error(f"导致错误的对象类型: {type(self.backup_dir)}")
            # 使用当前目录作为备份目录
            self.backup_dir = './seo_backups'
            os.makedirs(self.backup_dir, exist_ok=True)
            logger.info(f"使用默认备份目录: {self.backup_dir}")
        except Exception as e:
            logger.error(f"创建备份目录失败: {str(e)}")
            # 使用当前目录作为备份目录
            self.backup_dir = './seo_backups'
            os.makedirs(self.backup_dir, exist_ok=True)
            logger.info(f"使用默认备份目录: {self.backup_dir}")
        
        logger.info("BackupManager初始化完成")
    
    def _get_backup_directory(self) -> str:
        """
        获取备份存储目录
        
        Returns:
            str: 备份目录路径
        """
        try:
            logger.info("开始获取备份目录")
            
            # 添加调试信息
            logger.info(f"backup_config类型: {type(self.backup_config)}, 值: {self.backup_config}")
            logger.info(f"site_path类型: {type(self.site_path)}, 值: {self.site_path}")
            
            # 默认备份目录
            default_backup_dir = './seo_backups'
            
            # 从配置中获取备份路径，如果没有则使用默认路径
            backup_dir = None
            if isinstance(self.backup_config, dict):
                backup_dir = self.backup_config.get('backup_directory')
                logger.info(f"从backup_config获取的backup_dir: {backup_dir}")
                
                # 检查backup_dir是否为ConfigManager实例
                if isinstance(backup_dir, ConfigManager):
                    logger.error("错误：backup_directory是ConfigManager实例，这是不允许的")
                    backup_dir = None
                # 检查backup_dir是否为字符串类型
                elif backup_dir is not None and not isinstance(backup_dir, str):
                    logger.error(f"backup_directory不是字符串类型: {type(backup_dir)}")
                    backup_dir = None
            
            # 如果没有有效的备份路径，则使用默认路径
            if not backup_dir:
                logger.info("没有有效的备份路径配置，使用默认路径")
                
                # 尝试基于site_path构建默认路径
                if isinstance(self.site_path, str) and self.site_path != '.':
                    try:
                        parent_dir = os.path.dirname(self.site_path)
                        # 再次确保parent_dir是字符串
                        if isinstance(parent_dir, str):
                            backup_dir = os.path.join(parent_dir, 'seo_backups')
                            logger.info(f"使用基于site_path的默认备份路径: {backup_dir}")
                        else:
                            logger.error(f"parent_dir不是字符串类型: {type(parent_dir)}")
                            backup_dir = default_backup_dir
                    except Exception as e:
                        logger.error(f"构建默认备份路径失败: {str(e)}")
                        backup_dir = default_backup_dir
                else:
                    backup_dir = default_backup_dir
                    logger.info(f"使用当前目录作为备份目录: {backup_dir}")
            
            # 最终验证backup_dir是字符串
            if not isinstance(backup_dir, str):
                logger.error(f"backup_dir不是字符串类型: {type(backup_dir)}")
                backup_dir = default_backup_dir
            
            logger.info(f"最终返回的备份目录: {backup_dir}, 类型: {type(backup_dir).__name__}")
            return backup_dir
        except Exception as e:
            logger.error(f"获取备份目录失败: {str(e)}")
            logger.error(f"异常类型: {type(e).__name__}")
            return './seo_backups'
    
    def create_backup(self, description: str = "") -> Dict[str, Any]:
        """
        创建网站文件的备份
        
        Args:
            description: 备份描述
            
        Returns:
            Dict: 备份结果信息
        """
        logger.info(f"开始创建备份，描述: {description}")
        
        try:
            # 生成备份ID和文件名
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_id = f"backup_{timestamp}"
            
            # 生成备份文件名
            backup_filename = f"{backup_id}.zip"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # 记录备份开始时间
            start_time = datetime.datetime.now()
            
            # 统计信息
            stats = {
                'total_files': 0,
                'backup_files': 0,
                'skipped_files': 0,
                'error_files': 0
            }
            
            # 创建ZIP文件
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # 遍历网站目录并添加文件到ZIP
                for root, dirs, files in os.walk(self.site_path):
                    # 过滤目录
                    dirs[:] = [d for d in dirs if not self._should_exclude(os.path.join(root, d), 'dir')]
                    
                    for file in files:
                        file_path = os.path.join(root, file)
                        
                        # 检查是否应该排除此文件
                        if self._should_exclude(file_path, 'file'):
                            stats['skipped_files'] += 1
                            continue
                        
                        # 计算相对路径
                        rel_path = os.path.relpath(file_path, self.site_path)
                        
                        try:
                            # 添加文件到ZIP
                            zipf.write(file_path, rel_path)
                            stats['backup_files'] += 1
                            logger.debug(f"备份文件: {rel_path}")
                        except Exception as e:
                            stats['error_files'] += 1
                            logger.warning(f"备份文件失败 {file_path}: {str(e)}")
                        finally:
                            stats['total_files'] += 1
            
            # 计算备份文件大小
            backup_size = os.path.getsize(backup_path)
            
            # 计算备份文件MD5
            backup_md5 = self._calculate_file_md5(backup_path)
            
            # 备份信息
            backup_info = {
                'backup_id': backup_id,
                'timestamp': timestamp,
                'description': description,
                'site_path': self.site_path,
                'backup_path': backup_path,
                'backup_size': backup_size,
                'backup_md5': backup_md5,
                'stats': stats,
                'duration_seconds': (datetime.datetime.now() - start_time).total_seconds()
            }
            
            # 保存备份信息到JSON文件
            info_file_path = os.path.join(self.backup_dir, f"{backup_id}.json")
            with open(info_file_path, 'w', encoding='utf-8') as f:
                json.dump(backup_info, f, ensure_ascii=False, indent=2)
            
            # 更新最近备份信息
            self.last_backup_info = backup_info
            
            # 清理旧备份
            self._cleanup_old_backups()
            
            logger.info(f"备份创建成功: {backup_id}, 备份文件大小: {backup_size} 字节, 备份文件数: {stats['backup_files']}")
            
            return {
                'status': 'success',
                'backup_info': backup_info
            }
            
        except Exception as e:
            logger.error(f"创建备份失败: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _should_exclude(self, path: str, item_type: str) -> bool:
        """
        判断是否应该排除指定的路径
        
        Args:
            path: 要检查的路径
            item_type: 项目类型 ('file' 或 'dir')
            
        Returns:
            bool: 如果应该排除则返回True
        """
        # 相对路径用于模式匹配
        rel_path = os.path.relpath(path, self.site_path)
        
        # 检查排除模式
        for pattern in self.exclude_patterns:
            # 转换路径分隔符为统一格式
            pattern_norm = pattern.replace('/', os.path.sep).replace('\\', os.path.sep)
            
            # 检查路径是否匹配模式
            if self._match_pattern(rel_path, pattern_norm):
                return True
        
        # 检查文件类型
        if item_type == 'file':
            # 获取文件扩展名
            ext = os.path.splitext(path)[1].lower()
            
            # 检查是否在需要备份的类型中
            html_exts = self.file_types.get('html', ['.html', '.htm'])
            css_exts = self.file_types.get('css', ['.css'])
            js_exts = self.file_types.get('javascript', ['.js'])
            
            # 只备份指定类型的文件
            backup_extensions = html_exts + css_exts + js_exts
            
            if ext not in backup_extensions:
                return True
        
        # 排除隐藏文件和目录
        basename = os.path.basename(path)
        if basename.startswith('.'):
            return True
        
        # 排除备份目录本身
        if os.path.commonpath([path, self.backup_dir]) == self.backup_dir:
            return True
        
        # 排除其他常见不需要备份的目录
        common_exclude_dirs = ['node_modules', '__pycache__', '.git', '.svn', '.hg', 'vendor', 'dist', 'build']
        if item_type == 'dir' and basename in common_exclude_dirs:
            return True
        
        return False
    
    def _match_pattern(self, path: str, pattern: str) -> bool:
        """
        检查路径是否匹配模式
        
        Args:
            path: 要检查的路径
            pattern: 模式字符串，支持通配符 * 和 ?
            
        Returns:
            bool: 如果路径匹配模式则返回True
        """
        # 简化的通配符匹配
        # 将模式转换为正则表达式
        regex_pattern = pattern.replace('.', '\\.')
        regex_pattern = regex_pattern.replace('*', '.*')
        regex_pattern = regex_pattern.replace('?', '.')
        regex_pattern = f"^{regex_pattern}$"
        
        import re
        return bool(re.match(regex_pattern, path))
    
    def _calculate_file_md5(self, file_path: str) -> str:
        """
        计算文件的MD5哈希值
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: MD5哈希值
        """
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b"").send(None):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.error(f"计算文件MD5失败 {file_path}: {str(e)}")
            return ""
    
    def restore_from_backup(self, backup_id: str = None) -> Dict[str, Any]:
        """
        从备份恢复网站文件
        
        Args:
            backup_id: 备份ID，如果为None则使用最近的备份
            
        Returns:
            Dict: 恢复结果信息
        """
        logger.info(f"开始从备份恢复，备份ID: {backup_id}")
        
        # 获取备份信息
        backup_info = self._get_backup_info(backup_id)
        if not backup_info:
            return {
                'status': 'error',
                'error': f"找不到备份信息: {backup_id}"
            }
        
        backup_path = backup_info['backup_path']
        
        # 检查备份文件是否存在
        if not os.path.exists(backup_path):
            return {
                'status': 'error',
                'error': f"备份文件不存在: {backup_path}"
            }
        
        # 验证备份文件完整性
        if not self._verify_backup_integrity(backup_info):
            return {
                'status': 'error',
                'error': f"备份文件完整性验证失败: {backup_path}"
            }
        
        try:
            # 记录恢复开始时间
            start_time = datetime.datetime.now()
            
            # 统计信息
            stats = {
                'total_files': 0,
                'restored_files': 0,
                'error_files': 0
            }
            
            # 创建临时目录用于解压
            temp_dir = os.path.join(self.backup_dir, f"temp_restore_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}")
            os.makedirs(temp_dir, exist_ok=True)
            
            try:
                # 解压备份文件到临时目录
                with zipfile.ZipFile(backup_path, 'r') as zipf:
                    zipf.extractall(temp_dir)
                
                # 遍历解压后的文件并恢复
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        temp_file_path = os.path.join(root, file)
                        
                        # 计算目标路径
                        rel_path = os.path.relpath(temp_file_path, temp_dir)
                        target_path = os.path.join(self.site_path, rel_path)
                        
                        try:
                            # 确保目标目录存在
                            os.makedirs(os.path.dirname(target_path), exist_ok=True)
                            
                            # 复制文件
                            shutil.copy2(temp_file_path, target_path)
                            stats['restored_files'] += 1
                            logger.debug(f"恢复文件: {rel_path}")
                        except Exception as e:
                            stats['error_files'] += 1
                            logger.warning(f"恢复文件失败 {target_path}: {str(e)}")
                        finally:
                            stats['total_files'] += 1
                
                # 恢复信息
                restore_info = {
                    'backup_id': backup_info['backup_id'],
                    'restore_time': datetime.datetime.now().strftime("%Y%m%d_%H%M%S"),
                    'stats': stats,
                    'duration_seconds': (datetime.datetime.now() - start_time).total_seconds(),
                    'original_backup_info': backup_info
                }
                
                # 保存恢复记录
                restore_log_path = os.path.join(self.backup_dir, f"restore_{restore_info['restore_time']}.json")
                with open(restore_log_path, 'w', encoding='utf-8') as f:
                    json.dump(restore_info, f, ensure_ascii=False, indent=2)
                
                logger.info(f"从备份恢复成功: {backup_info['backup_id']}, 恢复文件数: {stats['restored_files']}")
                
                return {
                    'status': 'success',
                    'restore_info': restore_info
                }
                
            finally:
                # 清理临时目录
                if os.path.exists(temp_dir):
                    try:
                        shutil.rmtree(temp_dir)
                    except Exception as e:
                        logger.warning(f"清理临时目录失败 {temp_dir}: {str(e)}")
        
        except Exception as e:
            logger.error(f"从备份恢复失败: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _get_backup_info(self, backup_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        获取备份信息
        
        Args:
            backup_id: 备份ID，如果为None则返回最近的备份
            
        Returns:
            Dict: 备份信息，如果找不到则返回None
        """
        # 如果提供了backup_id，直接获取
        if backup_id:
            info_file_path = os.path.join(self.backup_dir, f"{backup_id}.json")
            if os.path.exists(info_file_path):
                try:
                    with open(info_file_path, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except Exception as e:
                    logger.error(f"读取备份信息失败 {info_file_path}: {str(e)}")
        
        # 如果没有提供backup_id或找不到指定的备份，获取最近的备份
        return self.get_latest_backup_info()
    
    def get_latest_backup_info(self) -> Optional[Dict[str, Any]]:
        """
        获取最近的备份信息
        
        Returns:
            Dict: 最近的备份信息，如果没有备份则返回None
        """
        # 从备份目录中查找所有备份信息文件
        backup_info_files = []
        for file in os.listdir(self.backup_dir):
            if file.endswith('.json') and file.startswith('backup_'):
                backup_info_files.append(os.path.join(self.backup_dir, file))
        
        # 按文件名排序（基于时间戳）
        backup_info_files.sort(reverse=True)
        
        # 读取最新的备份信息
        if backup_info_files:
            try:
                with open(backup_info_files[0], 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"读取最新备份信息失败: {str(e)}")
        
        return None
    
    def _verify_backup_integrity(self, backup_info: Dict[str, Any]) -> bool:
        """
        验证备份文件的完整性
        
        Args:
            backup_info: 备份信息
            
        Returns:
            bool: 如果备份文件完整则返回True
        """
        backup_path = backup_info['backup_path']
        expected_md5 = backup_info.get('backup_md5', '')
        
        if not expected_md5:
            logger.warning("备份信息中没有MD5值，跳过完整性验证")
            return True
        
        try:
            actual_md5 = self._calculate_file_md5(backup_path)
            if actual_md5 == expected_md5:
                return True
            else:
                logger.error(f"备份文件MD5不匹配。期望: {expected_md5}, 实际: {actual_md5}")
                return False
        except Exception as e:
            logger.error(f"验证备份完整性失败: {str(e)}")
            return False
    
    def _cleanup_old_backups(self):
        """
        清理旧备份文件，保留指定数量的最新备份
        """
        # 获取要保留的备份数量
        keep_count = self.backup_config.get('keep_backups', 5)
        
        if keep_count <= 0:
            return
        
        # 获取所有备份信息文件
        backup_info_files = []
        backup_files = []
        
        for file in os.listdir(self.backup_dir):
            full_path = os.path.join(self.backup_dir, file)
            if file.endswith('.json') and file.startswith('backup_'):
                backup_info_files.append(full_path)
            elif file.endswith('.zip') and file.startswith('backup_'):
                backup_files.append(full_path)
        
        # 按文件名排序（基于时间戳）
        backup_info_files.sort(reverse=True)
        backup_files.sort(reverse=True)
        
        # 删除超过保留数量的旧备份
        for info_file in backup_info_files[keep_count:]:
            try:
                os.remove(info_file)
                logger.info(f"删除旧备份信息: {info_file}")
            except Exception as e:
                logger.error(f"删除旧备份信息失败 {info_file}: {str(e)}")
        
        for backup_file in backup_files[keep_count:]:
            try:
                os.remove(backup_file)
                logger.info(f"删除旧备份文件: {backup_file}")
            except Exception as e:
                logger.error(f"删除旧备份文件失败 {backup_file}: {str(e)}")
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """
        列出所有可用的备份
        
        Returns:
            List: 备份信息列表，按时间倒序排列
        """
        backups = []
        
        # 获取所有备份信息文件
        for file in os.listdir(self.backup_dir):
            if file.endswith('.json') and file.startswith('backup_'):
                info_file_path = os.path.join(self.backup_dir, file)
                
                try:
                    with open(info_file_path, 'r', encoding='utf-8') as f:
                        backup_info = json.load(f)
                    
                    # 检查备份文件是否存在
                    backup_path = backup_info['backup_path']
                    backup_info['backup_exists'] = os.path.exists(backup_path)
                    
                    backups.append(backup_info)
                except Exception as e:
                    logger.error(f"读取备份信息失败 {info_file_path}: {str(e)}")
        
        # 按时间戳排序
        backups.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return backups
    
    def delete_backup(self, backup_id: str) -> Dict[str, Any]:
        """
        删除指定的备份
        
        Args:
            backup_id: 备份ID
            
        Returns:
            Dict: 删除结果
        """
        logger.info(f"删除备份: {backup_id}")
        
        info_file_path = os.path.join(self.backup_dir, f"{backup_id}.json")
        backup_path = os.path.join(self.backup_dir, f"{backup_id}.zip")
        
        deleted_files = []
        errors = []
        
        # 删除备份信息文件
        if os.path.exists(info_file_path):
            try:
                os.remove(info_file_path)
                deleted_files.append(info_file_path)
            except Exception as e:
                errors.append(f"删除备份信息文件失败: {str(e)}")
        
        # 删除备份文件
        if os.path.exists(backup_path):
            try:
                os.remove(backup_path)
                deleted_files.append(backup_path)
            except Exception as e:
                errors.append(f"删除备份文件失败: {str(e)}")
        
        if errors:
            return {
                'status': 'partial',
                'deleted_files': deleted_files,
                'errors': errors
            }
        elif deleted_files:
            return {
                'status': 'success',
                'deleted_files': deleted_files
            }
        else:
            return {
                'status': 'not_found',
                'message': f"备份不存在: {backup_id}"
            }
    
    def get_backup_stats(self) -> Dict[str, Any]:
        """
        获取备份统计信息
        
        Returns:
            Dict: 备份统计信息
        """
        backups = self.list_backups()
        
        # 计算总大小
        total_size = sum(b['backup_size'] for b in backups if b.get('backup_exists', False))
        
        # 计算按日期分组的备份数量
        backups_by_date = {}
        for backup in backups:
            date = backup['timestamp'].split('_')[0]  # YYYYMMDD
            if date not in backups_by_date:
                backups_by_date[date] = 0
            backups_by_date[date] += 1
        
        # 获取最新备份信息
        latest_backup = backups[0] if backups else None
        
        return {
            'total_backups': len(backups),
            'available_backups': sum(1 for b in backups if b.get('backup_exists', False)),
            'total_size': total_size,
            'backups_by_date': backups_by_date,
            'latest_backup': latest_backup,
            'backup_directory': self.backup_dir
        }