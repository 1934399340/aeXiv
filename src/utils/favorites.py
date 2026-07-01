# -*- coding: utf-8 -*-
"""
论文收藏管理模块
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

project_root = Path(__file__).parent.parent.parent
FAVORITES_DIR = project_root / "data" / "favorites"
FAVORITES_FILE = FAVORITES_DIR / "favorites.json"
CATEGORIES_FILE = FAVORITES_DIR / "categories.json"


def ensure_dirs():
    """确保目录存在"""
    FAVORITES_DIR.mkdir(parents=True, exist_ok=True)


def load_favorites() -> List[Dict]:
    """加载收藏列表"""
    ensure_dirs()
    if FAVORITES_FILE.exists():
        with open(FAVORITES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_favorites(favorites: List[Dict]):
    """保存收藏列表"""
    ensure_dirs()
    with open(FAVORITES_FILE, 'w', encoding='utf-8') as f:
        json.dump(favorites, f, ensure_ascii=False, indent=2)


def add_favorite(paper: Dict, category: str = "未分类") -> bool:
    """添加收藏"""
    favorites = load_favorites()
    
    paper_id = paper.get('id', '')
    
    # 检查是否已收藏
    for fav in favorites:
        if fav.get('id') == paper_id:
            return False
    
    # 添加收藏
    favorite = {
        "id": paper_id,
        "title": paper.get('metadata', {}).get('title', ''),
        "authors": paper.get('metadata', {}).get('authors', ''),
        "categories": paper.get('metadata', {}).get('categories', []),
        "published": paper.get('metadata', {}).get('published', ''),
        "pdf_url": paper.get('metadata', {}).get('pdf_url', ''),
        "abs_url": paper.get('metadata', {}).get('abs_url', ''),
        "category": category,
        "added_at": datetime.now().isoformat(),
        "score": paper.get('score', 0)
    }
    
    favorites.append(favorite)
    save_favorites(favorites)
    return True


def remove_favorite(paper_id: str) -> bool:
    """取消收藏"""
    favorites = load_favorites()
    
    for i, fav in enumerate(favorites):
        if fav.get('id') == paper_id:
            favorites.pop(i)
            save_favorites(favorites)
            return True
    
    return False


def is_favorite(paper_id: str) -> bool:
    """检查是否已收藏"""
    favorites = load_favorites()
    return any(fav.get('id') == paper_id for fav in favorites)


def update_favorite_category(paper_id: str, category: str) -> bool:
    """更新收藏分类"""
    favorites = load_favorites()
    
    for fav in favorites:
        if fav.get('id') == paper_id:
            fav['category'] = category
            save_favorites(favorites)
            return True
    
    return False


def get_favorites_by_category(category: str = None) -> List[Dict]:
    """按分类获取收藏"""
    favorites = load_favorites()
    
    if category is None or category == "全部":
        return favorites
    
    return [fav for fav in favorites if fav.get('category') == category]


def get_all_categories() -> List[str]:
    """获取所有分类"""
    favorites = load_favorites()
    categories = set()
    
    for fav in favorites:
        cat = fav.get('category', '未分类')
        categories.add(cat)
    
    return sorted(list(categories))


def get_favorites_stats() -> Dict:
    """获取收藏统计"""
    favorites = load_favorites()
    categories = {}
    
    for fav in favorites:
        cat = fav.get('category', '未分类')
        categories[cat] = categories.get(cat, 0) + 1
    
    return {
        "total": len(favorites),
        "categories": categories
    }
