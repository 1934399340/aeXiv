"""
ArXiv论文数据获取模块
"""

import requests
import xml.etree.ElementTree as ET
import json
import time
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import sys

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from configs.config import settings

class ArxivFetcher:
    """ArXiv论文获取器"""
    
    def __init__(self):
        self.api_url = settings.arxiv_api_url
        self.delay = settings.arxiv_api_delay
        self.max_results = settings.arxiv_max_results
        
    def fetch_papers(self, query: str, start: int = 0, 
                    max_results: int = 10, sort_by: str = "relevance",
                    sort_order: str = "descending") -> List[Dict]:
        """
        从ArXiv API获取论文
        
        Args:
            query: 搜索查询
            start: 起始位置
            max_results: 最大返回数量
            sort_by: 排序字段 (relevance, lastUpdatedDate, submittedDate)
            sort_order: 排序方向 (ascending, descending)
            
        Returns:
            论文列表
        """
        try:
            # 构建请求参数
            params = {
                "search_query": query,
                "start": start,
                "max_results": min(max_results, self.max_results),
                "sortBy": sort_by,
                "sortOrder": sort_order
            }
            
            # 发送请求
            print(f"🔍 正在获取论文: {query}")
            response = requests.get(self.api_url, params=params, timeout=30)
            response.raise_for_status()
            
            # 解析XML响应
            papers = self._parse_xml_response(response.text)
            
            print(f"✅ 成功获取 {len(papers)} 篇论文")
            return papers
            
        except requests.exceptions.RequestException as e:
            print(f"❌ 请求失败: {e}")
            return []
        except Exception as e:
            print(f"❌ 解析失败: {e}")
            return []
    
    def _parse_xml_response(self, xml_content: str) -> List[Dict]:
        """解析XML响应"""
        papers = []
        
        try:
            # 解析XML
            root = ET.fromstring(xml_content)
            
            # 命名空间
            ns = {
                'atom': 'http://www.w3.org/2005/Atom',
                'arxiv': 'http://arxiv.org/schemas/atom'
            }
            
            # 获取所有论文条目
            entries = root.findall('atom:entry', ns)
            
            for entry in entries:
                paper = self._parse_entry(entry, ns)
                if paper:
                    papers.append(paper)
            
            return papers
            
        except ET.ParseError as e:
            print(f"❌ XML解析错误: {e}")
            return []
    
    def _parse_entry(self, entry, ns: Dict) -> Optional[Dict]:
        """解析单个论文条目"""
        try:
            # 提取基本信息
            paper_id = self._extract_text(entry, 'atom:id', ns)
            title = self._extract_text(entry, 'atom:title', ns).strip()
            summary = self._extract_text(entry, 'atom:summary', ns).strip()
            
            # 提取作者
            authors = []
            author_elements = entry.findall('atom:author', ns)
            for author_elem in author_elements:
                name = self._extract_text(author_elem, 'atom:name', ns)
                if name:
                    authors.append(name)
            
            # 提取分类
            categories = []
            category_elements = entry.findall('atom:category', ns)
            for cat_elem in category_elements:
                term = cat_elem.get('term')
                if term:
                    categories.append(term)
            
            # 提取时间
            published = self._extract_text(entry, 'atom:published', ns)
            updated = self._extract_text(entry, 'atom:updated', ns)
            
            # 提取链接
            links = {}
            link_elements = entry.findall('atom:link', ns)
            for link_elem in link_elements:
                href = link_elem.get('href')
                link_title = link_elem.get('title')
                if href and link_title:
                    links[link_title.lower()] = href
            
            # 构建论文数据
            # primary_category取categories列表的第一个
            primary_category = categories[0] if categories else ""
            
            paper = {
                "id": paper_id,
                "title": title,
                "authors": authors,
                "abstract": summary,
                "categories": categories,
                "primary_category": primary_category,
                "published": published,
                "updated": updated,
                "pdf_url": links.get("pdf", ""),
                "abs_url": links.get("abs", ""),
                "doi": self._extract_text(entry, 'arxiv:doi', ns),
                "comment": self._extract_text(entry, 'arxiv:comment', ns),
                "journal_ref": self._extract_text(entry, 'arxiv:journal_ref', ns)
            }
            
            return paper
            
        except Exception as e:
            print(f"❌ 解析论文条目失败: {e}")
            return None
    
    def _extract_text(self, element, tag: str, ns: Dict) -> str:
        """提取XML元素文本"""
        try:
            elem = element.find(tag, ns)
            return elem.text if elem is not None else ""
        except:
            return ""
    
    def fetch_papers_by_category(self, category: str, 
                                max_results: int = 100) -> List[Dict]:
        """
        按分类获取论文
        
        Args:
            category: 论文分类 (如 cs.AI, cs.CL)
            max_results: 最大返回数量
            
        Returns:
            论文列表
        """
        query = f"cat:{category}"
        papers = []
        
        # 分批获取
        batch_size = 100
        for start in range(0, max_results, batch_size):
            current_batch = min(batch_size, max_results - start)
            batch_papers = self.fetch_papers(
                query=query,
                start=start,
                max_results=current_batch,
                sort_by="lastUpdatedDate",
                sort_order="descending"
            )
            
            papers.extend(batch_papers)
            
            # 避免请求过快
            if start + batch_size < max_results:
                print(f"⏳ 等待 {self.delay} 秒...")
                time.sleep(self.delay)
        
        return papers
    
    def save_papers(self, papers: List[Dict], filename: str = None) -> str:
        """
        保存论文数据
        
        Args:
            papers: 论文列表
            filename: 文件名
            
        Returns:
            保存的文件路径
        """
        if not papers:
            print("❌ 没有论文数据可保存")
            return ""
        
        # 生成文件名
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"arxiv_papers_{timestamp}.json"
        
        # 保存路径
        save_path = settings.raw_data_dir / filename
        
        try:
            # 保存为JSON
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(papers, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 论文数据已保存到: {save_path}")
            print(f"📊 共保存 {len(papers)} 篇论文")
            
            return str(save_path)
            
        except Exception as e:
            print(f"❌ 保存失败: {e}")
            return ""
    
    def get_paper_stats(self, papers: List[Dict]) -> Dict:
        """获取论文统计信息"""
        if not papers:
            return {}
        
        # 统计分类
        categories = {}
        for paper in papers:
            for cat in paper.get("categories", []):
                categories[cat] = categories.get(cat, 0) + 1
        
        # 统计作者
        authors = {}
        for paper in papers:
            for author in paper.get("authors", []):
                authors[author] = authors.get(author, 0) + 1
        
        # 统计时间
        dates = []
        for paper in papers:
            if paper.get("published"):
                dates.append(paper["published"][:10])  # 只取日期部分
        
        stats = {
            "total_papers": len(papers),
            "categories": dict(sorted(categories.items(), key=lambda x: x[1], reverse=True)[:10]),
            "top_authors": dict(sorted(authors.items(), key=lambda x: x[1], reverse=True)[:10]),
            "date_range": {
                "earliest": min(dates) if dates else "",
                "latest": max(dates) if dates else ""
            },
            "avg_abstract_length": sum(len(p.get("abstract", "")) for p in papers) / len(papers)
        }
        
        return stats

def main():
    """主函数"""
    print("=" * 50)
    print("📚 ArXiv论文数据获取工具")
    print("=" * 50)
    
    # 创建获取器
    fetcher = ArxivFetcher()
    
    # 示例：获取AI领域论文
    category = "cs.AI"
    max_results = 50
    
    print(f"\n🎯 目标: 获取 {category} 分类的 {max_results} 篇论文")
    
    # 获取论文
    papers = fetcher.fetch_papers_by_category(category, max_results)
    
    if papers:
        # 保存论文
        save_path = fetcher.save_papers(papers)
        
        # 显示统计信息
        stats = fetcher.get_paper_stats(papers)
        print("\n📊 论文统计:")
        print(f"  总论文数: {stats['total_papers']}")
        print(f"  分类分布: {stats['categories']}")
        print(f"  时间范围: {stats['date_range']}")
        print(f"  平均摘要长度: {stats['avg_abstract_length']:.0f} 字符")
        
        # 显示前3篇论文
        print("\n📄 前3篇论文:")
        for i, paper in enumerate(papers[:3], 1):
            print(f"\n{i}. {paper['title']}")
            print(f"   作者: {', '.join(paper['authors'][:3])}")
            print(f"   分类: {', '.join(paper['categories'][:3])}")
            print(f"   发布时间: {paper['published'][:10]}")
    else:
        print("❌ 未获取到论文数据")

if __name__ == "__main__":
    main()