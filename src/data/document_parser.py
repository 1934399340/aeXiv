# -*- coding: utf-8 -*-
"""
文档解析模块 - 支持PDF、Word、Markdown、纯文本
"""

import os
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

project_root = Path(__file__).parent.parent.parent


class DocumentParser:
    """文档解析器"""
    
    def __init__(self):
        self.user_docs_dir = project_root / "data" / "user_docs"
        self.user_docs_dir.mkdir(parents=True, exist_ok=True)
    
    def parse_file(self, file_content: bytes, filename: str, user_id: str = "default") -> Dict:
        """
        解析上传的文件
        
        Args:
            file_content: 文件内容（二进制）
            filename: 文件名
            user_id: 用户ID
            
        Returns:
            解析后的文档数据
        """
        file_ext = Path(filename).suffix.lower()
        
        # 生成文档ID
        doc_id = f"doc_{hashlib.md5(file_content).hexdigest()[:12]}"
        
        # 根据文件类型解析
        if file_ext == ".pdf":
            content = self._parse_pdf(file_content)
        elif file_ext == ".docx":
            content = self._parse_docx(file_content)
        elif file_ext == ".md":
            content = self._parse_markdown(file_content)
        elif file_ext == ".txt":
            content = file_content.decode("utf-8", errors="ignore")
        else:
            raise ValueError(f"不支持的文件格式: {file_ext}")
        
        # 提取标题（从内容第一行或文件名）
        title = self._extract_title(content, filename)
        
        # 构建文档数据
        doc_data = {
            "id": doc_id,
            "filename": filename,
            "file_type": file_ext,
            "file_size": len(file_content),
            "title": title,
            "content": content,
            "metadata": {
                "char_count": len(content),
                "word_count": len(content.split()),
            },
            "upload_time": datetime.now().isoformat(),
            "user_id": user_id,
            "status": "parsed"
        }
        
        # 保存文件
        self._save_file(file_content, user_id, doc_id, filename)
        
        # 保存文档索引
        self._save_doc_index(doc_data)
        
        return doc_data
    
    def _parse_pdf(self, file_content: bytes) -> str:
        """解析PDF文件"""
        try:
            import PyPDF2
            import io
            
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            content = ""
            
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    content += text + "\n\n"
            
            return content.strip()
        except ImportError:
            print("请安装PyPDF2: pip install PyPDF2")
            return ""
        except Exception as e:
            print(f"PDF解析失败: {e}")
            return ""
    
    def _parse_docx(self, file_content: bytes) -> str:
        """解析Word文件"""
        try:
            from docx import Document
            import io
            
            doc = Document(io.BytesIO(file_content))
            content = ""
            
            for para in doc.paragraphs:
                if para.text.strip():
                    content += para.text + "\n"
            
            return content.strip()
        except ImportError:
            print("请安装python-docx: pip install python-docx")
            return ""
        except Exception as e:
            print(f"Word解析失败: {e}")
            return ""
    
    def _parse_markdown(self, file_content: bytes) -> str:
        """解析Markdown文件"""
        try:
            import markdown
            
            text = file_content.decode("utf-8", errors="ignore")
            # 转换为纯文本（去除格式）
            html = markdown.markdown(text)
            # 简单去除HTML标签
            import re
            content = re.sub(r'<[^>]+>', '', html)
            
            return content.strip()
        except ImportError:
            # 没有markdown库，直接返回原文
            return file_content.decode("utf-8", errors="ignore")
        except Exception as e:
            print(f"Markdown解析失败: {e}")
            return file_content.decode("utf-8", errors="ignore")
    
    def _extract_title(self, content: str, filename: str) -> str:
        """从内容或文件名提取标题"""
        # 尝试从内容第一行提取
        lines = content.split("\n")
        for line in lines:
            line = line.strip()
            if line and len(line) > 3 and len(line) < 200:
                # 去除Markdown标题符号
                title = line.lstrip("#").strip()
                if title:
                    return title
        
        # 使用文件名（去掉扩展名）
        return Path(filename).stem
    
    def _save_file(self, file_content: bytes, user_id: str, doc_id: str, filename: str):
        """保存文件到磁盘"""
        user_dir = self.user_docs_dir / user_id
        user_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = user_dir / f"{doc_id}{Path(filename).suffix}"
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        print(f"文件已保存: {file_path}")
    
    def _save_doc_index(self, doc_data: Dict):
        """保存文档索引"""
        index_file = self.user_docs_dir / "docs_index.json"
        
        # 加载现有索引
        docs_index = []
        if index_file.exists():
            with open(index_file, "r", encoding="utf-8") as f:
                docs_index = json.load(f)
        
        # 添加新文档
        doc_summary = {
            "id": doc_data["id"],
            "filename": doc_data["filename"],
            "file_type": doc_data["file_type"],
            "title": doc_data["title"],
            "user_id": doc_data["user_id"],
            "upload_time": doc_data["upload_time"],
            "status": doc_data["status"],
            "char_count": doc_data["metadata"]["char_count"]
        }
        docs_index.append(doc_summary)
        
        # 保存索引
        with open(index_file, "w", encoding="utf-8") as f:
            json.dump(docs_index, f, ensure_ascii=False, indent=2)
    
    def get_user_docs(self, user_id: str = "default") -> List[Dict]:
        """获取用户文档列表"""
        index_file = self.user_docs_dir / "docs_index.json"
        
        if not index_file.exists():
            return []
        
        with open(index_file, "r", encoding="utf-8") as f:
            docs_index = json.load(f)
        
        return [doc for doc in docs_index if doc.get("user_id") == user_id]
    
    def get_doc_content(self, doc_id: str, user_id: str = "default") -> Optional[str]:
        """获取文档内容"""
        user_dir = self.user_docs_dir / user_id
        
        # 查找文件
        for file_path in user_dir.glob(f"{doc_id}.*"):
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        
        return None
    
    def delete_doc(self, doc_id: str, user_id: str = "default") -> bool:
        """删除文档"""
        # 删除文件
        user_dir = self.user_docs_dir / user_id
        for file_path in user_dir.glob(f"{doc_id}.*"):
            file_path.unlink()
        
        # 更新索引
        index_file = self.user_docs_dir / "docs_index.json"
        if index_file.exists():
            with open(index_file, "r", encoding="utf-8") as f:
                docs_index = json.load(f)
            
            docs_index = [doc for doc in docs_index if doc.get("id") != doc_id]
            
            with open(index_file, "w", encoding="utf-8") as f:
                json.dump(docs_index, f, ensure_ascii=False, indent=2)
        
        return True


def main():
    """测试文档解析"""
    parser = DocumentParser()
    
    # 测试解析
    test_str = "# 测试文档\n\n这是一个测试文档的内容。\n\n## 第一节\n\n这里是第一部分的内容。"
    test_content = test_str.encode("utf-8")
    doc_data = parser.parse_file(test_content, "test.md", "test_user")
    
    print(f"文档ID: {doc_data['id']}")
    print(f"标题: {doc_data['title']}")
    print(f"内容长度: {doc_data['metadata']['char_count']}")


if __name__ == "__main__":
    main()