"""网站 JS 文件扫描模块"""

import re
from typing import List, Set
from urllib.parse import urljoin, urlparse
from src.core.downloader import JSDownloader
from src.utils.logger import setup_logger

logger = setup_logger("Scanner")


class JSScanner:
    """网站 JS 文件扫描器"""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.downloader = JSDownloader(self.config.get('network', {}))
        
        self.js_patterns = [
            re.compile(r'<script[^>]+src=["\']([^"\']+\.js[^"\']*)["\']', re.IGNORECASE),
            re.compile(r'<script[^>]+src=["\']([^"\']+)["\'][^>]*type=["\'](?:text|application)/javascript["\']', re.IGNORECASE),
            re.compile(r'import\s*\(\s*["\']([^"\']+\.js[^"\']*)["\']\s*\)', re.IGNORECASE),
            re.compile(r'require\s*\(\s*["\']([^"\']+\.js[^"\']*)["\']\s*\)', re.IGNORECASE),
        ]
    
    def scan_html_for_js(self, html_content: str, base_url: str) -> Set[str]:
        """从 HTML 内容中扫描 JS 文件 URL"""
        js_urls = set()
        
        for pattern in self.js_patterns:
            matches = pattern.findall(html_content)
            for match in matches:
                if match.startswith(('http://', 'https://')):
                    js_urls.add(match)
                elif match.startswith('/'):
                    js_urls.add(urljoin(base_url, match))
                elif base_url:
                    js_urls.add(urljoin(base_url, match))
        
        logger.debug(f"从 HTML 中扫描到 {len(js_urls)} 个 JS 文件")
        return js_urls
    
    def scan_website(self, url: str) -> Set[str]:
        """扫描网站获取所有 JS 文件"""
        js_urls = set()
        
        try:
            # 下载首页
            html_content = self.downloader.download(url)
            if not html_content:
                logger.error(f"无法下载页面：{url}")
                return js_urls
            
            # 解析基础 URL
            parsed = urlparse(url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            
            # 扫描 JS 文件
            js_urls = self.scan_html_for_js(html_content, base_url)
            
            logger.info(f"从 {url} 扫描到 {len(js_urls)} 个 JS 文件")
            
        except Exception as e:
            logger.error(f"扫描网站失败：{e}")
        
        return js_urls