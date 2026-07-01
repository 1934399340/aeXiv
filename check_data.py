import json

# 检查最新JSON数据
papers = json.load(open("data/raw/arxiv_papers_20260612_203105.json", "r", encoding="utf-8"))
print(f"共 {len(papers)} 篇论文")
print("\n前5篇标题:")
for i, p in enumerate(papers[:5]):
    print(f"  {i+1}. {p['title'][:60]}")
print(f"\n前5篇primary_category:")
for i, p in enumerate(papers[:5]):
    print(f"  {i+1}. {p.get('primary_category', 'N/A')}")
