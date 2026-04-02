"""JS 文件下载模块"""

import requests
import urllib3
from typing import Optional, Dict
from src.utils.logger import setup_logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logger = setup_logger("Downloader")


class JSDownloader:
    """JS 文件下载器"""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.timeout = self.config.get('timeout', 15)
        self.max_retries = self.config.get('max_retries', 3)
        self.verify_ssl = self.config.get('verify_ssl', False)
        self.user_agent = self.config.get('user_agent', 
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """创建请求会话"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })
        return session
    
    def download(self, url: str) -> Optional[str]:
        """下载 JS 文件内容"""
        for attempt in range(self.max_retries):
            try:
                # 设置 Referer
                from urllib.parse import urlparse
                parsed = urlparse(url)
                referer = f"{parsed.scheme}://{parsed.netloc}"
                self.session.headers['Referer'] = referer
                
                response = self.session.get(
                    url, 
                    timeout=self.timeout, 
                    verify=self.verify_ssl
                )
                response.raise_for_status()
                
                # 检查内容类型
                content_type = response.headers.get('Content-Type', '')
                if 'text/html' in content_type and not url.endswith('.js'):
                    logger.warning(f"URL {url} 返回 HTML 内容，可能不是 JS 文件")
                
                logger.debug(f"成功下载：{url} ({len(response.text)} 字节)")
                return response.text
                
            except requests.exceptions.SSLError as e:
                logger.warning(f"SSL 错误 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                if attempt == self.max_retries - 1:
                    logger.error(f"SSL 错误，跳过：{url}")
                    return None
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"请求错误 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                if attempt == self.max_retries - 1:
                    logger.error(f"请求失败，跳过：{url}")
                    return None
        
        return None
    
    def download_batch(self, urls: list, delay: float = 0.5) -> Dict[str, Optional[str]]:
        """批量下载 JS 文件"""
        results = {}
        
        for i, url in enumerate(urls):
            logger.info(f"[{i + 1}/{len(urls)}] 下载：{url}")
            content = self.download(url)
            results[url] = content
            
            if delay > 0 and i < len(urls) - 1:
                import time
                time.sleep(delay)
        
        return results