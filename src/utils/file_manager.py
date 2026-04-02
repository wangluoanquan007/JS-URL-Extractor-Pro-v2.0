"""文件管理模块"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional
from src.utils.logger import setup_logger

logger = setup_logger("FileManager")


class FileManager:
    """文件管理器"""
    
    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.temp_dir = self.base_dir / "temp"
        self.output_dir = self.base_dir / "output"
        self.input_dir = self.base_dir / "input"
        
    def setup_directories(self):
        """创建必要的目录"""
        for directory in [self.temp_dir, self.output_dir, self.input_dir]:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"目录已准备：{directory}")
    
    def create_temp_dir(self, prefix: str = "js_scan_") -> Path:
        """创建临时目录"""
        temp_path = self.temp_dir / f"{prefix}{os.getpid()}"
        temp_path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"创建临时目录：{temp_path}")
        return temp_path
    
    def cleanup_temp_dir(self, temp_path: Path):
        """清理临时目录"""
        if temp_path and temp_path.exists():
            try:
                shutil.rmtree(temp_path)
                logger.debug(f"清理临时目录：{temp_path}")
            except Exception as e:
                logger.warning(f"清理临时目录失败：{e}")
    
    def read_file_lines(self, filepath: str, skip_comments: bool = True) -> List[str]:
        """读取文件行"""
        path = Path(filepath)
        if not path.exists():
            logger.error(f"文件不存在：{filepath}")
            return []
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                lines = []
                for line in f:
                    line = line.strip()
                    if line:
                        if skip_comments and line.startswith('#'):
                            continue
                        lines.append(line)
                logger.info(f"读取文件 {filepath}，共 {len(lines)} 行")
                return lines
        except Exception as e:
            logger.error(f"读取文件失败：{e}")
            return []
    
    def save_urls_to_file(self, urls: List[str], filepath: str, 
                          with_domain: List[str] = None, 
                          without_domain: List[str] = None):
        """保存 URL 到文件"""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(path, 'w', encoding='utf-8') as f:
                # 如果有分类，先输出有域名的
                if with_domain:
                    f.write("# ===== 含域名的完整 URL =====\n")
                    for url in sorted(with_domain):
                        f.write(url + '\n')
                    f.write("\n")
                
                # 再输出无域名的路径
                if without_domain:
                    f.write("# ===== 不含域名的相对路径 =====\n")
                    for url in sorted(without_domain):
                        f.write(url + '\n')
                else:
                    # 如果没有分类，直接输出所有 URL
                    for url in sorted(set(urls)):
                        f.write(url + '\n')
            
            logger.info(f"成功保存 {len(urls)} 个 URL 到 {filepath}")
        except Exception as e:
            logger.error(f"保存文件失败：{e}")
    
    def find_js_files(self, directory: str, recursive: bool = True) -> List[Path]:
        """查找目录下的所有 JS 文件"""
        dir_path = Path(directory)
        if not dir_path.exists():
            logger.error(f"目录不存在：{directory}")
            return []
        
        js_files = []
        pattern = "**/*.js" if recursive else "*.js"
        
        for js_file in dir_path.glob(pattern):
            if js_file.is_file():
                js_files.append(js_file)
        
        logger.info(f"在 {directory} 中找到 {len(js_files)} 个 JS 文件")
        return js_files