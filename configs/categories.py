"""
ArXiv CS子分类配置
"""

# CS子分类映射：英文代码 -> 中文名称
CS_CATEGORIES = {
    # 核心AI领域
    "cs.AI": "人工智能",
    "cs.CL": "计算与语言",
    "cs.CV": "计算机视觉",
    "cs.LG": "机器学习",
    "cs.NE": "神经与进化计算",
    "cs.MA": "多智能体系统",

    # 系统与工程
    "cs.SE": "软件工程",
    "cs.OS": "操作系统",
    "cs.DC": "分布式计算",
    "cs.NI": "网络与互联网架构",
    "cs.AR": "硬件架构",
    "cs.DC": "分布式计算",
    "cs.PF": "性能",

    # 数据与算法
    "cs.DB": "数据库",
    "cs.DS": "数据结构与算法",
    "cs.CG": "计算几何",
    "cs.IR": "信息检索",
    "cs.AI": "人工智能",

    # 应用领域
    "cs.RO": "机器人学",
    "cs.HC": "人机交互",
    "cs.MM": "多媒体",
    "cs.GR": "图形学",
    "cs.SD": "声音",
    "cs.MM": "多媒体",

    # 安全与密码
    "cs.CR": "密码学与安全",

    # 理论计算机科学
    "cs.FL": "形式语言与自动机",
    "cs.SC": "符号计算",
    "cs.GL": "一般文学",
    "cs.CC": "计算复杂性",

    # 跨学科
    "cs.CY": "计算与社会",
    "cs.ET": "新兴技术",
    "cs.SI": "社交与信息网络",
    "cs.AI": "人工智能",
}

# 分类分组（用于前端展示）
CATEGORY_GROUPS = {
    "AI核心": ["cs.AI", "cs.CL", "cs.CV", "cs.LG", "cs.NE", "cs.MA"],
    "系统工程": ["cs.SE", "cs.OS", "cs.DC", "cs.NI", "cs.AR", "cs.PF"],
    "数据算法": ["cs.DB", "cs.DS", "cs.CG", "cs.IR"],
    "应用领域": ["cs.RO", "cs.HC", "cs.MM", "cs.GR", "cs.SD"],
    "安全与理论": ["cs.CR", "cs.FL", "cs.SC", "cs.CC", "cs.GL"],
    "跨学科": ["cs.CY", "cs.ET", "cs.SI"],
}

# 分类颜色（黑白灰主题）
CATEGORY_COLORS = {
    "cs.AI": "#1a1a1a",  # 深黑
    "cs.CL": "#333333",  # 黑色
    "cs.CV": "#4a4a4a",  # 深灰
    "cs.LG": "#5c5c5c",  # 灰色
    "cs.RO": "#6b6b6b",  # 中灰
    "cs.IR": "#7a7a7a",  # 中灰
    "cs.SE": "#8a8a8a",  # 浅灰
    "cs.NE": "#9a9a9a",  # 浅灰
    "cs.CR": "#2d2d2d",  # 深黑
    "cs.DB": "#404040",  # 深灰
    "cs.HC": "#555555",  # 灰色
    "cs.MM": "#6a6a6a",  # 中灰
}

def get_category_zh(code: str) -> str:
    """获取分类的中文名称"""
    return CS_CATEGORIES.get(code, code)

def get_categories_by_group(group: str) -> list:
    """获取分组下的所有分类"""
    return CATEGORY_GROUPS.get(group, [])

def get_all_category_codes() -> list:
    """获取所有去重的分类代码"""
    return list(set(CS_CATEGORIES.keys()))

def get_category_color(code: str) -> str:
    """获取分类的颜色"""
    return CATEGORY_COLORS.get(code, "#6B7280")  # 默认灰色
