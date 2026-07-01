"""
简单构建索引 - 使用FAISS替代ChromaDB
"""
import json
import numpy as np
import faiss
from pathlib import Path
from sentence_transformers import SentenceTransformer

project_root = Path("Q:/aeXiv论文检索系统/arxiv-rag")

print("=" * 50)
print("  使用FAISS构建索引")
print("=" * 50)

# 加载论文
print("\n📄 加载论文...")
papers_file = project_root / "data" / "raw" / "cs_all_papers.json"
with open(papers_file, 'r', encoding='utf-8') as f:
    papers = json.load(f)
print(f"  加载 {len(papers)} 篇论文")

# 准备文本
print("\n📝 准备文本...")
texts = []
for paper in papers:
    title = paper.get("title", "")
    abstract = paper.get("abstract", "")
    categories = ", ".join(paper.get("categories", []))
    text = f"标题: {title}\n分类: {categories}\n摘要: {abstract}"
    texts.append(text)

# 加载模型
print("\n🔄 加载模型...")
model_path = str(project_root / "data" / "models" / "bge-large-zh-v1.5")
model = SentenceTransformer(model_path, device="cpu")
print("  模型加载完成")

# 向量化
print(f"\n🔄 向量化 {len(texts)} 篇论文...")
batch_size = 64
all_embeddings = []

for i in range(0, len(texts), batch_size):
    batch = texts[i:i+batch_size]
    batch_emb = model.encode(batch, show_progress_bar=True, batch_size=batch_size)
    all_embeddings.extend(batch_emb.tolist())
    if (i + batch_size) % 1000 == 0:
        print(f"  进度: {min(i+batch_size, len(texts))}/{len(texts)}")

embeddings = np.array(all_embeddings, dtype=np.float32)
print(f"✅ 向量化完成，维度: {embeddings.shape}")

# 构建FAISS索引
print("\n🔨 构建FAISS索引...")
dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(embeddings)
print(f"✅ 索引构建完成，共 {index.ntotal} 条记录")

# 保存
import os
output_dir = Path(os.path.expanduser("~")) / "arxiv_index"
output_dir.mkdir(parents=True, exist_ok=True)

index_path = str(output_dir / "arxiv.index")
faiss.write_index(index, index_path)

# 保存论文元数据
metadata_path = str(output_dir / "papers.json")
with open(metadata_path, 'w', encoding='utf-8') as f:
    json.dump(papers, f, ensure_ascii=False)

print(f"\n✅ 保存完成:")
print(f"  索引: {index_path}")
print(f"  元数据: {metadata_path}")

# 测试搜索
print("\n🔍 测试搜索...")
query = "attention mechanism transformer"
query_emb = model.encode([query])
D, I = index.search(np.array(query_emb, dtype=np.float32), 5)

print(f"\n搜索结果: {query}")
for i, idx in enumerate(I[0]):
    if idx < len(papers):
        print(f"  {i+1}. {papers[idx]['title'][:50]}... (距离: {D[0][i]:.3f})")

print("\n✅ 完成！")
