# -*- coding: utf-8 -*-
"""
文档管理模块 - 管理用户上传的文档和向量索引
"""

import json
import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

project_root = Path(__file__).parent.parent.parent


class DocumentManager:
    """文档管理器"""
    
    def __init__(self):
        self.user_docs_dir = project_root / "data" / "user_docs"
        self.user_embeddings_dir = project_root / "data" / "user_embeddings"
        self.user_docs_dir.mkdir(parents=True, exist_ok=True)
        self.user_embeddings_dir.mkdir(parents=True, exist_ok=True)
    
    def get_user_docs(self, user_id: str = "default") -> List[Dict]:
        """获取用户文档列表"""
        index_file = self.user_docs_dir / "docs_index.json"
        
        if not index_file.exists():
            return []
        
        with open(index_file, "r", encoding="utf-8") as f:
            docs_index = json.load(f)
        
        return [doc for doc in docs_index if doc.get("user_id") == user_id]
    
    def get_doc_by_id(self, doc_id: str) -> Optional[Dict]:
        """根据ID获取文档"""
        index_file = self.user_docs_dir / "docs_index.json"
        
        if not index_file.exists():
            return None
        
        with open(index_file, "r", encoding="utf-8") as f:
            docs_index = json.load(f)
        
        for doc in docs_index:
            if doc.get("id") == doc_id:
                return doc
        
        return None
    
    def delete_document(self, doc_id: str, user_id: str = "default") -> bool:
        """删除文档及其向量"""
        try:
            # 1. 删除文件
            user_dir = self.user_docs_dir / user_id
            for file_path in user_dir.glob(f"{doc_id}.*"):
                file_path.unlink()
                print(f"已删除文件: {file_path}")
            
            # 2. 删除向量索引文件
            embedding_dir = self.user_embeddings_dir / user_id
            if embedding_dir.exists():
                for file_path in embedding_dir.glob(f"{doc_id}.*"):
                    file_path.unlink()
                    print(f"已删除向量文件: {file_path}")
            
            # 3. 更新文档索引
            index_file = self.user_docs_dir / "docs_index.json"
            if index_file.exists():
                with open(index_file, "r", encoding="utf-8") as f:
                    docs_index = json.load(f)
                
                docs_index = [doc for doc in docs_index if doc.get("id") != doc_id]
                
                with open(index_file, "w", encoding="utf-8") as f:
                    json.dump(docs_index, f, ensure_ascii=False, indent=2)
            
            print(f"文档 {doc_id} 已删除")
            return True
            
        except Exception as e:
            print(f"删除文档失败: {e}")
            return False
    
    def rebuild_user_index(self, user_id: str) -> bool:
        """重建用户向量索引"""
        try:
            from src.data.document_parser import DocumentParser
            from sentence_transformers import SentenceTransformer
            import faiss
            import numpy as np
            
            print(f"重建用户 {user_id} 的向量索引...")
            
            # 加载用户文档
            docs = self.get_user_docs(user_id)
            if not docs:
                print("没有文档需要处理")
                return True
            
            # 加载模型
            model_path = str(project_root / "data" / "models" / "bge-large-zh-v1.5")
            model = SentenceTransformer(model_path, device="cpu")
            
            # 获取文档内容并分块
            parser = DocumentParser()
            all_chunks = []
            chunk_mapping = []
            
            for doc in docs:
                content = parser.get_doc_content(doc["id"], user_id)
                if content:
                    chunks = self._chunk_text(content)
                    for i, chunk in enumerate(chunks):
                        all_chunks.append(chunk)
                        chunk_mapping.append({
                            "doc_id": doc["id"],
                            "chunk_index": i,
                            "content": chunk
                        })
            
            if not all_chunks:
                print("没有内容需要向量化")
                return True
            
            # 向量化
            print(f"向量化 {len(all_chunks)} 个文本块...")
            embeddings = model.encode(all_chunks, show_progress_bar=True)
            
            # 构建FAISS索引
            dimension = embeddings.shape[1]
            index = faiss.IndexFlatL2(dimension)
            index.add(np.array(embeddings, dtype=np.float32))
            
            # 保存索引
            user_embedding_dir = self.user_embeddings_dir / user_id
            user_embedding_dir.mkdir(parents=True, exist_ok=True)
            
            index_path = user_embedding_dir / "index.faiss"
            faiss.write_index(index, str(index_path))
            
            # 保存分块映射
            mapping_path = user_embedding_dir / "chunks.json"
            with open(mapping_path, "w", encoding="utf-8") as f:
                json.dump(chunk_mapping, f, ensure_ascii=False, indent=2)
            
            print(f"索引构建完成，共 {len(all_chunks)} 个文本块")
            return True
            
        except Exception as e:
            print(f"重建索引失败: {e}")
            return False
    
    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """文本分块"""
        if not text:
            return []
        
        chunks = []
        paragraphs = text.split("\n\n")
        
        current_chunk = ""
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            if len(current_chunk) + len(para) > chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para
            else:
                current_chunk = current_chunk + "\n\n" + para if current_chunk else para
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def get_user_stats(self, user_id: str = "default") -> Dict:
        """获取用户文档统计"""
        docs = self.get_user_docs(user_id)
        
        total_size = sum(doc.get("file_size", 0) for doc in docs)
        total_chars = sum(doc.get("char_count", 0) for doc in docs)
        
        # 检查索引状态
        embedding_dir = self.user_embeddings_dir / user_id
        index_exists = (embedding_dir / "index.faiss").exists()
        
        return {
            "total_docs": len(docs),
            "total_size": total_size,
            "total_chars": total_chars,
            "index_exists": index_exists
        }