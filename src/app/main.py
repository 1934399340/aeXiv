# -*- coding: utf-8 -*-
"""
ArXiv论文检索系统 - Streamlit应用（学术极简风）
"""

import streamlit as st
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 页面配置（必须第一个st命令）
st.set_page_config(
    page_title="ArXiv Search",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 延迟导入（优化启动速度）
@st.cache_resource
def get_config():
    from configs.config import settings
    from configs.categories import CS_CATEGORIES, CATEGORY_COLORS, CATEGORY_GROUPS
    return settings, CS_CATEGORIES, CATEGORY_COLORS, CATEGORY_GROUPS

@st.cache_resource
def get_document_manager():
    from src.utils.document_manager import DocumentManager
    return DocumentManager()

@st.cache_resource
def get_document_parser():
    from src.data.document_parser import DocumentParser
    return DocumentParser()

@st.cache_resource
def get_incremental_updater():
    from src.data.incremental_update import IncrementalUpdater
    return IncrementalUpdater()

@st.cache_resource
def get_favorites_module():
    from src.utils.favorites import (
        add_favorite, remove_favorite, is_favorite, 
        load_favorites, get_favorites_by_category, get_all_categories,
        get_favorites_stats, update_favorite_category
    )
    return {
        'add_favorite': add_favorite,
        'remove_favorite': remove_favorite,
        'is_favorite': is_favorite,
        'load_favorites': load_favorites,
        'get_favorites_by_category': get_favorites_by_category,
        'get_all_categories': get_all_categories,
        'get_favorites_stats': get_favorites_stats,
        'update_favorite_category': update_favorite_category
    }

# 获取配置
settings, CS_CATEGORIES, CATEGORY_COLORS, CATEGORY_GROUPS = get_config()
fav_module = get_favorites_module()

# ========== CSS ==========
st.markdown("""
<style>
[data-testid="stSidebar"]{display:none!important}
#MainMenu,footer,header{visibility:hidden}
.stDeployButton{display:none}
.block-container{padding:2rem 2.5rem!important;max-width:1200px!important}

/* 标题 */
.main-title{font-size:2.2rem;font-weight:700;color:#0f172a;margin-bottom:1rem;letter-spacing:-0.02em}
.sub-title{font-size:1.1rem;color:#64748b;margin-bottom:3rem;line-height:1.6}

/* AI徽章 */
.ai-badge{
    display:inline-flex;
    align-items:center;
    background:#1a1a1a;
    color:#fff;
    padding:0.3rem 0.8rem;
    border-radius:4px;
    font-size:0.85rem;
    font-weight:500;
    letter-spacing:0.02em;
}

/* 功能卡片 */
.feature-card{
    background:#fff;
    padding:2rem;
    border-radius:12px;
    border:1px solid #e2e8f0;
    height:220px;
    display:flex;
    flex-direction:column;
    justify-content:space-between;
    transition:all 0.3s cubic-bezier(0.4,0,0.2,1);
    box-shadow:0 1px 3px rgba(0,0,0,0.04);
}
.feature-card:hover{
    transform:translateY(-8px);
    box-shadow:0 12px 24px rgba(0,0,0,0.12);
    border-color:#1a1a1a;
}
.feature-card h3{
    font-size:1.15rem;
    font-weight:600;
    color:#0f172a;
    margin:0 0 1rem 0;
}
.feature-card p{
    color:#64748b;
    font-size:1rem;
    line-height:1.7;
    margin:0;
    flex:1;
}

/* 统计卡片 */
.stat-card{text-align:center;padding:1.5rem 1rem}
.stat-number{font-size:2rem;font-weight:700;color:#0f172a}
.stat-label{font-size:1rem;color:#64748b;margin-top:0.5rem}

/* 分类标签 */
.category-tag{
    display:inline-block;
    padding:0.25rem 0.7rem;
    border-radius:4px;
    font-size:0.85rem;
    font-weight:500;
    color:#fff;
    margin-right:0.4rem;
}

/* 论文卡片 */
.paper-card{
    background:#fff;
    border:1px solid #e2e8f0;
    border-radius:12px;
    padding:1.8rem;
    margin-bottom:1.2rem;
    transition:all 0.2s;
}
.paper-card:hover{
    box-shadow:0 4px 12px rgba(0,0,0,0.06);
}
.paper-title{font-size:1.1rem;font-weight:600;color:#0f172a;margin:0 0 0.6rem 0;line-height:1.4}
.paper-meta{font-size:0.95rem;color:#64748b;margin:0.4rem 0}
.paper-abstract{font-size:1rem;color:#475569;margin:1rem 0;line-height:1.7}

/* 按钮 */
.stButton>button{
    background:#0f172a;
    color:#fff;
    border:none;
    padding:0.6rem 1.5rem;
    border-radius:8px;
    font-size:0.95rem;
    font-weight:500;
}
.stButton>button:hover{background:#1e293b}

/* 输入框 */
.stTextInput>div>div>input{
    border:1px solid #e2e8f0;
    border-radius:8px;
    padding:0.7rem 1.2rem;
    font-size:1rem;
}
.stTextInput>div>div>input:focus{
    border-color:#2563eb;
    box-shadow:0 0 0 3px rgba(37,99,235,0.1);
}

/* 分割线 */
hr{border:none;border-top:1px solid #e2e8f0;margin:2.5rem 0!important}

/* 展开器 */
.stExpander{margin-bottom:1.2rem}

/* 表单 */
.stForm{padding:0;margin:0}

/* 文字大小统一 */
p,.stMarkdown p{font-size:1rem;line-height:1.7}
h3,.stMarkdown h3{font-size:1.2rem;margin-bottom:1rem}

/* 修复光标 */
div[data-testid="stMarkdown"] p,
div[data-testid="stMarkdown"] h1,
div[data-testid="stMarkdown"] h2,
div[data-testid="stMarkdown"] h3,
div[data-testid="stMarkdown"] li {cursor:default!important}
</style>
""", unsafe_allow_html=True)


# ========== 模型加载 ==========
if 'model_loaded' not in st.session_state:
    st.session_state.current_page = "home"
    st.session_state.model_loaded = False
    st.session_state.searcher = None
    st.session_state.search_results = []
    st.session_state.search_query = ""
    st.session_state.translated_abstracts = {}
    st.session_state.viewing_paper = None
    st.session_state.viewing_fav_id = None


def load_searcher():
    """加载检索器"""
    if st.session_state.searcher is not None:
        return st.session_state.searcher
    
    try:
        from src.retrieval.search import PaperSearcher
        searcher = PaperSearcher()
        searcher.load_model()
        searcher.load_index()
        st.session_state.searcher = searcher
        st.session_state.model_loaded = True
        return searcher
    except Exception as e:
        st.error(f"加载检索器失败: {e}")
        return None


def translate_text(text: str, text_type: str = "abstract") -> str:
    """翻译文本"""
    try:
        from openai import OpenAI
        client = OpenAI(
            api_key=settings.mimo_api_key,
            base_url=settings.mimo_api_base_url,
            timeout=60.0
        )
        
        if text_type == "title":
            prompt = f"""请将以下英文学术论文标题完整翻译为中文。
要求：
1. 逐词逐句完整翻译，不要遗漏任何内容
2. 保持学术论文的严谨风格
3. 只输出翻译结果，不要解释

原文：
{text}"""
        else:
            # 摘要可能很长，分段处理
            prompt = f"""请将以下英文学术论文摘要完整翻译为中文。
要求：
1. 逐句完整翻译，不要遗漏任何内容
2. 不要概括或省略，保持原文的完整意思
3. 保持学术论文的严谨风格
4. 只输出翻译结果，不要解释

原文：
{text[:3000]}"""
        
        response = client.chat.completions.create(
            model=settings.llm_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=4096,
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        return text


def get_category_tag_html(category: str) -> str:
    """生成分类标签HTML"""
    name = CS_CATEGORIES.get(category, category)
    color = CATEGORY_COLORS.get(category, "#64748b")
    return f'<span class="category-tag" style="background:{color}">{category}</span>'


# ========== 导航栏 ==========
def render_nav(current_page: str):
    """渲染导航栏"""
    nav_items = [
        ("首页", "home"),
        ("论文检索", "search"),
        ("AI问答", "qa"),
        ("收藏管理", "favorites"),
    ]
    
    links_html = ""
    for label, key in nav_items:
        active_class = "active" if current_page == key else ""
        links_html += f'<a class="nav-link {active_class}" href="#">{label}</a>'
    
    st.markdown(f"""
    <div class="nav-bar">
        <div class="nav-logo">ArXiv <span>Search</span></div>
        <div class="nav-links">{links_html}</div>
    </div>
    """, unsafe_allow_html=True)


# ========== 首页 ==========
def show_home_page():
    """首页"""
    st.markdown('<div class="main-title">AI驱动的学术论文检索</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">基于语义理解，精准发现24,155篇CS领域论文</div>', unsafe_allow_html=True)
    
    # 搜索框（可交互）
    with st.form("home_search"):
        col1, col2 = st.columns([5, 1])
        with col1:
            query = st.text_input(
                "搜索", 
                placeholder="输入关键词或问题，AI语义搜索...",
                label_visibility="collapsed"
            )
        with col2:
            submitted = st.form_submit_button("搜索", use_container_width=True)
    
    st.markdown("""
    <div style="margin-top:-0.5rem;margin-bottom:1rem;">
        <span class="ai-badge">AI语义搜索</span>
        <span style="font-size:0.8rem;color:#94a3b8;margin-left:0.5rem;">支持自然语言，如"attention机制的最新进展"</span>
    </div>
    """, unsafe_allow_html=True)
    
    # 如果提交搜索，跳转到检索页
    if submitted and query:
        st.session_state.search_query = query
        st.session_state.current_page = "search"
        st.rerun()
    
    # 功能卡片
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <div>
                <h3>AI语义搜索</h3>
                <p>基于深度学习的语义理解，精准匹配论文内容，支持自然语言查询</p>
            </div>
            <div class="ai-badge">BGE Embedding</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <div>
                <h3>AI论文问答</h3>
                <p>与论文对话，快速理解复杂概念，获取关键信息和核心观点</p>
            </div>
            <div class="ai-badge">LLM问答</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <div>
                <h3>AI智能翻译</h3>
                <p>一键翻译论文标题和摘要，打破语言障碍，支持中英互译</p>
            </div>
            <div class="ai-badge">实时翻译</div>
        </div>
        """, unsafe_allow_html=True)
    
    # 统计数据
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-number">24,155</div>
            <div class="stat-label">收录论文</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-number">28</div>
            <div class="stat-label">CS分类</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-number">1024</div>
            <div class="stat-label">向量维度</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-number">< 0.3s</div>
            <div class="stat-label">检索速度</div>
        </div>
        """, unsafe_allow_html=True)
    
    # 快速开始
    st.markdown("---")
    st.markdown("### 快速开始")
    st.markdown("""
    1. 在搜索框输入关键词，AI自动理解语义
    2. 点击 **AI解读** 获取论文核心观点
    3. 使用 **AI问答** 深入理解论文
    4. 点击 **收藏** 保存重要论文
    """)


# ========== 论文检索页 ==========
def show_search_page():
    """论文检索页面"""
    
    # 初始化分页状态
    if 'search_page' not in st.session_state:
        st.session_state.search_page = 1
    
    PAGE_SIZE = 10  # 每页显示10篇
    
    # 搜索框
    with st.form("search_form"):
        query = st.text_input(
            "搜索", 
            placeholder="输入关键词或问题，AI语义搜索...",
            label_visibility="collapsed"
        )
        
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            search_type = st.selectbox(
                "搜索模式",
                ["semantic", "keyword", "hybrid"],
                format_func=lambda x: {"semantic": "AI语义搜索", "keyword": "关键词搜索", "hybrid": "混合搜索"}[x],
                label_visibility="collapsed"
            )
        with col2:
            threshold = st.slider("相似度阈值", min_value=0.0, max_value=1.0, value=0.3, step=0.05)
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)
            submitted = st.form_submit_button("搜索", use_container_width=True)
    
    # 搜索提示
    st.markdown("""
    <div class="search-hint">
        <span class="ai-badge">AI搜索</span>
        试试自然语言："transformer attention机制的改进方法"
    </div>
    """, unsafe_allow_html=True)
    
    # 筛选条件
    with st.expander("筛选条件", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            selected_categories = st.multiselect(
                "选择分类",
                options=list(CS_CATEGORIES.keys()),
                default=[],
                format_func=lambda x: f"{x} - {CS_CATEGORIES.get(x, x)}"
            )
        with col2:
            max_results = st.slider("最大检索数量", min_value=50, max_value=1000, value=200, step=50)
    
    # 执行搜索
    if submitted and query:
        st.session_state.search_page = 1  # 重置到第一页
        with st.spinner("AI正在搜索..."):
            try:
                searcher = load_searcher()
                if searcher:
                    categories_filter = selected_categories if selected_categories else None
                    # 使用用户设置的最大检索数量
                    results = searcher.search(query, search_type=search_type, top_k=max_results, categories=categories_filter)
                    st.session_state.search_results = results
                    st.session_state.search_query = query
                    st.session_state.search_threshold = threshold
            except Exception as e:
                st.error(f"搜索出错: {e}")
    
    # 显示搜索结果
    results = st.session_state.search_results
    threshold = st.session_state.get('search_threshold', 0.3)
    
    if results:
        # 根据相似度阈值过滤
        filtered_results = [r for r in results if r.get('score', 0) >= threshold]
        
        st.markdown("---")
        st.markdown(f"**找到 {len(filtered_results)} 篇相关论文**（相似度 >= {threshold:.2f}）")
        
        # 分页计算
        total_pages = (len(filtered_results) + PAGE_SIZE - 1) // PAGE_SIZE
        current_page = st.session_state.search_page
        start_idx = (current_page - 1) * PAGE_SIZE
        end_idx = min(start_idx + PAGE_SIZE, len(filtered_results))
        
        # 显示当前页的论文
        for i, paper in enumerate(filtered_results[start_idx:end_idx], start_idx + 1):
            title = paper['metadata'].get('title', '无标题')
            categories = paper['metadata'].get('categories', [])
            if isinstance(categories, str):
                categories = [c.strip() for c in categories.split(",") if c.strip()]
            cats_html = "".join([get_category_tag_html(c) for c in categories[:3]])
            
            # 提取摘要
            content = paper['content']
            abstract = ""
            if "摘要:" in content:
                abstract = content.split("摘要:")[1].strip()
            elif "Abstract:" in content:
                abstract = content.split("Abstract:")[1].strip()
            else:
                abstract = content
            
            # 论文卡片
            paper_id = paper.get('id', '')
            is_fav = fav_module['is_favorite'](paper_id)
            
            with st.container():
                st.markdown(f"""
                <div class="paper-card">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                        <div style="flex:1;">
                            <div class="paper-title">{title}</div>
                            <div class="paper-meta">
                                {paper['metadata'].get('authors', '未知')[:60]}...
                            </div>
                            <div style="margin:0.4rem 0;">{cats_html}</div>
                            <div class="paper-meta">
                                相似度: <strong>{paper['score']:.3f}</strong> · 
                                {paper['metadata'].get('published', '')[:10]}
                            </div>
                        </div>
                    </div>
                    <div class="paper-abstract">{abstract[:300]}...</div>
                </div>
                """, unsafe_allow_html=True)
                
                # 操作按钮
                col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
                with col1:
                    if paper['metadata'].get('pdf_url'):
                        st.markdown(f"[下载PDF]({paper['metadata']['pdf_url']})")
                with col2:
                    if paper['metadata'].get('abs_url'):
                        st.markdown(f"[查看原文]({paper['metadata']['abs_url']})")
                with col3:
                    # 翻译按钮
                    if st.button("翻译", key=f"translate_{i}"):
                        with st.spinner("翻译中..."):
                            translated = translate_text(abstract, "abstract")
                            st.session_state.translated_abstracts[paper_id] = translated
                            st.rerun()
                with col4:
                    if st.button("AI解读", key=f"ai_{i}"):
                        st.session_state.viewing_paper = paper
                        st.session_state.current_page = "qa"
                        st.rerun()
                with col5:
                    if is_fav:
                        if st.button("取消收藏", key=f"unfav_{i}"):
                            fav_module['remove_favorite'](paper_id)
                            st.rerun()
                    else:
                        if st.button("收藏", key=f"fav_{i}"):
                            fav_module['add_favorite'](paper)
                            st.rerun()
                
                # 显示翻译结果
                translated = st.session_state.translated_abstracts.get(paper_id, "")
                if translated:
                    st.markdown("**中文摘要:**")
                    st.info(translated[:600] + "..." if len(translated) > 600 else translated)
                
                st.markdown("---")
        
        # 分页控件
        if total_pages > 1:
            st.markdown("---")
            col1, col2, col3, col4, col5 = st.columns([1, 2, 1, 2, 1])
            
            with col1:
                if current_page > 1:
                    if st.button("上一页", use_container_width=True):
                        st.session_state.search_page = current_page - 1
                        st.rerun()
            
            with col2:
                st.markdown(f"<div style='text-align:center;padding-top:0.5rem;'>**第 {current_page} / {total_pages} 页**</div>", unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"<div style='text-align:center;padding-top:0.5rem;color:#64748b;'>共 {len(filtered_results)} 篇</div>", unsafe_allow_html=True)
            
            with col4:
                # 页码选择
                page_options = list(range(1, total_pages + 1))
                selected_page = st.selectbox(
                    "跳转到",
                    page_options,
                    index=current_page - 1,
                    label_visibility="collapsed",
                    key="page_select"
                )
                if selected_page != current_page:
                    st.session_state.search_page = selected_page
                    st.rerun()
            
            with col5:
                if current_page < total_pages:
                    if st.button("下一页", use_container_width=True):
                        st.session_state.search_page = current_page + 1
                        st.rerun()
    
    elif st.session_state.search_query:
        st.warning("未找到相关论文")


# ========== AI问答页 ==========
def show_qa_page():
    """AI问答页面"""
    st.markdown('<div class="main-title">AI论文问答</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">基于小米mimo-v2.5，智能解读论文内容</div>', unsafe_allow_html=True)
    
    # 检查API配置
    api_key = settings.mimo_api_key
    api_configured = api_key and api_key != "your_mimo_api_key_here"
    if not api_configured:
        st.warning("小米mimo API未配置，请在.env文件中设置MIMO_API_KEY")
    
    # 如果有选中的论文，直接显示
    if st.session_state.viewing_paper:
        paper = st.session_state.viewing_paper
        st.markdown(f"""
        <div class="ai-feature">
            <div class="ai-feature-header">
                <span class="ai-badge">AI解读</span>
                <strong>{paper.get('title', '无标题')}</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # 搜索论文
    search_query = st.text_input("搜索论文", placeholder="输入关键词搜索论文...", label_visibility="collapsed")
    
    selected_papers = []
    if search_query:
        with st.spinner("搜索中..."):
            try:
                searcher = load_searcher()
                if searcher:
                    results = searcher.search_semantic(search_query, top_k=10)
                    if results:
                        paper_options = [f"{r['metadata'].get('title', '无标题')}" for r in results]
                        selected_indices = st.multiselect(
                            "选择要分析的论文", 
                            range(len(paper_options)),
                            format_func=lambda x: paper_options[x],
                            default=[0] if paper_options else []
                        )
                        selected_papers = [results[i] for i in selected_indices]
            except Exception as e:
                st.error(f"搜索出错: {e}")
    
    # 问题输入
    st.markdown("### 提问")
    question = st.text_area(
        "问题", 
        placeholder="例如：这篇论文的主要贡献是什么？\n例如：这个方法相比传统方法有什么优势？",
        height=100,
        label_visibility="collapsed"
    )
    
    # AI回答
    if st.button("AI分析", use_container_width=True, disabled=not api_configured):
        if not selected_papers:
            st.warning("请先选择论文")
        elif not question:
            st.warning("请输入问题")
        else:
            with st.spinner("AI正在分析..."):
                try:
                    from src.generation.qa import PaperQA
                    qa = PaperQA()
                    result = qa.answer_question(question, selected_papers)
                    
                    st.markdown("---")
                    st.markdown("### AI回答")
                    # 使用markdown显示完整回答，避免截断
                    st.markdown(result["answer"])
                    
                    st.markdown("### 参考论文")
                    for citation in result["citations"]:
                        st.markdown(f"- [{citation['title']}]")
                except Exception as e:
                    st.error(f"问答出错: {e}")


# ========== 收藏管理页 ==========
def show_favorites_page():
    """收藏管理页面"""
    st.markdown('<div class="main-title">收藏管理</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">管理收藏的论文，支持分类和在线浏览</div>', unsafe_allow_html=True)
    
    # 初始化查看详情状态
    if 'viewing_fav_id' not in st.session_state:
        st.session_state.viewing_fav_id = None
    
    stats = fav_module['get_favorites_stats']()
    all_categories = ["全部"] + fav_module['get_all_categories']()
    
    col1, col2 = st.columns([3, 1])
    with col1:
        selected_category = st.selectbox(
            "选择分类",
            all_categories,
            label_visibility="collapsed"
        )
    with col2:
        new_category = st.text_input("新建分类", placeholder="分类名称", label_visibility="collapsed")
        if st.button("添加", use_container_width=True) and new_category:
            if new_category not in all_categories:
                all_categories.append(new_category)
                st.success(f"已添加分类: {new_category}")
                st.rerun()
    
    st.markdown(f"**共 {stats['total']} 篇收藏**")
    st.markdown("---")
    
    favorites = fav_module['get_favorites_by_category'](selected_category)
    
    if not favorites:
        st.info("暂无收藏论文")
        return
    
    # 查看详情模式
    if st.session_state.viewing_fav_id:
        for fav in favorites:
            if fav.get('id') == st.session_state.viewing_fav_id:
                st.markdown("### 论文详情")
                st.markdown(f"**标题**: {fav.get('title', '无标题')}")
                st.markdown(f"**作者**: {fav.get('authors', '未知')}")
                st.markdown(f"**分类**: {', '.join(fav.get('categories', []))}")
                st.markdown(f"**发布时间**: {fav.get('published', '未知')[:10]}")
                st.markdown(f"**收藏分类**: {fav.get('category', '未分类')}")
                
                if fav.get('pdf_url'):
                    st.markdown("---")
                    st.markdown("### PDF预览")
                    pdf_url = fav['pdf_url']
                    viewer_url = f"https://mozilla.github.io/pdf.js/web/viewer.html?file={pdf_url}"
                    st.markdown(f"[在新窗口打开PDF]({pdf_url})")
                    st.markdown(f"""
                    <div style="width:100%;height:500px;border:1px solid #e2e8f0;border-radius:8px;overflow:hidden;">
                        <iframe src="{viewer_url}" width="100%" height="100%" frameborder="0"></iframe>
                    </div>
                    """, unsafe_allow_html=True)
                
                if st.button("返回列表"):
                    st.session_state.viewing_fav_id = None
                    st.rerun()
                break
        return
    
    # 卡片列表
    for i, fav in enumerate(favorites):
        with st.container():
            st.markdown(f"""
            <div class="paper-card">
                <div class="paper-title">{fav.get('title', '无标题')[:80]}</div>
                <div class="paper-meta">{fav.get('authors', '未知')[:50]}...</div>
                <div class="paper-meta">分类: {', '.join(fav.get('categories', [])[:3])} · 收藏分类: {fav.get('category', '未分类')}</div>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if fav.get('pdf_url'):
                    st.markdown(f"[下载PDF]({fav['pdf_url']})")
            with col2:
                if st.button("查看详情", key=f"view_{i}"):
                    st.session_state.viewing_fav_id = fav.get('id')
                    st.rerun()
            with col3:
                if st.button("取消收藏", key=f"remove_{i}"):
                    fav_module['remove_favorite'](fav.get('id'))
                    st.rerun()
            
            st.markdown("---")


# ========== 文档上传页 ==========
def show_documents_page():
    """文档管理页面"""
    st.markdown('<div class="main-title">文档管理</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">上传文档，自动向量化，支持智能检索</div>', unsafe_allow_html=True)
    
    doc_manager = get_document_manager()
    doc_parser = get_document_parser()
    
    # 上传区域
    st.markdown("### 上传文档")
    st.markdown('<div class="ai-badge" style="margin-bottom:1rem;">支持 PDF、Word、Markdown、TXT</div>', unsafe_allow_html=True)
    
    uploaded_files = st.file_uploader(
        "选择文件",
        type=["pdf", "docx", "md", "txt"],
        accept_multiple_files=True,
        label_visibility="collapsed"
    )
    
    if uploaded_files:
        # 处理上传的文件
        processed_count = 0
        for uploaded_file in uploaded_files:
            with st.spinner(f"正在处理 {uploaded_file.name}..."):
                try:
                    file_content = uploaded_file.read()
                    doc_data = doc_parser.parse_file(file_content, uploaded_file.name)
                    processed_count += 1
                    st.success(f"✅ {uploaded_file.name} 解析完成")
                except Exception as e:
                    st.error(f"❌ {uploaded_file.name} 处理失败: {e}")
        
        # 自动向量化
        if processed_count > 0:
            st.markdown("---")
            with st.spinner("正在向量化文档..."):
                try:
                    doc_manager.rebuild_user_index("default")
                    st.success(f"✅ 向量化完成！共处理 {processed_count} 个文档")
                except Exception as e:
                    st.error(f"向量化失败: {e}")
    
    st.markdown("---")
    
    # 文档列表
    st.markdown("### 已上传文档")
    docs = doc_manager.get_user_docs()
    
    if not docs:
        st.info("暂无上传文档，请上传PDF、Word或Markdown文件")
    else:
        # 统计信息
        stats = doc_manager.get_user_stats()
        st.markdown(f"**共 {stats['total_docs']} 篇文档** | **总字数: {stats['total_chars']:,}**")
        st.markdown("---")
        
        # 文档列表
        for doc in docs:
            with st.container():
                col1, col2, col3 = st.columns([4, 2, 1])
                with col1:
                    st.markdown(f"**{doc.get('title', '无标题')}**")
                    st.caption(f"{doc.get('filename', '')} | {doc.get('file_type', '').upper()}")
                with col2:
                    st.caption(f"上传时间: {doc.get('upload_time', '')[:10]}")
                with col3:
                    if st.button("删除", key=f"del_doc_{doc.get('id')}"):
                        doc_manager.delete_document(doc.get('id'))
                        st.rerun()
                st.markdown("---")
        
        # 重建索引按钮
        if st.button("重建向量索引", use_container_width=True):
            with st.spinner("正在重建索引..."):
                doc_manager.rebuild_user_index("default")
                st.success("索引重建完成！")


# ========== 数据更新页 ==========
def show_updates_page():
    """数据更新页面"""
    st.markdown('<div class="main-title">数据更新</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">管理ArXiv数据和用户文档的更新</div>', unsafe_allow_html=True)
    
    updater = get_incremental_updater()
    
    # 获取统计信息
    stats = updater.get_update_stats()
    
    # 统计卡片
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("论文总数", f"{stats['paper_count']:,}")
    with col2:
        st.metric("用户文档", stats['doc_count'])
    with col3:
        st.metric("更新次数", stats['total_updates'])
    
    st.markdown("---")
    
    # ArXiv更新
    st.markdown("### ArXiv数据更新")
    st.markdown(f"**上次更新**: {stats['last_update'][:19] if stats['last_update'] else '从未更新'}")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("立即更新ArXiv数据", use_container_width=True):
            with st.spinner("正在获取新论文..."):
                try:
                    new_count = updater.update_arxiv_papers()
                    st.success(f"更新完成！新增 {new_count} 篇论文")
                    st.rerun()
                except Exception as e:
                    st.error(f"更新失败: {e}")
    
    with col2:
        if st.button("清理无效文档", use_container_width=True):
            with st.spinner("正在清理..."):
                try:
                    cleaned = updater.cleanup_user_documents()
                    st.success(f"清理完成！移除 {cleaned} 个无效记录")
                    st.rerun()
                except Exception as e:
                    st.error(f"清理失败: {e}")
    
    st.markdown("---")
    
    # 更新日志
    st.markdown("### 更新日志")
    logs = updater.get_update_logs(10)
    
    if not logs:
        st.info("暂无更新日志")
    else:
        for log in logs:
            status_icon = "✅" if log.get("status") == "success" else "❌"
            st.markdown(f"{status_icon} **{log.get('update_type', '')}** - {log.get('message', '')}")
            st.caption(f"时间: {log.get('created_at', '')[:19]}")


# ========== 系统信息页 ==========
def show_system_info():
    """系统信息页面"""
    st.markdown('<div class="main-title">系统信息</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("论文数量", "24,155")
    with col2:
        st.metric("CS分类", "28个")
    with col3:
        st.metric("检索速度", "< 0.3秒")
    
    st.markdown("---")
    st.markdown("### AI技术栈")
    st.markdown("""
    | 功能 | 技术 | 说明 |
    |------|------|------|
    | 语义搜索 | BGE-large-zh-v1.5 | 中文语义理解 |
    | 向量索引 | FAISS | 高效相似度检索 |
    | 论文问答 | mimo-v2.5 | 小米大语言模型 |
    | 智能翻译 | mimo-v2.5 | 实时学术翻译 |
    """)
    
    st.markdown("---")
    st.markdown("### CS分类")
    for group_name, categories in CATEGORY_GROUPS.items():
        with st.expander(group_name, expanded=False):
            cols = st.columns(3)
            for i, cat in enumerate(categories):
                with cols[i % 3]:
                    st.markdown(f"**{cat}** - {CS_CATEGORIES.get(cat, cat)}")


# ========== 导航栏 ==========
nav_items = [
    ("首页", "home"),
    ("论文检索", "search"),
    ("AI问答", "qa"),
    ("文档管理", "documents"),
    ("数据更新", "updates"),
    ("收藏管理", "favorites"),
    ("系统", "system")
]

# 8列：1列标题 + 7列导航
nav_cols = st.columns([1.5, 1, 1, 1, 1, 1, 1, 1])

with nav_cols[0]:
    st.markdown("**ArXiv Search**")

for i, (label, page_key) in enumerate(nav_items):
    with nav_cols[i + 1]:
        is_active = st.session_state.current_page == page_key
        if st.button(
            label, 
            key=f"nav_{page_key}", 
            use_container_width=True,
            type="primary" if is_active else "secondary"
        ):
            st.session_state.current_page = page_key
            st.rerun()

st.markdown("---")

# 页面路由
if st.session_state.current_page == "home":
    show_home_page()
elif st.session_state.current_page == "search":
    show_search_page()
elif st.session_state.current_page == "qa":
    show_qa_page()
elif st.session_state.current_page == "documents":
    show_documents_page()
elif st.session_state.current_page == "updates":
    show_updates_page()
elif st.session_state.current_page == "favorites":
    show_favorites_page()
elif st.session_state.current_page == "system":
    show_system_info()
