"""
使用FAISS的检索模块（替代ChromaDB）
"""

import sys
import json
import faiss
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional
import sqlite3

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from configs.config import settings


class FAISSSearcher:
    """FAISS检索器"""
    
    def __init__(self):
        self.model = None
        self.index = None
        self.papers = []
        self.db_path = project_root / "data" / "embeddings" / "chroma" / "chroma.sqlite3"
        
    def load_model(self):
        """加载嵌入模型"""
        if self.model is None:
            from sentence_transformers import SentenceTransformer
            local_model_path = str(project_root / "data" / "models" / "bge-large-zh-v1.5")
            print(f"🔄 加载嵌入模型...")
            self.model = SentenceTransformer(local_model_path, device="cpu")
            print(f"✅ 模型加载完成")
    
    def load_from_sqlite(self):
        """从SQLite加载数据"""
        print(f"🔄 从SQLite加载数据...")
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # 获取嵌入向量
        cursor.execute("SELECT id, embedding FROM embeddings")
        rows = cursor.fetchall()
        
        ids = []
        embeddings = []
        
        for row in rows:
            ids.append(row[0])
            # 解析二进制嵌入数据
            embedding = np.frombuffer(row[1], dtype=np.float32)
            embeddings.append(embedding)
        
        conn.close()
        
        # 转换为numpy数组
        embeddings_array = np.array(embeddings, dtype=np.float32)
        
        print(f"✅ 加载 {len(ids)} 个嵌入向量")
        print(f"   向量维度: {embeddings_array.shape[1]}")
        
        return ids, embeddings_array
    
    def load_papers_metadata(self):
        """加载论文元数据"""
        print(f"📄 加载论文元数据...")
        
        papers_file = project_root / "data" / "raw" / "cs_all_papers.json"
        with open(papers_file, 'r', encoding='utf-8') as f:
            self.papers = json.load(f)
        
        # 创建ID到论文的映射
        self.paper_map = {p["id"]: p for p in self.papers}
        
        print(f"✅ 加载 {len(self.papers)} 篇论文元数据")
    
    def build_index(self):
        """构建FAISS索引"""
        print(f"\n🔨 构建FAISS索引...")
        
        # 加载数据
        ids, embeddings = self.load_from_sqlite()
        self.load_papers_metadata()
        
        # 创建FAISS索引
        dimension = embeddings.shape[1]
        
        # 使用IVF索引（适合大数据量）
        nlist = min(100, len(embeddings) // 10)  # 聚类数量
        quantizer = faiss.IndexFlatL2(dimension)
        self.index = faiss.IndexIVFFlat(quantizer, dimension, nlist, faiss.METRIC_L2)
        
        # 训练索引
        print(f"  训练索引（nlist={nlist}）...")
        self.index.train(embeddings)
        
        # 添加向量
        print(f"  添加 {len(embeddings)} 个向量...")
        self.index.add(embeddings)
        
        # 保存ID映射
        self.ids = ids
        
        # 设置搜索参数
        self.index.nprobe = 10  # 搜索时检查的聚类数量
        
        print(f"✅ FAISS索引构建完成")
        print(f"   索引大小: {self.index.ntotal}")
    
    def search(self, query: str, top_k: int = 10, categories: List[str] = None) -> List[Dict]:
        """
        搜索
        
        Args:
            query: 查询文本
            top_k: 返回数量
            categories: 分类过滤
            
        Returns:
            搜索结果
        """
        if self.model is None:
            self.load_model()
        
        if self.index is None:
            self.build_index()
        
        # 编码查询
        query_embedding = self.model.encode([query], show_progress_bar=False)
        query_embedding = np.array(query_embedding, dtype=np.float32)
        
        # 搜索
        distances, indices = self.index.search(query_embedding, top_k * 2)  # 多搜索一些用于过滤
        
        # 处理结果
        results = []
        for i, idx in enumerate(indices[0]):
            if idx == -1:
                continue
            
            paper_id = self.ids[idx]
            paper = self.paper_map.get(paper_id, {})
            
            # 分类过滤
            if categories:
                paper_categories = paper.get("categories", [])
                if not any(c in paper_categories for c in categories):
                    continue
            
            # 转换距离为相似度（L2距离越小越相似）
            distance = distances[0][i]
            similarity = 1 / (1 + distance)
            
            result = {
                "id": paper_id,
                "score": float(similarity),
                "metadata": {
                    "title": paper.get("title", ""),
                    "title_zh": paper.get("title_zh", paper.get("title", "")),
                    "authors": ", ".join(paper.get("authors", [])),
                    "categories": paper.get("categories", []),
                    "primary_category": paper.get("primary_category", ""),
                    "published": paper.get("published", ""),
                    "pdf_url": paper.get("pdf_url", "")
                },
                "content": f"标题: {paper.get('title', '')}\n分类: {', '.join(paper.get('categories', []))}\n摘要: {paper.get('abstract', '')}"
            }
            
            results.append(result)
            
            if len(results) >= top_k:
                break
        
        return results
    
    def save_index(self, path: str):
        """保存FAISS索引"""
        if self.index is not None:
            faiss.write_index(self.index, path)
            # 保存ID映射
            id_file = path + ".ids.json"
            with open(id_file, 'w', encoding='utf-8') as f:
                json.dump(self.ids, f)
            print(f"✅ 索引已保存到 {path}")
    
    def load_index(self, path: str):
        """加载FAISS索引"""
        if Path(path).exists():
            self.index = faiss.read_index(path)
            # 加载ID映射
            id_file = path + ".ids.json"
            with open(id_file, 'r', encoding='utf-8') as f:
                self.ids = json.load(f)
            print(f"✅ 索引已加载，共 {self.index.ntotal} 条记录")
            return True
        return False


def main():
    """测试FAISS检索"""
    searcher = FAISSSearcher()
    
    # 构建索引
    searcher.build_index()
    
    # 保存索引
    index_path = str(project_root / "data" / "embeddings" / "faiss.index")
    searcher.save_index(index_path)
    
    # 测试搜索
    print("\n🔍 测试搜索...")
    results = searcher.search("attention mechanism transformer", top_k=5)
    
    print(f"\n搜索结果:")
    for i, r in enumerate(results, 1):
        print(f"{i}. {r['metadata']['title'][:50]}... (相似度: {r['score']:.3f})")


if __name__ == "__main__":
    main()
