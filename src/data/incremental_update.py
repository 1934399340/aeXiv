# -*- coding: utf-8 -*-
"""
增量更新模块 - 支持ArXiv数据定时更新和用户文档清理
"""

import json
import os
from pathlib import Path
from typing import Dict, List
from datetime import datetime, timedelta

project_root = Path(__file__).parent.parent.parent


class IncrementalUpdater:
    """增量更新器"""
    
    def __init__(self):
        self.data_dir = project_root / "data"
        self.update_logs_file = self.data_dir / "update_logs.json"
        self.last_update_file = self.data_dir / "last_update.json"
        
        # 确保目录存在
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def get_last_update_time(self) -> str:
        """获取上次更新时间"""
        if self.last_update_file.exists():
            with open(self.last_update_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("last_update", "")
        return ""
    
    def set_last_update_time(self, update_time: str):
        """设置更新时间"""
        with open(self.last_update_file, "w", encoding="utf-8") as f:
            json.dump({"last_update": update_time}, f)
    
    def get_existing_paper_ids(self) -> set:
        """获取已存在的论文ID"""
        papers_file = self.data_dir / "raw" / "cs_all_papers.json"
        
        if not papers_file.exists():
            return set()
        
        with open(papers_file, "r", encoding="utf-8") as f:
            papers = json.load(f)
        
        return set(p.get("id", "") for p in papers)
    
    def update_arxiv_papers(self) -> int:
        """
        增量更新ArXiv论文
        
        Returns:
            新增论文数量
        """
        from src.data.fetch_papers import ArxivFetcher
        from configs.categories import CS_CATEGORIES
        
        print("=" * 50)
        print("  ArXiv增量更新")
        print("=" * 50)
        
        fetcher = ArxivFetcher()
        
        # 获取上次更新时间
        last_update = self.get_last_update_time()
        print(f"上次更新: {last_update or '从未更新'}")
        
        # 获取已存在的论文ID
        existing_ids = self.get_existing_paper_ids()
        print(f"已有论文: {len(existing_ids)} 篇")
        
        # 获取新论文
        all_new_papers = []
        categories = list(CS_CATEGORIES.keys())[:10]  # 取前10个分类
        
        for category in categories:
            print(f"\n获取 {category}...")
            try:
                papers = fetcher.fetch_papers_by_category(category, 100)
                # 去重
                new_papers = [p for p in papers if p.get("id") not in existing_ids]
                all_new_papers.extend(new_papers)
                print(f"  新增 {len(new_papers)} 篇")
                existing_ids.update(p.get("id", "") for p in new_papers)
            except Exception as e:
                print(f"  获取失败: {e}")
        
        # 保存新论文
        if all_new_papers:
            self._save_new_papers(all_new_papers)
            print(f"\n✅ 共新增 {len(all_new_papers)} 篇论文")
        else:
            print("\n✅ 没有新论文需要更新")
        
        # 更新时间戳
        self.set_last_update_time(datetime.now().isoformat())
        
        # 记录更新日志
        self._log_update("arxiv", "success", f"新增 {len(all_new_papers)} 篇论文")
        
        return len(all_new_papers)
    
    def _save_new_papers(self, new_papers: List[Dict]):
        """保存新论文到现有数据文件"""
        papers_file = self.data_dir / "raw" / "cs_all_papers.json"
        
        # 加载现有论文
        existing_papers = []
        if papers_file.exists():
            with open(papers_file, "r", encoding="utf-8") as f:
                existing_papers = json.load(f)
        
        # 合并新论文
        existing_papers.extend(new_papers)
        
        # 保存
        with open(papers_file, "w", encoding="utf-8") as f:
            json.dump(existing_papers, f, ensure_ascii=False)
        
        print(f"保存到: {papers_file}")
    
    def cleanup_user_documents(self) -> int:
        """清理用户文档中已删除的文件"""
        from src.utils.document_manager import DocumentManager
        
        doc_manager = DocumentManager()
        
        # 获取文档索引
        index_file = doc_manager.user_docs_dir / "docs_index.json"
        if not index_file.exists():
            return 0
        
        with open(index_file, "r", encoding="utf-8") as f:
            docs_index = json.load(f)
        
        # 检查每个文档的文件是否存在
        cleaned_count = 0
        for doc in docs_index[:]:  # 使用切片避免修改列表时出错
            user_id = doc.get("user_id", "default")
            doc_id = doc.get("id", "")
            
            user_dir = doc_manager.user_docs_dir / user_id
            file_exists = any(user_dir.glob(f"{doc_id}.*"))
            
            if not file_exists:
                # 文件不存在，从索引中移除
                docs_index.remove(doc)
                cleaned_count += 1
                print(f"清理: {doc_id}")
        
        # 保存更新后的索引
        if cleaned_count > 0:
            index_file = doc_manager.user_docs_dir / "docs_index.json"
            with open(index_file, "w", encoding="utf-8") as f:
                json.dump(docs_index, f, ensure_ascii=False, indent=2)
        
        return cleaned_count
    
    def _log_update(self, update_type: str, status: str, message: str):
        """记录更新日志"""
        logs = []
        if self.update_logs_file.exists():
            with open(self.update_logs_file, "r", encoding="utf-8") as f:
                logs = json.load(f)
        
        log_entry = {
            "update_type": update_type,
            "status": status,
            "message": message,
            "created_at": datetime.now().isoformat()
        }
        logs.append(log_entry)
        
        # 只保留最近100条日志
        logs = logs[-100:]
        
        with open(self.update_logs_file, "w", encoding="utf-8") as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
    
    def get_update_logs(self, limit: int = 10) -> List[Dict]:
        """获取更新日志"""
        if not self.update_logs_file.exists():
            return []
        
        with open(self.update_logs_file, "r", encoding="utf-8") as f:
            logs = json.load(f)
        
        return logs[-limit:]
    
    def get_update_stats(self) -> Dict:
        """获取更新统计"""
        # 论文统计
        papers_file = self.data_dir / "raw" / "cs_all_papers.json"
        paper_count = 0
        if papers_file.exists():
            with open(papers_file, "r", encoding="utf-8") as f:
                papers = json.load(f)
                paper_count = len(papers)
        
        # 文档统计
        from src.utils.document_manager import DocumentManager
        doc_manager = DocumentManager()
        docs = doc_manager.get_user_docs()
        
        return {
            "paper_count": paper_count,
            "doc_count": len(docs),
            "last_update": self.get_last_update_time(),
            "total_updates": len(self.get_update_logs())
        }


def main():
    """测试增量更新"""
    updater = IncrementalUpdater()
    
    print("更新统计:")
    stats = updater.get_update_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()