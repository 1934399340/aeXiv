"""
批量获取全CS分类论文数据
"""

import sys
import json
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data.fetch_papers import ArxivFetcher
from configs.categories import CS_CATEGORIES


def main():
    """批量获取CS分类论文"""
    print("=" * 60)
    print("  批量获取全CS分类论文数据")
    print("=" * 60)
    
    fetcher = ArxivFetcher()
    
    # 所有CS分类
    all_categories = list(CS_CATEGORIES.keys())
    
    # 每个分类获取的数量
    papers_per_category = 1000
    
    # 总计
    total_target = len(all_categories) * papers_per_category
    
    print(f"\n目标分类: {len(all_categories)} 个")
    print(f"每类获取: {papers_per_category} 篇")
    print(f"预计总量: {total_target} 篇")
    print(f"预计耗时: 约{len(all_categories) * 30 // 60} 分钟")
    print()
    
    all_papers = []
    seen_ids = set()  # 去重
    
    for i, category in enumerate(all_categories, 1):
        cat_name = CS_CATEGORIES.get(category, category)
        print(f"\n[{i}/{len(all_categories)}] 正在获取: {category} ({cat_name})")
        
        try:
            papers = fetcher.fetch_papers_by_category(category, papers_per_category)
            
            # 去重
            new_papers = []
            for p in papers:
                if p["id"] not in seen_ids:
                    seen_ids.add(p["id"])
                    new_papers.append(p)
            
            print(f"  获取 {len(papers)} 篇，去重后新增 {len(new_papers)} 篇")
            all_papers.extend(new_papers)
            
        except Exception as e:
            print(f"  获取失败: {e}")
            continue
        
        # 每获取一个分类，检查是否需要暂停
        if i < len(all_categories):
            print(f"  暂停3秒...")
            time.sleep(3)
    
    print(f"\n{'='*60}")
    print(f"获取完成！总计: {len(all_papers)} 篇论文")
    print(f"{'='*60}")
    
    # 保存数据
    if all_papers:
        save_path = project_root / "data" / "raw" / "cs_all_papers.json"
        
        print(f"\n保存到: {save_path}")
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(all_papers, f, ensure_ascii=False, indent=2)
        
        # 统计信息
        categories_count = {}
        for p in all_papers:
            for c in p.get("categories", []):
                categories_count[c] = categories_count.get(c, 0) + 1
        
        print(f"\n分类分布:")
        for cat, count in sorted(categories_count.items(), key=lambda x: -x[1])[:10]:
            name = CS_CATEGORIES.get(cat, cat)
            print(f"  {cat:10} {name:15} {count:>5} 篇")
        
        print(f"\n文件大小: {save_path.stat().st_size / 1024 / 1024:.1f} MB")


if __name__ == "__main__":
    main()
