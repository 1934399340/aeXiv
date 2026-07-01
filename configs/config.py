"""
配置管理模块
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Settings(BaseSettings):
    """应用配置"""
    
    # 应用配置
    app_name: str = "ArXiv论文检索系统"
    app_version: str = "1.0.0"
    app_description: str = "基于RAG的ArXiv论文检索问答系统"
    
    # 路径配置
    base_dir: Path = Path(__file__).parent.parent
    data_dir: Path = base_dir / "data"
    raw_data_dir: Path = data_dir / "raw"
    processed_data_dir: Path = data_dir / "processed"
    embeddings_dir: Path = data_dir / "embeddings"
    
    # ArXiv API配置
    arxiv_api_url: str = "http://export.arxiv.org/api/query"
    arxiv_api_delay: int = 3  # 请求间隔（秒）
    arxiv_max_results: int = 100  # 单次最大获取数量
    
    # 向量数据库配置
    chroma_persist_directory: str = str(embeddings_dir / "chroma")
    chroma_collection_name: str = "arxiv_papers"
    
    # 嵌入模型配置
    embedding_model: str = "BAAI/bge-large-zh-v1.5"
    embedding_device: str = "cpu"
    embedding_dimension: int = 1024
    
    # 检索配置
    retrieval_top_k: int = 10
    retrieval_similarity_threshold: float = 0.7
    
    # LLM配置
    mimo_api_key: Optional[str] = os.getenv("MIMO_API_KEY")
    mimo_api_base_url: str = "https://token-plan-cn.xiaomimimo.com/v1"
    llm_model: str = "mimo-v2.5"
    llm_temperature: float = 0.3
    llm_max_tokens: int = 1024
    llm_top_p: float = 0.9
    
    # 应用配置
    app_host: str = "0.0.0.0"
    app_port: int = 8501
    app_debug: bool = True
    
    # 日志配置
    log_level: str = "INFO"
    log_file: str = "logs/app.log"
    
    # ArXiv API Key（可选）
    arxiv_api_key: Optional[str] = None
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }
        
    def get_arxiv_search_url(self, query: str, start: int = 0, 
                            max_results: int = 10, 
                            sort_by: str = "relevance",
                            sort_order: str = "descending") -> str:
        """构建ArXiv搜索URL"""
        params = {
            "search_query": query,
            "start": start,
            "max_results": max_results,
            "sortBy": sort_by,
            "sortOrder": sort_order
        }
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.arxiv_api_url}?{query_string}"
    
    def ensure_directories(self):
        """确保所有目录存在"""
        directories = [
            self.data_dir,
            self.raw_data_dir,
            self.processed_data_dir,
            self.embeddings_dir,
            Path(self.chroma_persist_directory),
            Path(self.log_file).parent
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

# 创建全局配置实例
settings = Settings()

# 确保目录存在
settings.ensure_directories()