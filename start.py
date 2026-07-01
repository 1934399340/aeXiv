# -*- coding: utf-8 -*-
"""
启动脚本 - 预加载模型后启动Streamlit
"""
import sys
import time
from pathlib import Path

# 添加项目根目录
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def preload_model():
    """预加载嵌入模型"""
    print("🔄 预加载嵌入模型...")
    start_time = time.time()
    
    try:
        from sentence_transformers import SentenceTransformer
        import numpy as np
        
        # 加载模型
        model_path = str(project_root / "data" / "models" / "bge-large-zh-v1.5")
        model = SentenceTransformer(model_path, device="cpu")
        
        # 测试编码
        test_embedding = model.encode(["test"], show_progress_bar=False)
        
        elapsed = time.time() - start_time
        print(f"✅ 模型预加载完成 ({elapsed:.1f}秒)")
        
        # 保存模型到全局变量供后续使用
        import builtins
        builtins._preloaded_model = model
        
        return True
    except Exception as e:
        print(f"❌ 模型预加载失败: {e}")
        return False

def start_streamlit():
    """启动Streamlit"""
    print("\n🚀 启动Streamlit服务...")
    import subprocess
    import os
    
    # 设置环境变量
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["STREAMLIT_SERVER_HEADLESS"] = "true"
    
    # 启动Streamlit
    cmd = [
        sys.executable, "-m", "streamlit", "run", 
        str(project_root / "src" / "app" / "main.py"),
        "--server.port", "8502",
        "--server.headless", "true"
    ]
    
    subprocess.Popen(cmd, env=env, cwd=str(project_root))

if __name__ == "__main__":
    print("=" * 50)
    print("  ArXiv论文检索系统 - 启动器")
    print("=" * 50)
    
    # 预加载模型
    preload_model()
    
    # 启动Streamlit
    start_streamlit()
    
    print("\n✅ 服务已启动!")
    print("   访问: http://localhost:8502")
    print("   按 Ctrl+C 停止服务")
