"""
向量索引构建模块
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Optional
import pandas as pd
import numpy as np

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from configs.config import settings

class EmbeddingBuilder:
    """向量索引构建器"""
    
    def __init__(self):
        self.embedding_model = settings.embedding_model
        self.embedding_device = settings.embedding_device
        self.chroma_persist_directory = settings.chroma_persist_directory
        self.chroma_collection_name = settings.chroma_collection_name
        
        # 初始化模型
        self.model = None
        self.chroma_client = None
        self.collection = None
        
    def load_model(self):
        """加载嵌入模型"""
        try:
            from sentence_transformers import SentenceTransformer
            
            # 优先使用本地模型路径
            local_model_path = str(project_root / "data" / "models" / "bge-large-zh-v1.5")
            import os
            if os.path.exists(local_model_path):
                model_path = local_model_path
                print(f"🔄 加载本地嵌入模型: {model_path}")
            else:
                model_path = self.embedding_model
                print(f"🔄 加载远程嵌入模型: {model_path}")
            
            self.model = SentenceTransformer(
                model_path,
                device=self.embedding_device
            )
            print(f"✅ 模型加载成功，设备: {self.embedding_device}")
            
        except ImportError:
            print("❌ 请安装sentence-transformers: pip install sentence-transformers")
            raise
        except Exception as e:
            print(f"❌ 模型加载失败: {e}")
            raise
    
    def init_chroma(self):
        """初始化ChromaDB"""
        try:
            import chromadb
            
            print(f"🔄 初始化ChromaDB...")
            self.chroma_client = chromadb.PersistentClient(
                path=self.chroma_persist_directory
            )
            
            # 获取或创建集合
            self.collection = self.chroma_client.get_or_create_collection(
                name=self.chroma_collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            
            print(f"✅ ChromaDB初始化成功，集合: {self.chroma_collection_name}")
            
        except ImportError:
            print("❌ 请安装chromadb: pip install chromadb")
            raise
        except Exception as e:
            print(f"❌ ChromaDB初始化失败: {e}")
            raise
    
    def load_papers(self, file_path: str = None) -> List[Dict]:
        """加载论文数据"""
        try:
            if file_path:
                # 加载指定文件
                with open(file_path, 'r', encoding='utf-8') as f:
                    papers = json.load(f)
            else:
                # 优先加载cs_all_papers.json
                target_file = project_root / "data" / "raw" / "cs_all_papers.json"
                if target_file.exists():
                    print(f"📄 加载论文文件: {target_file.name}")
                    with open(target_file, 'r', encoding='utf-8') as f:
                        papers = json.load(f)
                else:
                    # 加载最新的论文文件
                    papers_dir = settings.raw_data_dir
                    json_files = list(papers_dir.glob("*.json"))
                    
                    if not json_files:
                        print("❌ 未找到论文数据文件")
                        return []
                    
                    # 按修改时间排序，获取最新的文件
                    latest_file = max(json_files, key=lambda x: x.stat().st_mtime)
                    print(f"📄 加载论文文件: {latest_file.name}")
                    
                    with open(latest_file, 'r', encoding='utf-8') as f:
                        papers = json.load(f)
            
            print(f"✅ 成功加载 {len(papers)} 篇论文")
            return papers
            
        except Exception as e:
            print(f"❌ 加载论文数据失败: {e}")
            return []
    
    def prepare_documents(self, papers: List[Dict]) -> List[Dict]:
        """准备文档数据"""
        documents = []
        
        for paper in papers:
            # 构建文档内容
            content = self._build_document_content(paper)
            
            # 构建元数据 - categories改为list类型
            categories = paper.get("categories", [])
            primary_category = paper.get("primary_category", categories[0] if categories else "")
            
            metadata = {
                "id": paper.get("id", ""),
                "title": paper.get("title", ""),
                "title_zh": paper.get("title_zh", paper.get("title", "")),
                "authors": ", ".join(paper.get("authors", [])),
                "categories": categories,  # list类型，支持$in过滤
                "primary_category": primary_category,  # 主分类，用于精确过滤
                "published": paper.get("published", ""),
                "pdf_url": paper.get("pdf_url", ""),
                "abstract_length": len(paper.get("abstract", ""))
            }
            
            documents.append({
                "id": paper.get("id", ""),
                "content": content,
                "metadata": metadata
            })
        
        return documents
    
    def _build_document_content(self, paper: Dict) -> str:
        """构建文档内容"""
        # 组合标题、摘要和分类
        title = paper.get("title", "")
        title_zh = paper.get("title_zh", "")
        abstract = paper.get("abstract", "")
        abstract_zh = paper.get("abstract_zh", "")
        categories = ", ".join(paper.get("categories", []))
        
        # 构建内容 - 优先使用中文
        if title_zh:
            content = f"标题: {title_zh} ({title})\n\n"
        else:
            content = f"标题: {title}\n\n"
        
        content += f"分类: {categories}\n\n"
        
        if abstract_zh:
            content += f"摘要: {abstract_zh}\n\n"
            content += f"Abstract: {abstract}"
        else:
            content += f"摘要: {abstract}"
        
        return content
    
    def build_embeddings(self, documents: List[Dict]) -> List[List[float]]:
        """构建向量嵌入"""
        if not self.model:
            self.load_model()
        
        print(f"🔄 构建向量嵌入，共 {len(documents)} 个文档...")
        
        # 提取文本内容
        texts = [doc["content"] for doc in documents]
        
        # 批量编码
        batch_size = 32
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i+batch_size]
            batch_embeddings = self.model.encode(
                batch_texts,
                show_progress_bar=True,
                batch_size=batch_size
            )
            embeddings.extend(batch_embeddings.tolist())
            
            print(f"  进度: {min(i+batch_size, len(texts))}/{len(texts)}")
        
        print(f"✅ 向量嵌入构建完成，维度: {len(embeddings[0])}")
        return embeddings
    
    def store_in_chroma(self, documents: List[Dict], embeddings: List[List[float]]):
        """存储到ChromaDB"""
        if not self.collection:
            self.init_chroma()
        
        print(f"🔄 存储到ChromaDB...")
        
        # 准备数据
        ids = [doc["id"] for doc in documents]
        contents = [doc["content"] for doc in documents]
        metadatas = [doc["metadata"] for doc in documents]
        
        # 批量存储 - 使用更小的批次避免内存问题
        batch_size = 50  # 减小批次大小
        total = len(documents)
        
        for i in range(0, total, batch_size):
            batch_ids = ids[i:i+batch_size]
            batch_contents = contents[i:i+batch_size]
            batch_embeddings = embeddings[i:i+batch_size]
            batch_metadatas = metadatas[i:i+batch_size]
            
            try:
                self.collection.add(
                    ids=batch_ids,
                    documents=batch_contents,
                    embeddings=batch_embeddings,
                    metadatas=batch_metadatas
                )
                current = min(i + batch_size, total)
                print(f"  进度: {current}/{total}")
            except Exception as e:
                print(f"  ❌ 批次 {i//batch_size + 1} 存储失败: {e}")
                # 尝试逐条存储
                for j in range(len(batch_ids)):
                    try:
                        self.collection.add(
                            ids=[batch_ids[j]],
                            documents=[batch_contents[j]],
                            embeddings=[batch_embeddings[j]],
                            metadatas=[batch_metadatas[j]]
                        )
                    except Exception as e2:
                        print(f"    单条存储失败: {e2}")
                continue
            
            print(f"  进度: {min(i+batch_size, len(documents))}/{len(documents)}")
        
        print(f"✅ 数据存储完成，集合大小: {self.collection.count()}")
    
    def build_index(self, papers: List[Dict] = None, file_path: str = None):
        """构建完整索引"""
        print("=" * 50)
        print("🔨 构建向量索引")
        print("=" * 50)
        
        # 加载论文数据
        if papers is None:
            papers = self.load_papers(file_path)
        
        if not papers:
            print("❌ 没有论文数据可处理")
            return
        
        # 准备文档
        documents = self.prepare_documents(papers)
        
        # 构建向量
        embeddings = self.build_embeddings(documents)
        
        # 存储到ChromaDB
        self.store_in_chroma(documents, embeddings)
        
        print("\n" + "=" * 50)
        print("✅ 索引构建完成！")
        print("=" * 50)
    
    def get_index_stats(self) -> Dict:
        """获取索引统计信息"""
        if not self.collection:
            self.init_chroma()
        
        stats = {
            "collection_name": self.chroma_collection_name,
            "total_documents": self.collection.count(),
            "persist_directory": self.chroma_persist_directory
        }
        
        return stats

def main():
    """主函数"""
    print("=" * 50)
    print("📚 ArXiv论文向量索引构建工具")
    print("=" * 50)
    
    # 创建构建器
    builder = EmbeddingBuilder()
    
    # 构建索引
    builder.build_index()
    
    # 显示统计信息
    stats = builder.get_index_stats()
    print("\n📊 索引统计:")
    print(f"  集合名称: {stats['collection_name']}")
    print(f"  文档总数: {stats['total_documents']}")
    print(f"  存储目录: {stats['persist_directory']}")

if __name__ == "__main__":
    main()