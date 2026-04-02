"""URL 数据模型"""

from dataclasses import dataclass, field
from typing import Set, List, Optional
from datetime import datetime


@dataclass
class URLData:
    """URL 数据"""
    url: str
    source_file: str = ""
    has_domain: bool = True
    extracted_at: datetime = field(default_factory=datetime.now)


@dataclass
class ExtractionResult:
    """提取结果"""
    total_urls: int = 0
    with_domain: List[str] = field(default_factory=list)
    without_domain: List[str] = field(default_factory=list)
    processed_files: int = 0
    failed_files: int = 0
    extraction_time: float = 0.0
    
    def summary(self) -> str:
        """生成摘要"""
        return (
            f"\n{'='*50}\n"
            f"提取完成摘要:\n"
            f"  - 处理文件数：{self.processed_files}\n"
            f"  - 失败文件数：{self.failed_files}\n"
            f"  - 总 URL 数：{self.total_urls}\n"
            f"  - 含域名 URL: {len(self.with_domain)}\n"
            f"  - 无域名路径：{len(self.without_domain)}\n"
            f"  - 耗时：{self.extraction_time:.2f} 秒\n"
            f"{'='*50}"
        )