#!/usr/bin/env python3
"""
ArXiv论文检索系统启动脚本
"""

import os
import sys
import argparse
from pathlib import Path

def check_environment():
    """检查环境配置"""
    required_vars = ['MIMO_API_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ 缺少必要的环境变量: {', '.join(missing_vars)}")
        print("请复制 .env.example 为 .env 并填入配置")
        return False
    
    return True

def check_dependencies():
    """检查依赖包"""
    required_packages = [
        'streamlit',
        'chromadb',
        'sentence_transformers',
        'langchain',
        'openai'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ 缺少依赖包: {', '.join(missing_packages)}")
        print("请运行: pip install -r requirements.txt")
        return False
    
    return True

def run_streamlit():
    """运行Streamlit应用"""
    print("🚀 启动Streamlit应用...")
    os.system("streamlit run src/app/main.py")

def run_gradio():
    """运行Gradio应用"""
    print("🚀 启动Gradio应用...")
    os.system("python src/app/gradio_app.py")

def run_api():
    """运行API服务"""
    print("🚀 启动API服务...")
    os.system("uvicorn src.app.api:app --reload --host 0.0.0.0 --port 8000")

def main():
    parser = argparse.ArgumentParser(description='ArXiv论文检索系统')
    parser.add_argument('--mode', choices=['streamlit', 'gradio', 'api'], 
                       default='streamlit', help='运行模式')
    parser.add_argument('--check', action='store_true', 
                       help='检查环境配置')
    
    args = parser.parse_args()
    
    print("=" * 50)
    print("📚 ArXiv论文检索系统")
    print("=" * 50)
    
    # 检查环境
    if args.check:
        print("\n🔍 检查环境配置...")
        if check_environment():
            print("✅ 环境配置正确")
        else:
            print("❌ 环境配置有问题")
            return
        
        print("\n🔍 检查依赖包...")
        if check_dependencies():
            print("✅ 依赖包完整")
        else:
            print("❌ 依赖包不完整")
            return
        
        print("\n✅ 环境检查通过！")
        return
    
    # 检查环境变量
    if not check_environment():
        return
    
    # 检查依赖
    if not check_dependencies():
        return
    
    # 运行应用
    if args.mode == 'streamlit':
        run_streamlit()
    elif args.mode == 'gradio':
        run_gradio()
    elif args.mode == 'api':
        run_api()

if __name__ == "__main__":
    main()