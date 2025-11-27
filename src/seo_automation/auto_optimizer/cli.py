"""SEO自优化程序的命令行界面"""

import os
import sys
import argparse
import logging
import json
import datetime
from typing import Dict, List, Optional, Any

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.seo_automation.auto_optimizer.config_manager import ConfigManager
from src.seo_automation.auto_optimizer.profile_manager import ProfileManager
from src.seo_automation.auto_optimizer.optimizer import SEOAutoOptimizer
from src.seo_automation.auto_optimizer.backup_manager import BackupManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'logs', 'seo_auto_optimizer.log')),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class CLI:
    """SEO自优化程序的命令行界面"""
    
    def __init__(self):
        """初始化CLI"""
        self.config_manager = ConfigManager()
        self.profile_manager = ProfileManager(self.config_manager)
        self.optimizer = None
        
        # 确保日志目录存在
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'logs')
        os.makedirs(log_dir, exist_ok=True)
    
    def parse_args(self):
        """
        解析命令行参数
        
        Returns:
            argparse.Namespace: 解析后的参数
        """
        parser = argparse.ArgumentParser(
            prog='seo_auto_optimizer',
            description='SEO自优化程序 - 自动分析和优化网站SEO，提升搜索引擎排名',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
示例:
  # 创建新配置文件
  seo_auto_optimizer profile create --name "my_website" --site-path "/path/to/website" --description "我的网站SEO配置"
  
  # 列出所有配置文件
  seo_auto_optimizer profile list
  
  # 使用配置文件进行SEO分析
  seo_auto_optimizer analyze --profile "my_website"
  
  # 生成优化建议
  seo_auto_optimizer recommend --profile "my_website"
  
  # 执行优化
  seo_auto_optimizer optimize --profile "my_website" --dry-run
  
  # 列出备份
  seo_auto_optimizer backup list
  
  # 恢复备份
  seo_auto_optimizer backup restore --name "backup_20230501_120000"
            """
        )
        
        # 创建子命令解析器
        subparsers = parser.add_subparsers(dest='command', help='命令')
        
        # profile 命令 - 配置文件管理
        profile_parser = subparsers.add_parser('profile', help='管理配置文件')
        profile_subparsers = profile_parser.add_subparsers(dest='profile_command', help='配置文件操作')
        
        # profile create - 创建新配置文件
        profile_create = profile_subparsers.add_parser('create', help='创建新配置文件')
        profile_create.add_argument('--name', required=True, help='配置文件名称')
        profile_create.add_argument('--site-path', required=True, help='网站根目录路径')
        profile_create.add_argument('--description', default='', help='配置文件描述')
        
        # profile list - 列出所有配置文件
        profile_list = profile_subparsers.add_parser('list', help='列出所有配置文件')
        
        # profile load - 加载配置文件
        profile_load = profile_subparsers.add_parser('load', help='加载配置文件')
        profile_load.add_argument('--name', required=True, help='配置文件名称')
        
        # profile delete - 删除配置文件
        profile_delete = profile_subparsers.add_parser('delete', help='删除配置文件')
        profile_delete.add_argument('--name', required=True, help='配置文件名称')
        
        # profile export - 导出配置文件
        profile_export = profile_subparsers.add_parser('export', help='导出配置文件')
        profile_export.add_argument('--name', required=True, help='配置文件名称')
        profile_export.add_argument('--output', required=True, help='导出路径')
        
        # profile import - 导入配置文件
        profile_import = profile_subparsers.add_parser('import', help='导入配置文件')
        profile_import.add_argument('--file', required=True, help='导入文件路径')
        profile_import.add_argument('--name', help='新的配置文件名称')
        
        # profile update-path - 更新网站路径
        profile_update_path = profile_subparsers.add_parser('update-path', help='更新配置文件中的网站路径')
        profile_update_path.add_argument('--name', required=True, help='配置文件名称')
        profile_update_path.add_argument('--new-path', required=True, help='新的网站路径')
        
        # analyze 命令 - SEO分析
        analyze_parser = subparsers.add_parser('analyze', help='执行SEO分析')
        analyze_parser.add_argument('--profile', required=True, help='配置文件名称')
        analyze_parser.add_argument('--output', help='分析结果输出路径')
        analyze_parser.add_argument('--verbose', action='store_true', help='显示详细分析结果')
        
        # recommend 命令 - 生成优化建议
        recommend_parser = subparsers.add_parser('recommend', help='生成优化建议')
        recommend_parser.add_argument('--profile', required=True, help='配置文件名称')
        recommend_parser.add_argument('--output', help='优化建议输出路径')
        recommend_parser.add_argument('--level', choices=['basic', 'moderate', 'advanced'], help='优化级别')
        
        # optimize 命令 - 执行优化
        optimize_parser = subparsers.add_parser('optimize', help='执行SEO优化')
        optimize_parser.add_argument('--profile', required=True, help='配置文件名称')
        optimize_parser.add_argument('--dry-run', action='store_true', help='只显示将要进行的更改，不实际修改文件')
        optimize_parser.add_argument('--backup', action='store_true', help='优化前创建备份（默认开启）')
        optimize_parser.add_argument('--no-backup', action='store_true', help='优化前不创建备份')
        optimize_parser.add_argument('--output', help='优化报告输出路径')
        
        # backup 命令 - 备份管理
        backup_parser = subparsers.add_parser('backup', help='管理备份')
        backup_subparsers = backup_parser.add_subparsers(dest='backup_command', help='备份操作')
        
        # backup list - 列出所有备份
        backup_list = backup_subparsers.add_parser('list', help='列出所有备份')
        
        # backup create - 创建新备份
        backup_create = backup_subparsers.add_parser('create', help='创建新备份')
        backup_create.add_argument('--profile', required=True, help='配置文件名称')
        backup_create.add_argument('--name', help='备份名称')
        
        # backup restore - 恢复备份
        backup_restore = backup_subparsers.add_parser('restore', help='恢复备份')
        backup_restore.add_argument('--name', required=True, help='备份名称')
        backup_restore.add_argument('--confirm', action='store_true', help='确认恢复备份（需要此参数以防止误操作）')
        
        # backup delete - 删除备份
        backup_delete = backup_subparsers.add_parser('delete', help='删除备份')
        backup_delete.add_argument('--name', required=True, help='备份名称')
        backup_delete.add_argument('--confirm', action='store_true', help='确认删除备份（需要此参数以防止误操作）')
        
        # config 命令 - 配置管理
        config_parser = subparsers.add_parser('config', help='管理程序配置')
        config_parser.add_argument('--show', action='store_true', help='显示当前配置')
        
        # 版本命令
        version_parser = subparsers.add_parser('version', help='显示程序版本')
        
        return parser.parse_args()
    
    def run(self, args):
        """
        运行命令
        
        Args:
            args: 命令行参数
        """
        try:
            if args.command == 'profile':
                self.handle_profile_command(args)
            elif args.command == 'analyze':
                self.handle_analyze_command(args)
            elif args.command == 'recommend':
                self.handle_recommend_command(args)
            elif args.command == 'optimize':
                self.handle_optimize_command(args)
            elif args.command == 'backup':
                self.handle_backup_command(args)
            elif args.command == 'config':
                self.handle_config_command(args)
            elif args.command == 'version':
                self.show_version()
            else:
                logger.error("请指定有效的命令。使用 --help 查看可用命令。")
                return 1
            
            return 0
        
        except KeyboardInterrupt:
            logger.info("操作已取消。")
            return 0
        except Exception as e:
            logger.error(f"执行命令时出错: {str(e)}")
            return 1
    
    def handle_profile_command(self, args):
        """
        处理配置文件命令
        
        Args:
            args: 命令行参数
        """
        if args.profile_command == 'create':
            result = self.profile_manager.create_profile(
                args.name,
                args.site_path,
                args.description
            )
            
            if result['status'] == 'success':
                logger.info(f"配置文件 '{result['profile_name']}' 已成功创建。")
                logger.info(f"配置文件路径: {result['profile_path']}")
            else:
                logger.error(f"创建配置文件失败: {result['error']}")
                
        elif args.profile_command == 'list':
            profiles = self.profile_manager.list_profiles()
            
            if not profiles:
                logger.info("没有找到配置文件。")
                return
            
            logger.info("\n可用配置文件列表:\n")
            logger.info("{:<20} {:<30} {:<15} {:<20} {:<20}".format(
                "名称", "网站路径", "优化级别", "创建时间", "更新时间"
            ))
            logger.info("-" * 120)
            
            for profile in profiles:
                logger.info("{:<20} {:<30} {:<15} {:<20} {:<20}".format(
                    profile['profile_name'][:18] + '..' if len(profile['profile_name']) > 20 else profile['profile_name'],
                    profile['site_path'][:28] + '..' if len(profile['site_path']) > 30 else profile['site_path'],
                    profile['optimization_level'],
                    profile['created_at'][:16],
                    profile['updated_at'][:16]
                ))
                
                if profile['description']:
                    logger.info(f"  描述: {profile['description']}\n")
                else:
                    logger.info("")
                    
        elif args.profile_command == 'load':
            result = self.profile_manager.load_profile(args.name)
            
            if result['status'] == 'success':
                logger.info(f"配置文件 '{args.name}' 已成功加载。")
                logger.info(f"网站路径: {result['profile_content']['site_path']}")
                logger.info(f"优化级别: {result['profile_content'].get('optimization_config', {}).get('optimization_level', 'moderate')}")
            else:
                logger.error(f"加载配置文件失败: {result['error']}")
                
        elif args.profile_command == 'delete':
            # 询问用户确认
            confirm = input(f"确定要删除配置文件 '{args.name}' 吗？(y/n): ")
            if confirm.lower() != 'y':
                logger.info("删除已取消。")
                return
            
            result = self.profile_manager.delete_profile(args.name)
            
            if result['status'] == 'success':
                logger.info(f"配置文件 '{args.name}' 已成功删除。")
            else:
                logger.error(f"删除配置文件失败: {result['error']}")
                
        elif args.profile_command == 'export':
            result = self.profile_manager.export_profile(args.name, args.output)
            
            if result['status'] == 'success':
                logger.info(f"配置文件 '{args.name}' 已成功导出到 '{result['export_path']}'。")
            else:
                logger.error(f"导出配置文件失败: {result['error']}")
                
        elif args.profile_command == 'import':
            result = self.profile_manager.import_profile(args.file, args.name)
            
            if result['status'] == 'success':
                logger.info(f"配置文件已成功导入为 '{result['profile_name']}'。")
                logger.info(f"配置文件路径: {result['profile_path']}")
            else:
                logger.error(f"导入配置文件失败: {result['error']}")
                
        elif args.profile_command == 'update-path':
            result = self.profile_manager.update_profile_site_path(args.name, args.new_path)
            
            if result['status'] == 'success':
                logger.info(f"配置文件 '{args.name}' 的网站路径已成功更新为 '{result['new_site_path']}'。")
            else:
                logger.error(f"更新网站路径失败: {result['error']}")
                
        else:
            logger.error("请指定有效的配置文件操作。使用 --help 查看可用操作。")
    
    def handle_analyze_command(self, args):
        """
        处理SEO分析命令
        
        Args:
            args: 命令行参数
        """
        # 加载配置文件
        load_result = self.profile_manager.load_profile(args.profile)
        if load_result['status'] != 'success':
            logger.error(f"加载配置文件失败: {load_result['error']}")
            return
        
        # 初始化优化器，将配置文件内容传递给构造函数
        self.optimizer = SEOAutoOptimizer(self.config_manager, load_result['profile_content'])
        
        # 执行分析
        logger.info(f"开始分析网站: {load_result['profile_content']['site_path']}")
        logger.info("这可能需要一些时间，请耐心等待...")
        
        success = self.optimizer._perform_analysis()
        analysis_results = self.optimizer.get_analysis_results()
        
        # 显示分析结果
        self._display_analysis_results(analysis_results, args.verbose)
        
        # 保存分析结果
        if args.output:
            self._save_analysis_results(analysis_results, args.output)
            logger.info(f"分析结果已保存到 '{args.output}'。")
    
    def handle_recommend_command(self, args):
        """
        处理优化建议命令
        
        Args:
            args: 命令行参数
        """
        # 加载配置文件
        load_result = self.profile_manager.load_profile(args.profile)
        if load_result['status'] != 'success':
            logger.error(f"加载配置文件失败: {load_result['error']}")
            return
        
        # 如果指定了优化级别，更新配置
        if args.level:
            # 获取当前优化配置
            current_config = self.config_manager.get_config('optimization_config') or {}
            current_config['optimization_level'] = args.level
            self.config_manager.set_config('optimization_config', current_config)
        
        # 初始化优化器，将配置文件内容传递给构造函数
        self.optimizer = SEOAutoOptimizer(self.config_manager, load_result['profile_content'])
        
        # 执行分析和建议生成
        logger.info(f"开始生成优化建议: {load_result['profile_content']['site_path']}")
        logger.info("正在执行网站分析...")
        
        success = self.optimizer._perform_analysis()
        recommendations = self.optimizer.get_suggestions()
        
        # 显示优化建议
        self._display_recommendations(recommendations)
        
        # 保存优化建议
        if args.output:
            self._save_recommendations(recommendations, args.output)
            logger.info(f"优化建议已保存到 '{args.output}'。")
    
    def handle_optimize_command(self, args):
        """
        处理优化命令
        
        Args:
            args: 命令行参数
            
        Returns:
            int: 退出码，成功返回0，失败返回1
        """
        try:
            # 特殊处理：如果提供的是网站目录（包含HTML文件），则创建临时配置
            if os.path.isdir(args.profile) and any(file.endswith(('.html', '.htm')) for file in os.listdir(args.profile)):
                logger.info(f"检测到网站目录: {args.profile}，将其作为网站根目录进行优化")
                
                # 创建临时配置
                temp_profile = {
                    'profile_name': 'temp_website_profile',
                    'site_path': args.profile,
                    'created_at': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'analysis_config': {
                        'analyze_content': True,
                        'analyze_keywords': True,
                        'analyze_performance': True
                    },
                    'optimization_config': {
                        'enable_auto_optimize': True,
                        'auto_optimize_level': 'medium'
                    }
                }
                
                # 更新配置管理器
                self.config_manager.set_config('site_path', args.profile)
                self.config_manager.set_config('analysis_config', temp_profile['analysis_config'])
                self.config_manager.set_config('optimization_config', temp_profile['optimization_config'])
                
                # 初始化SEO自优化器
                self.optimizer = SEOAutoOptimizer(self.config_manager, temp_profile)
                
                # 确定是否创建备份
                backup_config = self.config_manager.get_config('backup_config') or {}
                backup_enabled = not args.no_backup and (args.backup or backup_config.get('enabled', True))
                
                logger.info("跳过确认提示以进行测试")
                
                # 执行优化
                logger.info(f"{'执行模拟优化（不修改文件）' if args.dry_run else '开始优化网站'}: {args.profile}")
                
                optimization_result = self.optimizer.optimize(
                    backup_before=backup_enabled,
                    dry_run=args.dry_run
                )
            else:
                # 正常加载配置文件
                load_result = self.profile_manager.load_profile(args.profile)
                if load_result['status'] != 'success':
                    logger.error(f"加载配置文件失败: {load_result['error']}")
                    return 1
                
                # 确定是否创建备份
                # 获取备份配置
                backup_config = self.config_manager.get_config('backup_config') or {}
                backup_enabled = not args.no_backup and (args.backup or backup_config.get('enabled', True))
                
                # 如果不是dry-run且需要备份，询问确认
                # 临时跳过确认提示以方便测试
                logger.info("跳过确认提示以进行测试")
                # if not args.dry_run and backup_enabled:
                #     confirm = input("将要对网站文件进行修改。修改前将创建备份。确定继续吗？(y/n): ")
                #     if confirm.lower() != 'y':
                #         logger.info("优化已取消。")
                #         return 0
                # elif not args.dry_run:
                #     confirm = input("将要对网站文件进行修改。注意：您已禁用备份功能，这可能导致数据丢失。确定继续吗？(y/n): ")
                #     if confirm.lower() != 'y':
                #         logger.info("优化已取消。")
                #         return 0
                
                # 初始化优化器，将配置文件内容传递给构造函数
                self.optimizer = SEOAutoOptimizer(self.config_manager, load_result['profile_content'])
                
                # 执行优化
                logger.info(f"{'执行模拟优化（不修改文件）' if args.dry_run else '开始优化网站'}: {load_result['profile_content']['site_path']}")
                
                optimization_result = self.optimizer.optimize(
                    backup_before=backup_enabled,
                    dry_run=args.dry_run
                )
            
            # 显示优化结果
            self._display_optimization_result(optimization_result)
            
            # 保存优化报告
            if args.output:
                self._save_optimization_report(optimization_result, args.output)
                logger.info(f"优化报告已保存到 '{args.output}'。")
            
            # 根据优化结果返回退出码
            if optimization_result.get('status') == 'success':
                return 0
            else:
                logger.error(f"优化过程失败: {optimization_result.get('error', '未知错误')}")
                return 1
                
        except Exception as e:
            logger.error(f"执行优化命令时出错: {str(e)}")
            return 1
    
    def handle_backup_command(self, args):
        """
        处理备份命令
        
        Args:
            args: 命令行参数
        """
        # 获取备份目录
        # 获取备份目录配置
        backup_config = self.config_manager.get_config('backup_config') or {}
        backup_dir = backup_config.get('backup_directory')
        if not backup_dir:
            # 默认备份目录
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            backup_dir = os.path.join(base_dir, 'backups')
        
        # 初始化备份管理器
        backup_manager = BackupManager(self.config_manager)
        
        if args.backup_command == 'list':
            backups = backup_manager.list_backups()
            
            if not backups:
                logger.info("没有找到备份。")
                return
            
            logger.info("\n可用备份列表:\n")
            logger.info("{:<30} {:<20} {:<15} {:<10}".format(
                "名称", "创建时间", "大小", "包含文件"
            ))
            logger.info("-" * 85)
            
            for backup in backups:
                logger.info("{:<30} {:<20} {:<15} {:<10}".format(
                    backup['name'],
                    backup['created_at'][:16],
                    backup['size'],
                    str(backup['file_count'])
                ))
                
        elif args.backup_command == 'create':
            # 加载配置文件以获取网站路径
            load_result = self.profile_manager.load_profile(args.profile)
            if load_result['status'] != 'success':
                logger.error(f"加载配置文件失败: {load_result['error']}")
                return
            
            site_path = load_result['profile_content']['site_path']
            
            # 创建备份
            backup_name = args.name or f"backup_{args.profile}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            logger.info(f"开始创建备份: {backup_name}")
            logger.info(f"网站路径: {site_path}")
            
            result = backup_manager.create_backup(
                source_path=site_path,
                backup_name=backup_name
            )
            
            if result['status'] == 'success':
                logger.info(f"备份 '{result['backup_name']}' 已成功创建。")
                logger.info(f"备份路径: {result['backup_path']}")
                logger.info(f"包含文件数: {result['file_count']}")
            else:
                logger.error(f"创建备份失败: {result['error']}")
                
        elif args.backup_command == 'restore':
            if not args.confirm:
                logger.error("恢复操作需要确认。请使用 --confirm 参数确认恢复。")
                return
            
            # 再次确认
            confirm = input(f"确定要恢复备份 '{args.name}' 吗？这将覆盖当前的网站文件。(yes/no): ")
            if confirm.lower() != 'yes':
                logger.info("恢复已取消。")
                return
            
            # 查找使用该备份的配置文件
            profiles = self.profile_manager.list_profiles()
            restore_path = None
            
            for profile in profiles:
                if profile['profile_name'] in args.name:
                    restore_path = profile['site_path']
                    break
            
            # 如果找不到，询问用户
            if not restore_path:
                restore_path = input("请输入要恢复到的网站路径: ")
                if not os.path.exists(restore_path):
                    logger.error(f"恢复路径不存在: {restore_path}")
                    return
            
            logger.info(f"开始恢复备份: {args.name}")
            logger.info(f"恢复目标: {restore_path}")
            
            result = backup_manager.restore_from_backup(
                backup_name=args.name,
                restore_path=restore_path
            )
            
            if result['status'] == 'success':
                logger.info(f"备份 '{args.name}' 已成功恢复到 '{restore_path}'。")
                logger.info(f"恢复文件数: {result['file_count']}")
            else:
                logger.error(f"恢复备份失败: {result['error']}")
                
        elif args.backup_command == 'delete':
            if not args.confirm:
                logger.error("删除操作需要确认。请使用 --confirm 参数确认删除。")
                return
            
            logger.info(f"开始删除备份: {args.name}")
            
            result = backup_manager.delete_backup(args.name)
            
            if result['status'] == 'success':
                logger.info(f"备份 '{args.name}' 已成功删除。")
            else:
                logger.error(f"删除备份失败: {result['error']}")
                
        else:
            logger.error("请指定有效的备份操作。使用 --help 查看可用操作。")
    
    def handle_config_command(self, args):
        """
        处理配置命令
        
        Args:
            args: 命令行参数
        """
        if args.show:
            config = self.config_manager.get_all_config()
            
            logger.info("\n当前配置:\n")
            
            # 格式化输出配置
            formatted_config = json.dumps(config, ensure_ascii=False, indent=2)
            logger.info(formatted_config)
    
    def show_version(self):
        """
        显示程序版本
        """
        logger.info("\nSEO自优化程序 v1.0.0")
        logger.info("一个用于自动分析和优化网站SEO的工具")
        logger.info("https://github.com/seo-optimizer\n")
    
    def _display_analysis_results(self, results: Dict[str, Any], verbose: bool = False):
        """
        显示分析结果
        
        Args:
            results: 分析结果
            verbose: 是否显示详细结果
        """
        logger.info("\n===== SEO分析结果 =====\n")
        
        # 总体评分
        if 'overall_score' in results:
            logger.info(f"总体SEO评分: {results['overall_score']}/100")
            logger.info(f"网站健康状态: {self._get_health_status(results['overall_score'])}\n")
        
        # 页面统计
        if 'page_stats' in results:
            logger.info(f"分析页面数: {results['page_stats'].get('total_pages', 0)}")
            logger.info(f"发现错误: {results['page_stats'].get('error_pages', 0)}")
            logger.info(f"平均页面大小: {results['page_stats'].get('avg_page_size', 'N/A')}")
            logger.info(f"平均加载时间: {results['page_stats'].get('avg_load_time', 'N/A')}\n")
        
        # 各维度评分
        if 'category_scores' in results:
            logger.info("各维度评分:")
            for category, score in results['category_scores'].items():
                logger.info(f"  - {self._format_category_name(category)}: {score}/100")
            logger.info()
        
        # 问题统计
        if 'issues' in results and results['issues']:
            logger.info("发现的问题:")
            
            # 按严重程度分组
            severity_groups = {
                'critical': [],
                'high': [],
                'medium': [],
                'low': []
            }
            
            for issue in results['issues']:
                severity = issue.get('severity', 'medium')
                severity_groups[severity].append(issue)
            
            # 显示不同严重程度的问题
            for severity in ['critical', 'high', 'medium', 'low']:
                issues = severity_groups[severity]
                if issues:
                    logger.info(f"  {severity.upper()} ({len(issues)}):")
                    
                    # 最多显示前5个问题
                    for i, issue in enumerate(issues[:5]):
                        logger.info(f"    {i+1}. {issue.get('description', '未知问题')}")
                        if 'affected_pages' in issue and issue['affected_pages']:
                            logger.info(f"       影响页面: {', '.join(issue['affected_pages'][:3])}{'...' if len(issue['affected_pages']) > 3 else ''}")
                    
                    if len(issues) > 5:
                        logger.info(f"    ... 还有 {len(issues) - 5} 个问题")
            
            logger.info()
        
        # 如果是详细模式，显示更多信息
        if verbose:
            if 'pages' in results and results['pages']:
                logger.info("页面详细分析:")
                
                # 显示前3个页面的详细信息
                for page in results['pages'][:3]:
                    logger.info(f"  URL: {page.get('url', 'N/A')}")
                    logger.info(f"  评分: {page.get('score', 'N/A')}/100")
                    
                    if 'issues' in page:
                        logger.info(f"  问题: {len(page['issues'])}")
                        for issue in page['issues'][:5]:
                            logger.info(f"    - {issue.get('description', '未知问题')}")
                    
                    logger.info("")
                
                if len(results['pages']) > 3:
                    logger.info(f"  ... 还有 {len(results['pages']) - 3} 个页面")
    
    def _display_recommendations(self, recommendations: List[Dict[str, Any]]):
        """
        显示优化建议
        
        Args:
            recommendations: 优化建议列表
        """
        logger.info("\n===== SEO优化建议 =====\n")
        
        if not recommendations:
            logger.info("未发现需要优化的问题。您的网站SEO状况良好！\n")
            return
        
        # 按优先级分组
        priority_groups = {
            'high': [],
            'medium': [],
            'low': []
        }
        
        for rec in recommendations:
            priority = rec.get('priority', 'medium')
            priority_groups[priority].append(rec)
        
        # 显示不同优先级的建议
        for priority in ['high', 'medium', 'low']:
            recs = priority_groups[priority]
            if recs:
                logger.info(f"{'!' * 5} {priority.upper()} PRIORITY {'!' * 5} ({len(recs)} 项)\n")
                
                for i, rec in enumerate(recs, 1):
                    logger.info(f"{i}. {rec.get('title', '未命名建议')}")
                    logger.info(f"   描述: {rec.get('description', '')}")
                    
                    if 'affected_pages' in rec and rec['affected_pages']:
                        logger.info(f"   影响页面: {len(rec['affected_pages'])} 个")
                        logger.info(f"   示例: {', '.join(rec['affected_pages'][:3])}{'...' if len(rec['affected_pages']) > 3 else ''}")
                    
                    if 'potential_impact' in rec:
                        logger.info(f"   潜在影响: {rec['potential_impact']}")
                    
                    if 'recommended_action' in rec:
                        logger.info(f"   建议操作: {rec['recommended_action']}")
                    
                    logger.info()
        
        logger.info("总结:")
        logger.info(f"  高优先级: {len(priority_groups['high'])} 项")
        logger.info(f"  中优先级: {len(priority_groups['medium'])} 项")
        logger.info(f"  低优先级: {len(priority_groups['low'])} 项")
        logger.info()
        
        # 提供优化建议
        total_recs = sum(len(recs) for recs in priority_groups.values())
        if total_recs > 0:
            logger.info("下一步建议:")
            if len(priority_groups['high']) > 0:
                logger.info(f"  1. 优先处理 {len(priority_groups['high'])} 个高优先级问题")
            logger.info(f"  2. 使用 'seo_auto_optimizer optimize --profile <配置文件名称> --dry-run' 查看将要进行的更改")
            logger.info(f"  3. 确认无误后，使用 'seo_auto_optimizer optimize --profile <配置文件名称>' 执行优化")
            logger.info()
    
    def _display_optimization_result(self, result: Dict[str, Any]):
        """
        显示优化结果
        
        Args:
            result: 优化结果
        """
        logger.info("")
        logger.info("===== SEO优化结果 =====")
        logger.info("")
        
        if result.get('status') != 'success':
            logger.error(f"优化失败: {result.get('error', '未知错误')}")
            return
        
        logger.info(f"{'模拟优化' if result.get('dry_run', False) else '优化'} {'成功完成' if result.get('status') == 'success' else '失败'}")
        
        # 备份信息
        if 'backup_info' in result and result['backup_info']:
            backup_name = result['backup_info'].get('backup_name')
            backup_path = result['backup_info'].get('backup_path')
            logger.info(f"备份已创建: {backup_name}")
            logger.info(f"备份路径: {backup_path}")
            logger.info("")
        
        # 文件修改统计
        if 'changes' in result:
            changes = result['changes']
            total_files = len(changes)
            total_changes = sum(len(file_changes.get('changes', [])) for file_changes in changes)
            
            logger.info(f"总文件数: {total_files}")
            logger.info(f"总修改数: {total_changes}")
            logger.info("")
            
            # 按修改类型统计
            change_types = {}
            for file_changes in changes:
                for change in file_changes.get('changes', []):
                    change_type = change.get('type', 'unknown')
                    change_types[change_type] = change_types.get(change_type, 0) + 1
            
            logger.info("修改类型统计:")
            if change_types:
                for change_type, count in change_types.items():
                    logger.info(f"  - {self._format_change_type(change_type)}: {count} 次")
            else:
                logger.info("  无修改")
            
            logger.info("")
            
            # 显示前几个文件的修改详情
            logger.info("修改详情:")
            for i, file_changes in enumerate(changes[:10], 1):
                file_path = file_changes.get('file_path')
                file_changes_count = len(file_changes.get('changes', []))
                
                logger.info(f"{i}. {file_path}")
                logger.info(f"   修改: {file_changes_count} 处")
                
                # 显示该文件的修改类型
                file_change_types = {}
                for change in file_changes.get('changes', []):
                    change_type = change.get('type', 'unknown')
                    file_change_types[change_type] = file_change_types.get(change_type, 0) + 1
                
                if file_change_types:
                    logger.info(f"   类型: {', '.join([f'{self._format_change_type(ct)} ({count})' for ct, count in file_change_types.items()])}")
                
                logger.info()
            
            if len(changes) > 10:
                logger.info(f"... 还有 {len(changes) - 10} 个文件\n")
        
        # 优化效果估计
        if 'estimated_impact' in result:
            impact = result['estimated_impact']
            logger.info("优化效果估计:")
            logger.info(f"  预计SEO评分提升: +{impact.get('score_improvement', '0')}")
            logger.info(f"  预计性能提升: {impact.get('performance_improvement', '0')}%")
            logger.info()
        
        # 下一步建议
        logger.info("下一步建议:")
        logger.info("  1. 检查网站以确保优化没有引入任何问题")
        logger.info("  2. 运行 'seo_auto_optimizer analyze --profile <配置文件名称>' 再次分析以查看改进")
        logger.info("  3. 定期重新优化以保持良好的SEO状态")
        if 'backup_info' in result and result['backup_info']:
            logger.info(f"  4. 如需撤销更改，请使用 'seo_auto_optimizer backup restore --name {result['backup_info'].get('backup_name')} --confirm'")
    
    def _save_analysis_results(self, results: Dict[str, Any], output_path: str):
        """
        保存分析结果到文件
        
        Args:
            results: 分析结果
            output_path: 输出文件路径
        """
        # 确保输出目录存在
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # 保存为JSON格式
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
    
    def _save_recommendations(self, recommendations: List[Dict[str, Any]], output_path: str):
        """
        保存优化建议到文件
        
        Args:
            recommendations: 优化建议
            output_path: 输出文件路径
        """
        # 确保输出目录存在
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # 构建建议报告
        report = {
            'generated_at': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'total_recommendations': len(recommendations),
            'recommendations': recommendations
        }
        
        # 保存为JSON格式
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
    
    def _save_optimization_report(self, result: Dict[str, Any], output_path: str):
        """
        保存优化报告到文件
        
        Args:
            result: 优化结果
            output_path: 输出文件路径
        """
        # 确保输出目录存在
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # 构建报告
        report = {
            'generated_at': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'status': result.get('status', 'failed'),
            'dry_run': result.get('dry_run', False),
            'backup_info': result.get('backup_info', {}),
            'total_files_changed': len(result.get('changes', [])),
            'total_changes': sum(len(file_changes.get('changes', [])) for file_changes in result.get('changes', [])),
            'changes': result.get('changes', []),
            'estimated_impact': result.get('estimated_impact', {})
        }
        
        # 保存为JSON格式
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
    
    def _get_health_status(self, score: int) -> str:
        """
        根据分数获取健康状态描述
        
        Args:
            score: SEO评分
            
        Returns:
            str: 健康状态描述
        """
        if score >= 90:
            return "优秀"
        elif score >= 80:
            return "良好"
        elif score >= 70:
            return "一般"
        elif score >= 60:
            return "需要改进"
        else:
            return "较差"
    
    def _format_category_name(self, category: str) -> str:
        """
        格式化类别名称
        
        Args:
            category: 类别名称
            
        Returns:
            str: 格式化后的名称
        """
        # 将下划线替换为空格，并将首字母大写
        return ' '.join(word.capitalize() for word in category.split('_'))
    
    def _format_change_type(self, change_type: str) -> str:
        """
        格式化修改类型名称
        
        Args:
            change_type: 修改类型
            
        Returns:
            str: 格式化后的名称
        """
        # 将下划线替换为空格，并将首字母大写
        return ' '.join(word.capitalize() for word in change_type.split('_'))


def main():
    """主函数"""
    cli = CLI()
    args = cli.parse_args()
    sys.exit(cli.run(args))


if __name__ == '__main__':
    main()