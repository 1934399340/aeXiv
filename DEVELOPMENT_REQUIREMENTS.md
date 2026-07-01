# ArXiv论文检索系统 - 功能扩展开发需求

## 一、需求概述

在现有系统基础上，新增三个核心功能：
1. **文档上传与解析** - 支持用户上传PDF/Word/Markdown等文档
2. **自动向量化** - 上传文档自动解析、分块、向量化存储
3. **增量更新** - 支持定时更新ArXiv数据和用户文档

---

## 二、功能一：文档上传与解析

### 2.1 需求描述
用户可以上传PDF、Word、Markdown等格式的文档，系统自动解析文档内容，提取文本、标题、作者等信息。

### 2.2 功能清单

| 功能 | 优先级 | 说明 |
|------|--------|------|
| PDF解析 | P0 | 支持PDF文本提取 |
| Word解析 | P1 | 支持.docx格式 |
| Markdown解析 | P1 | 支持.md格式 |
| 纯文本解析 | P1 | 支持.txt格式 |
| 文件预览 | P2 | 上传后预览文档内容 |
| 批量上传 | P2 | 支持多文件同时上传 |

### 2.3 技术方案

#### 数据结构
```python
# 用户文档数据结构
user_document = {
    "id": "doc_xxx",           # 文档唯一ID
    "filename": "论文.pdf",    # 原始文件名
    "file_type": "pdf",        # 文件类型
    "file_size": 1024000,      # 文件大小(bytes)
    "title": "论文标题",       # 提取的标题
    "content": "全文内容...",   # 提取的文本
    "metadata": {
        "author": "作者",
        "create_time": "2024-01-01",
        "page_count": 10
    },
    "upload_time": "2024-01-01T10:00:00",
    "user_id": "user_xxx",     # 上传用户
    "status": "processed"      # 处理状态
}
```

#### 依赖库
```txt
PyPDF2>=3.0.0        # PDF解析
python-docx>=0.8.11  # Word解析
markdown>=3.5         # Markdown解析
```

#### 文件存储
```
data/
├── user_docs/
│   ├── user_001/
│   │   ├── doc_001.pdf
│   │   ├── doc_002.docx
│   │   └── ...
│   └── user_002/
│       └── ...
└── user_docs_index.json  # 文档索引
```

### 2.4 界面设计

#### 上传页面
```
┌─────────────────────────────────────────┐
│           文档上传                       │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────────────────────────┐    │
│  │     拖拽文件到此处或点击上传       │    │
│  │     支持 PDF、Word、Markdown     │    │
│  └─────────────────────────────────┘    │
│                                         │
│  已上传文档:                             │
│  ┌─────┬──────┬──────┬──────┐          │
│  │名称  │类型  │大小  │操作  │          │
│  ├─────┼──────┼──────┼──────┤          │
│  │论文1│PDF  │2.1MB│删除  │          │
│  │文档2│Word │1.5MB│删除  │          │
│  └─────┴──────┴──────┴──────┘          │
└─────────────────────────────────────────┘
```

---

## 三、功能二：自动向量化

### 3.1 需求描述
用户上传文档后，系统自动完成：
1. 文本分块（chunking）
2. 向量化（embedding）
3. 索引存储（indexing）

### 3.2 功能清单

| 功能 | 优先级 | 说明 |
|------|--------|------|
| 文本分块 | P0 | 按段落/句子分块 |
| 向量化 | P0 | 使用BGE模型 |
| 索引存储 | P0 | 存入FAISS |
| 处理状态 | P1 | 显示处理进度 |
| 批量处理 | P2 | 支持批量向量化 |

### 3.3 技术方案

#### 分块策略
```python
def chunk_document(content: str, chunk_size: int = 500, overlap: int = 50):
    """
    文档分块策略
    
    Args:
        content: 文档全文
        chunk_size: 每块最大字符数
        overlap: 块之间重叠字符数
    
    Returns:
        分块列表
    """
    chunks = []
    # 按段落分块
    paragraphs = content.split('\n\n')
    
    current_chunk = ""
    for para in paragraphs:
        if len(current_chunk) + len(para) > chunk_size:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = para
        else:
            current_chunk += "\n\n" + para if current_chunk else para
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks
```

#### 向量化流程
```python
def process_document(doc_id: str, content: str):
    """处理单个文档"""
    # 1. 分块
    chunks = chunk_document(content)
    
    # 2. 向量化
    embeddings = model.encode(chunks)
    
    # 3. 存储到FAISS
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        index.add(embedding)
        # 存储元数据
        metadata = {
            "doc_id": doc_id,
            "chunk_index": i,
            "content": chunk
        }
    
    return len(chunks)
```

#### 存储结构
```
data/
├── user_embeddings/
│   ├── user_001/
│   │   ├── index.faiss        # FAISS索引
│   │   ├── index.mapping.json # ID映射
│   │   └── chunks.json        # 文本分块
│   └── user_002/
│       └── ...
```

### 3.4 界面设计

#### 处理状态展示
```
┌─────────────────────────────────────────┐
│           文档处理状态                   │
├─────────────────────────────────────────┤
│                                         │
│  论文1.pdf                              │
│  ████████████████████ 100% 完成         │
│  分块: 15块 | 向量化: 完成 | 索引: 完成  │
│                                         │
│  文档2.docx                             │
│  ████████░░░░░░░░░░░░ 40% 处理中        │
│  分块: 8块 | 向量化: 进行中 | 索引: 等待  │
│                                         │
└─────────────────────────────────────────┘
```

---

## 四、功能三：增量更新

### 4.1 需求描述
支持两种增量更新：
1. **ArXiv数据更新** - 定期获取新论文
2. **用户文档更新** - 用户删除文档时清理向量

### 4.2 功能清单

| 功能 | 优先级 | 说明 |
|------|--------|------|
| ArXiv定时更新 | P1 | 每日获取新论文 |
| 用户文档删除 | P0 | 删除时清理向量 |
| 文档更新 | P2 | 重新上传时更新索引 |
| 更新日志 | P2 | 记录更新历史 |

### 4.3 技术方案

#### ArXiv增量更新
```python
def update_arxiv_papers():
    """增量更新ArXiv论文"""
    # 1. 获取上次更新时间
    last_update = get_last_update_time()
    
    # 2. 获取新论文
    new_papers = fetch_papers_since(last_update)
    
    # 3. 去重
    existing_ids = get_existing_paper_ids()
    new_papers = [p for p in new_papers if p["id"] not in existing_ids]
    
    # 4. 向量化并存储
    for paper in new_papers:
        embedding = encode_paper(paper)
        add_to_index(paper["id"], embedding, paper)
    
    # 5. 更新时间戳
    update_last_update_time()
    
    return len(new_papers)
```

#### 用户文档删除
```python
def delete_user_document(doc_id: str, user_id: str):
    """删除用户文档及其向量"""
    # 1. 删除文件
    file_path = get_user_doc_path(user_id, doc_id)
    os.remove(file_path)
    
    # 2. 重建FAISS索引（删除指定文档）
    rebuild_user_index(user_id, exclude_doc_id=doc_id)
    
    # 3. 更新文档索引
    remove_from_doc_index(doc_id)
    
    return True
```

#### 定时任务
```python
# 使用schedule库实现定时更新
import schedule

def setup_scheduler():
    """设置定时任务"""
    # 每日凌晨2点更新ArXiv数据
    schedule.every().day.at("02:00").do(update_arxiv_papers)
    
    # 每小时检查用户文档更新
    schedule.every().hour.do(check_user_doc_updates)
```

### 4.4 界面设计

#### 更新管理页面
```
┌─────────────────────────────────────────┐
│           数据更新管理                   │
├─────────────────────────────────────────┤
│                                         │
│  ArXiv数据状态:                          │
│  最后更新: 2024-01-01 02:00             │
│  论文总数: 24,155                        │
│  [立即更新] [查看更新日志]               │
│                                         │
│  用户文档状态:                           │
│  文档总数: 156                           │
│  索引状态: 正常                          │
│  [重建索引] [清理过期文档]              │
│                                         │
│  更新计划:                               │
│  ✓ 每日 02:00 - ArXiv增量更新           │
│  ✓ 每小时 - 用户文档检查               │
│                                         │
└─────────────────────────────────────────┘
```

---

## 五、数据库设计

### 5.1 文档表
```sql
CREATE TABLE user_documents (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_size INTEGER,
    title TEXT,
    content TEXT,
    user_id TEXT NOT NULL,
    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'pending',
    chunk_count INTEGER DEFAULT 0
);
```

### 5.2 更新日志表
```sql
CREATE TABLE update_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    update_type TEXT NOT NULL,  -- 'arxiv' 或 'user_doc'
    status TEXT NOT NULL,       -- 'success' 或 'failed'
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 六、项目结构更新

```
arxiv-rag/
├── data/
│   ├── user_docs/           # 用户上传的文档
│   ├── user_embeddings/     # 用户文档的向量索引
│   ├── user_docs_index.json # 文档索引
│   └── update_logs.json     # 更新日志
├── src/
│   ├── data/
│   │   ├── fetch_papers.py
│   │   ├── document_parser.py    # 新增：文档解析
│   │   └── incremental_update.py # 新增：增量更新
│   ├── embedding/
│   │   ├── build_index.py
│   │   └── user_index_builder.py # 新增：用户文档索引
│   ├── retrieval/
│   │   └── search.py
│   ├── utils/
│   │   ├── favorites.py
│   │   └── document_manager.py   # 新增：文档管理
│   └── app/
│       └── main.py
```

---

## 七、开发计划

### 第一阶段：文档上传（3-4天）
- [ ] 实现PDF/Word/Markdown解析
- [ ] 实现文件上传界面
- [ ] 实现文档管理界面
- [ ] 测试文档解析准确性

### 第二阶段：自动向量化（3-4天）
- [ ] 实现文档分块逻辑
- [ ] 集成向量化模块
- [ ] 实现FAISS索引存储
- [ ] 实现处理状态展示

### 第三阶段：增量更新（2-3天）
- [ ] 实现ArXiv增量更新
- [ ] 实现用户文档删除
- [ ] 实现定时任务
- [ ] 实现更新日志

### 第四阶段：测试优化（2-3天）
- [ ] 功能测试
- [ ] 性能优化
- [ ] 界面优化
- [ ] 文档编写

---

## 八、验收标准

### 8.1 功能验收
- [ ] 支持上传PDF/Word/Markdown文件
- [ ] 上传后自动解析并展示内容
- [ ] 自动向量化并存储到FAISS
- [ ] 可以基于用户文档进行检索和问答
- [ ] 删除文档时自动清理向量
- [ ] ArXiv数据可以增量更新

### 8.2 性能验收
- [ ] 10MB以内PDF解析时间 < 5秒
- [ ] 单文档向量化时间 < 30秒
- [ ] 基于用户文档检索响应时间 < 1秒

### 8.3 界面验收
- [ ] 上传界面简洁易用
- [ ] 处理状态实时显示
- [ ] 文档管理界面清晰

---

## 九、风险评估

| 风险 | 影响 | 概率 | 对策 |
|------|------|------|------|
| PDF解析失败 | 部分文件无法处理 | 中 | 使用多种解析库备选 |
| 大文件处理慢 | 用户等待时间长 | 中 | 异步处理+进度显示 |
| 向量索引损坏 | 数据丢失 | 低 | 定期备份+重建机制 |
| 内存溢出 | 系统崩溃 | 低 | 分批处理+内存监控 |