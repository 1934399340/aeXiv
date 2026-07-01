# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, 'Q:/aeXiv论文检索系统/arxiv-rag')

try:
    from configs.config import settings
    from configs.categories import CS_CATEGORIES, CATEGORY_COLORS, CATEGORY_GROUPS
    from src.utils.favorites import (
        add_favorite, remove_favorite, is_favorite, 
        load_favorites, get_favorites_by_category, get_all_categories,
        get_favorites_stats, update_favorite_category
    )
    print("Import OK")
except Exception as e:
    print(f"Import Error: {e}")
