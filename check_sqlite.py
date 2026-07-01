import sqlite3

conn = sqlite3.connect("Q:/aeXiv论文检索系统/arxiv-rag/data/embeddings/chroma/chroma.sqlite3")
cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print(f"表: {tables}")

for table in tables:
    cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    print(f"  {table}: {count} 条记录")
