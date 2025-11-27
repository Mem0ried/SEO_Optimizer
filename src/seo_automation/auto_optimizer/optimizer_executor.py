"""SEO优化执行器，根据优化建议执行实际的SEO优化操作"""

import os
import logging
import shutil
from typing import Dict, List, Any, Optional
import re
from bs4 import BeautifulSoup

from .config_manager import ConfigManager

logger = logging.getLogger(__name__)


class OptimizerExecutor:
    """SEO优化执行器"""
    
    def __init__(self, config_manager: ConfigManager):
        """
        初始化优化执行器
        
        Args:
            config_manager: 配置管理器实例
        """
        self.config_manager = config_manager
        
        # 获取site_path并添加防御性检查
        site_path = config_manager.get_config('site_path')
        logger.info(f"OptimizerExecutor: site_path类型: {type(site_path)}, 值: {site_path}")
        
        # 防止ConfigManager实例被用作路径
        if isinstance(site_path, ConfigManager):
            logger.error("错误：site_path是ConfigManager实例，使用默认值")
            self.site_path = '.'
        elif isinstance(site_path, str):
            self.site_path = site_path
        else:
            logger.error(f"site_path不是字符串类型: {type(site_path)}")
            self.site_path = '.'
        
        # 获取备份目录配置并添加防御性检查
        backup_dir = config_manager.get_config('backup_dir')
        logger.info(f"OptimizerExecutor: backup_dir类型: {type(backup_dir)}")
        
        # 默认备份目录
        default_backup_dir = os.path.join(self.site_path, '.seo_backup')
        
        # 防止ConfigManager实例被用作路径
        if isinstance(backup_dir, ConfigManager):
            logger.error("错误：backup_dir是ConfigManager实例，使用默认值")
            self.backup_dir = default_backup_dir
        elif isinstance(backup_dir, str) and backup_dir:
            self.backup_dir = backup_dir
        else:
            self.backup_dir = default_backup_dir
        
        logger.info(f"OptimizerExecutor: 最终使用的backup_dir: {self.backup_dir}, 类型: {type(self.backup_dir).__name__}")
        
        # 获取优化配置并添加防御性检查
        optimization_config = config_manager.get_config('optimization_config')
        logger.info(f"OptimizerExecutor: optimization_config类型: {type(optimization_config)}")
        
        if isinstance(optimization_config, ConfigManager):
            logger.error("错误：optimization_config是ConfigManager实例，使用空字典")
            self.optimization_config = {}
        elif isinstance(optimization_config, dict):
            self.optimization_config = optimization_config
        else:
            self.optimization_config = {}
        
        # 初始化执行结果
        self.execution_results = {
            'success_count': 0,
            'failed_count': 0,
            'skipped_count': 0,
            'operations': []
        }
    
    def execute_optimizations(self, suggestions: List[Dict[str, Any]], 
                             selected_suggestions: List[str] = None, 
                             dry_run: bool = False) -> Dict[str, Any]:
        """
        执行SEO优化
        
        Args:
            suggestions: 优化建议列表
            selected_suggestions: 要执行的建议ID列表，None表示执行所有可自动修复的建议
            dry_run: 是否仅模拟执行而不实际修改文件
            
        Returns:
            Dict: 执行结果
        """
        logger.info("开始执行SEO优化...")
        
        try:
            # 清空之前的执行结果
            self.execution_results = {
                'success_count': 0,
                'failed_count': 0,
                'skipped_count': 0,
                'operations': []
            }
            
            # 如果不是模拟运行，先创建备份
            if not dry_run:
                self._create_backup()
            
            # 添加详细的调试日志
            logger.critical("CRITICAL: 进入筛选执行建议逻辑")
            logger.critical(f"CRITICAL: selected_suggestions: {selected_suggestions}")
            logger.critical(f"CRITICAL: 输入建议数量: {len(suggestions)}")
            for i, suggestion in enumerate(suggestions):
                logger.critical(f"CRITICAL: 建议{i+1}: auto_fixable={suggestion.get('auto_fixable', 'NOT_SET')}, id={suggestion.get('id')}")
            
            # 筛选要执行的建议
            to_execute = []
            # 修复逻辑：检查selected_suggestions是否为None或空列表
            has_selected_suggestions = selected_suggestions is not None and len(selected_suggestions) > 0
            logger.critical(f"CRITICAL: has_selected_suggestions: {has_selected_suggestions}")
            
            for suggestion in suggestions:
                # 如果指定了非空的selected_suggestions，则只执行指定的建议
                if has_selected_suggestions:
                    if suggestion.get('id') in selected_suggestions:
                        logger.critical(f"CRITICAL: 建议 {suggestion.get('id')} 被选中执行")
                        to_execute.append(suggestion)
                    else:
                        logger.critical(f"CRITICAL: 建议 {suggestion.get('id')} 未在选中列表中")
                # 否则只执行可自动修复的建议
                elif suggestion.get('auto_fixable', False):
                    logger.critical(f"CRITICAL: 建议 {suggestion.get('id')} auto_fixable=True，添加到执行列表")
                    to_execute.append(suggestion)
                else:
                    logger.critical(f"CRITICAL: 建议 {suggestion.get('id')} auto_fixable={suggestion.get('auto_fixable')}，跳过")
            
            logger.critical(f"CRITICAL: 最终执行建议数量: {len(to_execute)}")
            logger.info(f"将执行 {len(to_execute)} 项优化操作")
            
            # 执行优化
            for suggestion in to_execute:
                self._execute_suggestion(suggestion, dry_run)
            
            logger.info(f"优化执行完成 - 成功: {self.execution_results['success_count']}, "
                      f"失败: {self.execution_results['failed_count']}, "
                      f"跳过: {self.execution_results['skipped_count']}")
            
            return self.execution_results
            
        except Exception as e:
            logger.error(f"执行优化时发生错误: {str(e)}")
            # 如果不是模拟运行，尝试恢复备份
            if not dry_run:
                try:
                    self._restore_backup()
                except:
                    logger.error("恢复备份失败")
            raise
    
    def _execute_suggestion(self, suggestion: Dict[str, Any], dry_run: bool):
        """执行单个优化建议"""
        issue = suggestion.get('issue')
        page = suggestion.get('page')
        
        # 获取本地文件路径
        file_path = self._get_local_file_path(page)
        if not file_path or not os.path.exists(file_path):
            logger.warning(f"文件不存在或无法访问: {file_path}")
            self._record_operation(suggestion, 'skipped', '文件不存在或无法访问')
            self.execution_results['skipped_count'] += 1
            return
        
        try:
            # 根据问题类型执行不同的优化操作
            if issue == 'missing_meta_description':
                self._fix_missing_meta_description(file_path, suggestion, dry_run)
            elif issue == 'missing_image_alt':
                self._fix_missing_image_alt(file_path, suggestion, dry_run)
            elif issue == 'title_too_long':
                self._fix_title_too_long(file_path, suggestion, dry_run)
            elif issue == 'meta_description_too_long':
                self._fix_meta_description_too_long(file_path, suggestion, dry_run)
            else:
                logger.warning(f"不支持的优化类型: {issue}")
                self._record_operation(suggestion, 'skipped', '不支持的优化类型')
                self.execution_results['skipped_count'] += 1
        except Exception as e:
            logger.error(f"执行优化时出错: {str(e)}")
            self._record_operation(suggestion, 'failed', str(e))
            self.execution_results['failed_count'] += 1
    
    def _fix_missing_meta_description(self, file_path: str, suggestion: Dict[str, Any], dry_run: bool):
        """修复缺少元描述的问题"""
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # 解析HTML
        soup = BeautifulSoup(content, 'lxml')
        
        # 检查是否已经有meta description
        existing_meta = soup.find('meta', attrs={'name': 'description'})
        if existing_meta:
            logger.info(f"文件已有meta description: {file_path}")
            self._record_operation(suggestion, 'skipped', '文件已有meta description')
            self.execution_results['skipped_count'] += 1
            return
        
        # 获取页面标题作为参考
        title = soup.title.string.strip() if soup.title and soup.title.string else '页面'
        
        # 生成meta description
        meta_description = self._generate_meta_description(title, content)
        
        # 创建新的meta标签
        new_meta = soup.new_tag('meta')
        new_meta['name'] = 'description'
        new_meta['content'] = meta_description
        
        # 添加到head标签
        head = soup.find('head')
        if head:
            head.append(new_meta)
            
            # 保存修改
            if not dry_run:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(str(soup))
                logger.info(f"已添加meta description: {file_path}")
                self._record_operation(suggestion, 'success', f'已添加meta description: {meta_description}')
                self.execution_results['success_count'] += 1
            else:
                logger.info(f"[模拟] 将添加meta description: {file_path}")
                self._record_operation(suggestion, 'success', f'[模拟] 将添加meta description: {meta_description}')
                self.execution_results['success_count'] += 1
        else:
            logger.warning(f"找不到head标签: {file_path}")
            self._record_operation(suggestion, 'failed', '找不到head标签')
            self.execution_results['failed_count'] += 1
    
    def _fix_missing_image_alt(self, file_path: str, suggestion: Dict[str, Any], dry_run: bool):
        """修复缺少图片alt属性的问题"""
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # 解析HTML
        soup = BeautifulSoup(content, 'lxml')
        
        # 查找所有没有alt属性的图片
        images_without_alt = [img for img in soup.find_all('img') if not img.get('alt')]
        
        # 检查是否是特定图片的修复
        image_src = None
        if '图片缺少alt属性:' in suggestion.get('description', ''):
            # 从描述中提取图片src
            match = re.search(r'图片缺少alt属性: (.*)', suggestion['description'])
            if match:
                image_src = match.group(1)
        
        fixed_count = 0
        
        # 为图片添加alt属性
        for img in images_without_alt:
            # 如果指定了特定图片，只修复该图片
            if image_src and img.get('src') != image_src:
                continue
            
            # 生成alt文本
            alt_text = self._generate_image_alt(img)
            img['alt'] = alt_text
            fixed_count += 1
        
        # 如果有修复，保存文件
        if fixed_count > 0:
            if not dry_run:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(str(soup))
                logger.info(f"已为 {fixed_count} 张图片添加alt属性: {file_path}")
                self._record_operation(suggestion, 'success', f'已为 {fixed_count} 张图片添加alt属性')
                self.execution_results['success_count'] += 1
            else:
                logger.info(f"[模拟] 将为 {fixed_count} 张图片添加alt属性: {file_path}")
                self._record_operation(suggestion, 'success', f'[模拟] 将为 {fixed_count} 张图片添加alt属性')
                self.execution_results['success_count'] += 1
        else:
            logger.info(f"没有需要添加alt属性的图片: {file_path}")
            self._record_operation(suggestion, 'skipped', '没有需要添加alt属性的图片')
            self.execution_results['skipped_count'] += 1
    
    def _fix_title_too_long(self, file_path: str, suggestion: Dict[str, Any], dry_run: bool):
        """修复标题过长的问题"""
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # 解析HTML
        soup = BeautifulSoup(content, 'lxml')
        
        # 查找标题
        if soup.title and soup.title.string:
            original_title = soup.title.string.strip()
            if len(original_title) <= 70:
                logger.info(f"标题长度已合适: {file_path}")
                self._record_operation(suggestion, 'skipped', '标题长度已合适')
                self.execution_results['skipped_count'] += 1
                return
            
            # 优化标题，截断到70字符
            optimized_title = self._truncate_title(original_title, 70)
            soup.title.string = optimized_title
            
            # 保存修改
            if not dry_run:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(str(soup))
                logger.info(f"已优化标题长度: {file_path}")
                self._record_operation(suggestion, 'success', 
                                     f'已将标题从 {len(original_title)} 字符优化到 {len(optimized_title)} 字符')
                self.execution_results['success_count'] += 1
            else:
                logger.info(f"[模拟] 将优化标题长度: {file_path}")
                self._record_operation(suggestion, 'success', 
                                     f'[模拟] 将将标题从 {len(original_title)} 字符优化到 {len(optimized_title)} 字符')
                self.execution_results['success_count'] += 1
        else:
            logger.warning(f"找不到标题标签: {file_path}")
            self._record_operation(suggestion, 'failed', '找不到标题标签')
            self.execution_results['failed_count'] += 1
    
    def _fix_meta_description_too_long(self, file_path: str, suggestion: Dict[str, Any], dry_run: bool):
        """修复元描述过长的问题"""
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # 解析HTML
        soup = BeautifulSoup(content, 'lxml')
        
        # 查找meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if not meta_desc or not meta_desc.get('content'):
            logger.warning(f"找不到meta description: {file_path}")
            self._record_operation(suggestion, 'failed', '找不到meta description')
            self.execution_results['failed_count'] += 1
            return
        
        original_desc = meta_desc['content'].strip()
        if len(original_desc) <= 160:
            logger.info(f"meta description长度已合适: {file_path}")
            self._record_operation(suggestion, 'skipped', 'meta description长度已合适')
            self.execution_results['skipped_count'] += 1
            return
        
        # 优化meta description，截断到160字符
        optimized_desc = self._truncate_text(original_desc, 160)
        meta_desc['content'] = optimized_desc
        
        # 保存修改
        if not dry_run:
            with open(file_path, 'w', encoding='utf-8') as f:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(str(soup))
            logger.info(f"已优化meta description长度: {file_path}")
            self._record_operation(suggestion, 'success', 
                                 f'已将meta description从 {len(original_desc)} 字符优化到 {len(optimized_desc)} 字符')
            self.execution_results['success_count'] += 1
        else:
            logger.info(f"[模拟] 将优化meta description长度: {file_path}")
            self._record_operation(suggestion, 'success', 
                                 f'[模拟] 将将meta description从 {len(original_desc)} 字符优化到 {len(optimized_desc)} 字符')
            self.execution_results['success_count'] += 1
    
    def _create_backup(self):
        """创建网站文件备份"""
        logger.info("创建网站文件备份...")
        
        # 确保备份目录存在
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # 获取当前时间作为备份标识
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(self.backup_dir, f'backup_{timestamp}')
        
        try:
            # 如果是目录，备份整个目录
            if os.path.isdir(self.site_path):
                shutil.copytree(self.site_path, backup_path, 
                              ignore=lambda src, names: ['.seo_backup', '__pycache__', '.git'])
            # 如果是文件，备份单个文件
            elif os.path.isfile(self.site_path):
                os.makedirs(backup_path, exist_ok=True)
                shutil.copy2(self.site_path, os.path.join(backup_path, os.path.basename(self.site_path)))
            
            logger.info(f"备份已创建: {backup_path}")
            
            # 清理旧备份（保留最近5个）
            self._cleanup_old_backups()
            
        except Exception as e:
            logger.error(f"创建备份失败: {str(e)}")
            raise
    
    def _restore_backup(self, backup_path: str = None):
        """恢复备份"""
        logger.info("恢复网站文件备份...")
        
        # 如果没有指定备份路径，使用最新的备份
        if not backup_path:
            backup_files = sorted([f for f in os.listdir(self.backup_dir) 
                                 if os.path.isdir(os.path.join(self.backup_dir, f)) 
                                 and f.startswith('backup_')], reverse=True)
            
            if not backup_files:
                raise ValueError("没有可用的备份文件")
            
            backup_path = os.path.join(self.backup_dir, backup_files[0])
        
        try:
            # 清空当前站点目录
            if os.path.exists(self.site_path):
                if os.path.isdir(self.site_path):
                    shutil.rmtree(self.site_path)
                else:
                    os.remove(self.site_path)
            
            # 恢复备份
            if os.path.isdir(backup_path):
                # 获取备份中的内容
                backup_contents = os.listdir(backup_path)
                if len(backup_contents) == 1 and os.path.isfile(os.path.join(backup_path, backup_contents[0])):
                    # 如果备份中只有一个文件，直接复制
                    shutil.copy2(os.path.join(backup_path, backup_contents[0]), self.site_path)
                else:
                    # 否则复制整个目录
                    shutil.copytree(backup_path, self.site_path)
            
            logger.info(f"已从备份恢复: {backup_path}")
            
        except Exception as e:
            logger.error(f"恢复备份失败: {str(e)}")
            raise
    
    def _cleanup_old_backups(self, keep_count: int = 5):
        """清理旧备份"""
        try:
            # 获取所有备份目录
            backup_dirs = sorted([f for f in os.listdir(self.backup_dir) 
                                if os.path.isdir(os.path.join(self.backup_dir, f)) 
                                and f.startswith('backup_')], reverse=True)
            
            # 删除超过保留数量的备份
            for old_backup in backup_dirs[keep_count:]:
                old_backup_path = os.path.join(self.backup_dir, old_backup)
                shutil.rmtree(old_backup_path)
                logger.info(f"已删除旧备份: {old_backup_path}")
                
        except Exception as e:
            logger.warning(f"清理旧备份时出错: {str(e)}")
    
    def _get_local_file_path(self, page_url: str) -> Optional[str]:
        """根据页面URL获取本地文件路径"""
        if not page_url:
            return self.site_path
        
        # 如果是file:// URL，转换为本地路径
        if page_url.startswith('file://'):
            # 移除file://前缀
            path = page_url[7:]
            # 处理Windows路径格式
            if path.startswith('/') and len(path) > 1 and path[1] == ':':
                path = path[1:]
            return path
        
        # 如果是相对路径，相对于site_path
        if not page_url.startswith(('http://', 'https://')):
            return os.path.join(self.site_path, page_url)
        
        # 对于HTTP URL，尝试提取路径部分并与site_path组合
        # 这是一个简单的实现，实际使用中可能需要更复杂的URL解析
        import urllib.parse
        parsed_url = urllib.parse.urlparse(page_url)
        path = parsed_url.path
        if not path or path == '/':
            path = 'index.html'
        return os.path.join(self.site_path, path.lstrip('/'))
    
    def _generate_meta_description(self, title: str, content: str) -> str:
        """生成meta description"""
        # 简单实现：使用标题和内容的前150个字符
        # 移除HTML标签
        soup = BeautifulSoup(content, 'lxml')
        text = soup.get_text(separator=' ', strip=True)
        
        # 生成描述
        if len(text) > 100:
            description = f"{title} - {text[:120]}..."
        else:
            description = f"{title} - {text}"
        
        # 确保不超过160字符
        return self._truncate_text(description, 160)
    
    def _generate_image_alt(self, img) -> str:
        """生成图片alt文本"""
        # 从文件名生成alt文本
        src = img.get('src', '')
        filename = os.path.basename(src)
        # 移除扩展名
        alt_text = os.path.splitext(filename)[0]
        # 替换下划线和连字符为空格
        alt_text = alt_text.replace('_', ' ').replace('-', ' ')
        # 首字母大写
        alt_text = alt_text.title()
        
        # 如果生成的alt文本为空，使用默认值
        if not alt_text.strip():
            alt_text = "装饰图片"
        
        return alt_text
    
    def _truncate_title(self, title: str, max_length: int) -> str:
        """截断标题，确保在指定长度内"""
        if len(title) <= max_length:
            return title
        
        # 在单词边界处截断
        truncated = title[:max_length-3]
        last_space = truncated.rfind(' ')
        if last_space > max_length * 0.7:  # 确保截断后至少保留70%的长度
            truncated = truncated[:last_space]
        
        return truncated + '...'
    
    def _truncate_text(self, text: str, max_length: int) -> str:
        """截断文本，确保在指定长度内"""
        if len(text) <= max_length:
            return text
        
        # 在单词边界处截断
        truncated = text[:max_length-3]
        last_space = truncated.rfind(' ')
        if last_space > max_length * 0.7:  # 确保截断后至少保留70%的长度
            truncated = truncated[:last_space]
        
        return truncated + '...'
    
    def _record_operation(self, suggestion: Dict[str, Any], status: str, message: str):
        """记录操作结果"""
        operation = {
            'suggestion_id': suggestion.get('id'),
            'page': suggestion.get('page'),
            'category': suggestion.get('category'),
            'issue': suggestion.get('issue'),
            'status': status,
            'message': message
        }
        self.execution_results['operations'].append(operation)
    
    def get_execution_summary(self) -> str:
        """获取执行摘要"""
        summary = f"SEO优化执行摘要:\n"
        summary += f"- 成功: {self.execution_results['success_count']}\n"
        summary += f"- 失败: {self.execution_results['failed_count']}\n"
        summary += f"- 跳过: {self.execution_results['skipped_count']}\n"
        summary += f"- 总操作数: {len(self.execution_results['operations'])}\n\n"
        
        # 添加详细信息
        if self.execution_results['operations']:
            summary += "详细操作记录:\n"
            for op in self.execution_results['operations']:
                summary += f"  - [{op['status'].upper()}] {op['page'] or '全局'}: {op['issue']} - {op['message']}\n"
        
        return summary