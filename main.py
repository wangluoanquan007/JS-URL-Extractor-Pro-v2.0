#!/usr/bin/env python3
"""
JS URL Extractor Pro - 主程序
功能：
1. 从目标网站下载 JS 文件并提取 URL
2. 扫描本地目录下的 JS 文件提取 URL
3. 分类输出：含域名的完整 URL 和 不含域名的相对路径
"""

import argparse
import sys
import os
import yaml
from pathlib import Path

from src.core.extractor import JSURLExtractor
from src.core.scanner import JSScanner
from src.utils.file_manager import FileManager
from src.utils.logger import setup_logger

logger = setup_logger("Main")


def load_config(config_path: str = "config.yaml") -> dict:
    """加载配置文件"""
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"加载配置文件失败：{e}，使用默认配置")
    return {}


def main():
    parser = argparse.ArgumentParser(
        description='JS URL Extractor Pro - 从 JS 文件中提取 URL',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 从 URL 文件提取
  python main.py --url-file input/file.txt --output output/urls.txt
  
  # 扫描本地目录
  python main.py --dir ./js_files --output output/urls.txt
  
  # 混合模式
  python main.py --url-file input/file.txt --dir ./js_files --output output/urls.txt
  
  # 扫描网站获取 JS 文件
  python main.py --scan-site https://example.com --output output/js_urls.txt
        """
    )
    
    parser.add_argument('--url-file', '-u', type=str, 
                        help='包含 JS 文件 URL 的文本文件路径')
    parser.add_argument('--dir', '-d', type=str,
                        help='本地 JS 文件目录路径')
    parser.add_argument('--scan-site', '-s', type=str,
                        help='扫描网站获取 JS 文件 URL')
    parser.add_argument('--output', '-o', type=str, default='output/urls_extracted.txt',
                        help='输出文件路径 (默认：output/urls_extracted.txt)')
    parser.add_argument('--config', '-c', type=str, default='config.yaml',
                        help='配置文件路径 (默认：config.yaml)')
    parser.add_argument('--no-delay', action='store_true',
                        help='禁用请求延迟')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='显示详细日志')
    
    args = parser.parse_args()
    
    # 加载配置
    config = load_config(args.config)
    
    # 创建提取器
    extractor = JSURLExtractor(config)
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(args.output) or '.', exist_ok=True)
    
    print("=" * 45)
    print("  JS URL Extractor Pro v2.0")
    print("  Version: 2.0 | Year: 2026")
    print("  By | wangluoanquan007    ")
    print("=" * 45)
    print()
    
    result = None
    
    try:
        # 模式 1: 扫描网站
        if args.scan_site:
            logger.info(f"扫描网站：{args.scan_site}")
            scanner = JSScanner(config)
            js_urls = scanner.scan_website(args.scan_site)
            
            if js_urls:
                # 保存 JS 文件 URL
                js_output = args.output.replace('.txt', '_js_files.txt')
                fm = FileManager()
                with open(js_output, 'w', encoding='utf-8') as f:
                    for url in sorted(js_urls):
                        f.write(url + '\n')
                logger.info(f"JS 文件列表已保存到：{js_output}")
                
                # 提取这些 JS 文件中的 URL
                result = extractor.extract_from_urls(
                    list(js_urls), 
                    output_file=args.output,
                    delay=0 if args.no_delay else config.get('concurrency', {}).get('delay_between_requests', 0.5)
                )
            else:
                logger.warning("未找到任何 JS 文件")
        
        # 模式 2: 从 URL 文件提取
        elif args.url_file and not args.dir:
            logger.info(f"从 URL 文件提取：{args.url_file}")
            fm = FileManager()
            js_urls = fm.read_file_lines(args.url_file)
            
            if js_urls:
                result = extractor.extract_from_urls(
                    js_urls,
                    output_file=args.output,
                    delay=0 if args.no_delay else config.get('concurrency', {}).get('delay_between_requests', 0.5)
                )
            else:
                logger.error(f"URL 文件为空或不存在：{args.url_file}")
        
        # 模式 3: 扫描本地目录
        elif args.dir and not args.url_file:
            logger.info(f"扫描本地目录：{args.dir}")
            result = extractor.extract_from_directory(
                args.dir,
                output_file=args.output,
                recursive=True
            )
        
        # 模式 4: 混合模式
        elif args.url_file and args.dir:
            logger.info("混合模式：处理 URL 文件和本地目录")
            result = extractor.extract_from_mixed(
                url_file=args.url_file,
                directory=args.dir,
                output_file=args.output
            )
        
        else:
            parser.print_help()
            sys.exit(1)
        
        # 输出结果
        if result:
            print(result.summary())
            print(f"\n✅ 结果已保存到：{os.path.abspath(args.output)}")
            
    except KeyboardInterrupt:
        print("\n⚠️  用户中断操作")
        sys.exit(1)
    except Exception as e:
        logger.error(f"程序执行出错：{e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()