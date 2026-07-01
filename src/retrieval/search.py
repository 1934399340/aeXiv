"""
论文检索模块 - 使用FAISS
"""

import sys
import json
import os
import numpy as np
import faiss
from pathlib import Path
from typing import List, Dict, Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from configs.config import settings


class PaperSearcher:
    """论文检索器 - 使用FAISS"""
    
    def __init__(self):
        self.model = None
        self.index = None
        self.papers = []
        self.paper_map = {}
        
        # 路径配置
        self.index_path = Path(os.path.expanduser("~")) / "arxiv_index" / "arxiv.index"
        self.papers_path = Path(os.path.expanduser("~")) / "arxiv_index" / "papers.json"
        self.model_path = str(project_root / "data" / "models" / "bge-large-zh-v1.5")
        
    def load_model(self):
        """加载嵌入模型"""
        if self.model is None:
            from sentence_transformers import SentenceTransformer
            print(f"🔄 加载嵌入模型...")
            self.model = SentenceTransformer(self.model_path, device="cpu")
            print(f"✅ 模型加载成功")
    
    def load_index(self):
        """加载FAISS索引和论文数据"""
        if self.index is None:
            print(f"🔄 加载索引...")
            
            # 加载FAISS索引
            self.index = faiss.read_index(str(self.index_path))
            print(f"  索引加载完成，共 {self.index.ntotal} 条记录")
            
            # 加载论文元数据
            with open(self.papers_path, 'r', encoding='utf-8') as f:
                self.papers = json.load(f)
            self.paper_map = {p["id"]: p for p in self.papers}
            print(f"  论文元数据加载完成，共 {len(self.papers)} 篇")
    
    def search(self, query: str, search_type: str = "semantic", 
              top_k: int = 10, categories: List[str] = None) -> List[Dict]:
        """
        搜索论文
        
        Args:
            query: 搜索查询
            search_type: 搜索类型 (semantic, keyword, hybrid)
            top_k: 返回结果数量
            categories: 分类过滤列表
            
        Returns:
            搜索结果列表
        """
        # 加载模型和索引
        self.load_model()
        self.load_index()
        
        # 编码查询
        query_embedding = self.model.encode([query], show_progress_bar=False)
        query_embedding = np.array(query_embedding, dtype=np.float32)
        
        # 搜索
        distances, indices = self.index.search(query_embedding, top_k * 2)
        
        # 处理结果
        results = []
        for i, idx in enumerate(indices[0]):
            if idx == -1:
                continue
            
            paper = self.papers[idx]
            
            # 分类过滤
            if categories:
                paper_categories = paper.get("categories", [])
                if not any(c in paper_categories for c in categories):
                    continue
            
            # 转换距离为相似度
            distance = distances[0][i]
            similarity = 1 / (1 + distance)
            
            result = {
                "id": paper.get("id", ""),
                "score": float(similarity),
                "content": f"标题: {paper.get('title', '')}\n分类: {', '.join(paper.get('categories', []))}\n摘要: {paper.get('abstract', '')}",
                "metadata": {
                    "title": paper.get("title", ""),
                    "title_zh": paper.get("title_zh", paper.get("title", "")),
                    "authors": ", ".join(paper.get("authors", [])),
                    "categories": paper.get("categories", []),
                    "primary_category": paper.get("primary_category", ""),
                    "published": paper.get("published", ""),
                    "pdf_url": paper.get("pdf_url", ""),
                    "abs_url": paper.get("abs_url", "")
                }
            }
            
            results.append(result)
            
            if len(results) >= top_k:
                break
        
        return results
    
    def search_semantic(self, query: str, top_k: int = 10, categories: List[str] = None) -> List[Dict]:
        """语义搜索"""
        return self.search(query, "semantic", top_k, categories)
    
    def search_keyword(self, query: str, top_k: int = 10, categories: List[str] = None) -> List[Dict]:
        """关键词搜索（使用标题和摘要匹配）"""
        self.load_index()
        
        results = []
        query_lower = query.lower()
        
        for paper in self.papers:
            # 分类过滤
            if categories:
                paper_categories = paper.get("categories", [])
                if not any(c in paper_categories for c in categories):
                    continue
            
            # 关键词匹配
            title = paper.get("title", "").lower()
            abstract = paper.get("abstract", "").lower()
            
            if query_lower in title or query_lower in abstract:
                result = {
                    "id": paper.get("id", ""),
                    "score": 1.0,
                    "content": f"标题: {paper.get('title', '')}\n分类: {', '.join(paper.get('categories', []))}\n摘要: {paper.get('abstract', '')}",
                    "metadata": {
                        "title": paper.get("title", ""),
                        "title_zh": paper.get("title_zh", paper.get("title", "")),
                        "authors": ", ".join(paper.get("authors", [])),
                        "categories": paper.get("categories", []),
                        "primary_category": paper.get("primary_category", ""),
                        "published": paper.get("published", ""),
                        "pdf_url": paper.get("pdf_url", ""),
                        "abs_url": paper.get("abs_url", "")
                    }
                }
                results.append(paper)
                
                if len(results) >= top_k:
                    break
        
        return results
    
    def search_hybrid(self, query: str, top_k: int = 10, 
                     semantic_weight: float = 0.7, categories: List[str] = None) -> List[Dict]:
        """混合搜索"""
        # 语义搜索
        semantic_results = self.search_semantic(query, top_k, categories)
        
        # 关键词搜索
        keyword_results = self.search_keyword(query, top_k, categories)
        
        # 合并结果
        paper_scores = {}
        
        for paper in semantic_results:
            paper_id = paper["id"]
            paper_scores[paper_id] = {
                "paper": paper,
                "score": paper["score"] * semantic_weight
            }
        
        for paper in keyword_results:
            paper_id = paper["id"]
            if paper_id in paper_scores:
                paper_scores[paper_id]["score"] += paper["score"] * (1 - semantic_weight)
            else:
                paper_scores[paper_id] = {
                    "paper": paper,
                    "score": paper["score"] * (1 - semantic_weight)
                }
        
        # 按分数排序
        sorted_papers = sorted(
            paper_scores.values(),
            key=lambda x: x["score"],
            reverse=True
        )[:top_k]
        
        # 转换格式
        results = []
        for item in sorted_papers:
            paper = item["paper"]
            paper["score"] = item["score"]
            results.append(paper)
        
        return results


def main():
    """测试检索"""
    searcher = PaperSearcher()
    
    # 测试搜索
    print("\n🔍 测试搜索...")
    results = searcher.search("attention mechanism transformer", top_k=5)
    
    print(f"\n搜索结果:")
    for i, r in enumerate(results, 1):
        print(f"{i}. {r['metadata']['title'][:50]}... (相似度: {r['score']:.3f})")


if __name__ == "__main__":
    main()
