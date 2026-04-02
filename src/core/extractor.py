"""URL 提取核心模块 (适配不拼接逻辑)"""

import time
from pathlib import Path
from typing import Set, List
from tqdm import tqdm
from src.core.downloader import JSDownloader
from src.utils.url_parser import URLParser
from src.utils.file_manager import FileManager
from src.models.url_data import ExtractionResult
from src.utils.logger import setup_logger

logger = setup_logger("Extractor")


class JSURLExtractor:
    """JS URL 提取器"""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.downloader = JSDownloader(self.config.get('network', {}))
        self.parser = URLParser(self.config.get('regex_patterns', {}))
        self.file_manager = FileManager()
        self.file_manager.setup_directories()
    
    def extract_from_urls(self, js_urls: List[str], 
                          output_file: str = None,
                          delay: float = 0.5) -> ExtractionResult:
        """从远程 URL 列表提取"""
        start_time = time.time()
        result = ExtractionResult()
        all_urls: Set[str] = set()
        
        logger.info(f"开始处理 {len(js_urls)} 个 JS 文件...")
        
        for js_url in tqdm(js_urls, desc="处理远程 JS"):
            try:
                # 解析基础 URL (仅用于下载时的 Referer 或日志，不用于拼接结果)
                from urllib.parse import urlparse
                parsed = urlparse(js_url)
                if not parsed.scheme or not parsed.netloc:
                    result.failed_files += 1
                    continue
                
                # 下载内容
                js_content = self.downloader.download(js_url)
                if js_content is None:
                    result.failed_files += 1
                    continue
                
                # 【关键】提取 URL，这里不再传递 base_url 进行拼接，保持原始形态
                # 即使传递了，新的 parser 逻辑也不会自动 join
                extracted = self.parser.extract_urls(js_content, base_url=None) 
                filtered = self.parser.filter_urls(extracted)
                all_urls.update(filtered)
                result.processed_files += 1
                
            except Exception as e:
                logger.error(f"处理 {js_url} 失败：{e}")
                result.failed_files += 1
            
            if delay > 0:
                time.sleep(delay)
        
        # 分类
        result.with_domain, result.without_domain = self.parser.classify_urls(all_urls)
        result.total_urls = len(all_urls)
        result.extraction_time = time.time() - start_time
        
        if output_file:
            self.file_manager.save_urls_to_file(
                list(all_urls), 
                output_file,
                result.with_domain,
                result.without_domain
            )
        
        return result
    
    def extract_from_directory(self, directory: str, 
                               output_file: str = None,
                               recursive: bool = True) -> ExtractionResult:
        """从本地目录提取"""
        start_time = time.time()
        result = ExtractionResult()
        all_urls: Set[str] = set()
        
        js_files = self.file_manager.find_js_files(directory, recursive)
        if not js_files:
            logger.warning(f"未在 {directory} 中找到 JS 文件")
            return result
        
        logger.info(f"开始扫描 {len(js_files)} 个本地 JS 文件...")
        
        for js_file in tqdm(js_files, desc="扫描本地 JS"):
            try:
                with open(js_file, 'r', encoding='utf-8', errors='ignore') as f:
                    js_content = f.read()
                
                # 本地模式肯定没有 base_url，直接提取
                extracted = self.parser.extract_urls(js_content, base_url=None)
                filtered = self.parser.filter_urls(extracted)
                all_urls.update(filtered)
                result.processed_files += 1
                
            except Exception as e:
                logger.error(f"处理 {js_file} 失败：{e}")
                result.failed_files += 1
        
        result.with_domain, result.without_domain = self.parser.classify_urls(all_urls)
        result.total_urls = len(all_urls)
        result.extraction_time = time.time() - start_time
        
        if output_file:
            self.file_manager.save_urls_to_file(
                list(all_urls),
                output_file,
                result.with_domain,
                result.without_domain
            )
        
        return result