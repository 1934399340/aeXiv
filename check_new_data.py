import json

papers = json.load(open('data/raw/cs_all_papers.json', 'r', encoding='utf-8'))
print(f'加载 {len(papers)} 篇论文')
print('字段检查:')
print(f'  title: {papers[0].get("title", "N/A")[:50]}')
print(f'  primary_category: {papers[0].get("primary_category", "N/A")}')
print(f'  categories: {papers[0].get("categories", [])[:3]}')
