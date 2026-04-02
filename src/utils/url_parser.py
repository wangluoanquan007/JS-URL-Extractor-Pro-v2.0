"""URL 解析和过滤模块 (路径标准化优化版)"""

import re
from urllib.parse import urlparse
from typing import Set, Tuple, List
from src.utils.logger import setup_logger

logger = setup_logger("URLParser")


class URLParser:
    """URL 解析器"""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.excluded_schemes = ['javascript:', 'data:', 'mailto:', 'tel:', '#']
        self.excluded_extensions = [
            '.css', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico',
            '.woff', '.woff2', '.ttf', '.eot'
        ]
        
        # 正则表达式：匹配引号内的路径
        self.pattern_quoted_path = re.compile(
            r'["\']((?:/[^\s"\']*|[a-zA-Z0-9_\-./]*[a-zA-Z0-9_\-]+\.[a-zA-Z0-9]+)[^\s"\']*)["\']'
        )
        
        self.pattern_absolute = re.compile(r'https?://[^\s"\'<>${}\]\[]+(?<!\${)')
        
        self.patterns_special = [
            re.compile(r'fetch\s*\(\s*["\']([^"\']+)["\']'),
            re.compile(r'axios\.(?:get|post|put|delete)\s*\(\s*["\']([^"\']+)["\']'),
            re.compile(r'import\s*\(\s*["\']([^"\']+)["\']'),
        ]

    def extract_urls(self, js_content: str, base_url: str = None) -> Set[str]:
        """从 JS 内容中提取所有 URL（原始形态，不拼接）"""
        urls = set()
        
        if not js_content:
            return urls
        
        # 1. 提取绝对 URL
        absolute_matches = self.pattern_absolute.findall(js_content)
        for match in absolute_matches:
            clean_url = self._clean_url(match)
            if clean_url and self._is_valid_url(clean_url):
                urls.add(clean_url)
        
        # 2. 提取相对路径
        relative_matches = self.pattern_quoted_path.findall(js_content)
        for match in relative_matches:
            clean_path = self._clean_url(match)
            if not clean_path:
                continue
            
            if self._is_likely_path(clean_path):
                if not clean_path.startswith(('http://', 'https://')):
                    urls.add(clean_path)
        
        # 3. 提取特殊模式
        for pattern in self.patterns_special:
            matches = pattern.findall(js_content)
            for match in matches:
                clean_val = self._clean_url(match)
                if clean_val and not clean_val.startswith(('http://', 'https://')):
                    if self._is_likely_path(clean_val):
                        urls.add(clean_val)
                elif clean_val and self._is_valid_url(clean_val):
                    urls.add(clean_val)
        
        logger.debug(f"提取到 {len(urls)} 个原始 URL")
        return urls
    
    def _is_likely_path(self, s: str) -> bool:
        """判断字符串是否像一个文件路径"""
        if not s or len(s) < 2:
            return False
        if '${' in s or '{' in s:
            return False
        
        if s.startswith(('/', './', '../')):
            return True
        
        if '/' in s:
            return True
        
        common_exts = ['.js', '.css', '.json', '.html', '.xml', '.svg', '.png', '.jpg', '.jpeg', '.gif']
        if any(s.lower().endswith(ext) for ext in common_exts):
            return True
            
        return False

    def _clean_url(self, url: str) -> str:
        """清理 URL 两端符号"""
        if not url:
            return ''
        url = re.sub(r'[,"\'\)\]]+$', '', url).strip()
        if '${' in url or '{' in url or '}' in url:
            return ''
        if url.startswith('+') or url.endswith('+'):
            return ''
        return url
    
    def _is_valid_url(self, url: str) -> bool:
        """验证绝对 URL 有效性"""
        if not url or len(url) < 5:
            return False
        parsed = urlparse(url)
        if parsed.scheme.lower() in [s.replace(':', '') for s in self.excluded_schemes]:
            return False
        for ext in self.excluded_extensions:
            if url.lower().endswith(ext):
                return False
        return True

    def filter_urls(self, urls: Set[str]) -> Set[str]:
        """过滤无效 URL"""
        valid_urls = set()
        for url in urls:
            if url.startswith(('http://', 'https://')):
                if self._is_valid_url(url):
                    valid_urls.add(url)
            else:
                if self._is_likely_path(url):
                    valid_urls.add(url)
        return valid_urls

    def _normalize_relative_path(self, path: str) -> str:
        """
        标准化相对路径：
        - assets/xxx.js  → /assets/xxx.js
        - ./utils.js     → /utils.js
        - ../lib.js      → /lib.js
        - /api/v1        → /api/v1 (不变)
        """
        if not path:
            return path
        
        # 如果已经以 / 开头，保持不变
        if path.startswith('/'):
            return path
        
        # 去掉 ./ 前缀
        if path.startswith('./'):
            path = path[2:]
        
        # 去掉 ../ 前缀 (简化处理，统一转为根路径)
        while path.startswith('../'):
            path = path[3:]
        
        # 如果去掉前缀后为空，返回 /
        if not path:
            return '/'
        
        # 前面加上 /
        return '/' + path

    def classify_urls(self, urls: Set[str]) -> Tuple[List[str], List[str]]:
        """
        分类 URL 并标准化相对路径：
        1. with_domain: 以 http:// 或 https:// 开头 (保持不变)
        2. without_domain: 其他所有，标准化为 / 开头
        """
        with_domain = []
        without_domain = []
        
        for url in urls:
            if url.startswith(('http://', 'https://')):
                with_domain.append(url)
            else:
                # 对相对路径进行标准化
                normalized = self._normalize_relative_path(url)
                without_domain.append(normalized)
        
        # 排序并去重
        with_domain = sorted(set(with_domain))
        without_domain = sorted(set(without_domain))
        
        logger.info(f"分类完成：{len(with_domain)} 个完整 URL, {len(without_domain)} 个相对路径 (已标准化)")
        return with_domain, without_domain