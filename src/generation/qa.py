"""
论文问答模块
"""

import sys
from pathlib import Path
from typing import List, Dict, Optional
import json

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from configs.config import settings

class PaperQA:
    """论文问答系统"""
    
    def __init__(self):
        self.mimo_api_key = settings.mimo_api_key
        self.mimo_api_base_url = settings.mimo_api_base_url
        self.llm_model = settings.llm_model
        self.llm_temperature = settings.llm_temperature
        self.llm_max_tokens = settings.llm_max_tokens
        self.llm_top_p = settings.llm_top_p
        
        # 初始化LLM客户端
        self.client = None
        
    def init_llm(self):
        """初始化LLM客户端"""
        try:
            from openai import OpenAI
            
            if self.client is None:
                print(f"🔄 初始化LLM客户端...")
                self.client = OpenAI(
                    api_key=self.mimo_api_key,
                    base_url=self.mimo_api_base_url,
                    timeout=30.0
                )
                print(f"✅ LLM客户端初始化成功")
            
        except ImportError:
            print("❌ 请安装openai: pip install openai")
            raise
        except Exception as e:
            print(f"❌ LLM客户端初始化失败: {e}")
            raise
    
    def build_context(self, papers: List[Dict]) -> str:
        """构建上下文"""
        context_parts = []
        
        for i, paper in enumerate(papers, 1):
            # 提取论文信息
            title = paper.get("metadata", {}).get("title", "未知标题")
            authors = paper.get("metadata", {}).get("authors", "未知作者")
            abstract = paper.get("content", "")
            
            # 构建上下文片段
            context_part = f"论文{i}:\n"
            context_part += f"标题: {title}\n"
            context_part += f"作者: {authors}\n"
            context_part += f"内容: {abstract}\n"
            
            context_parts.append(context_part)
        
        return "\n\n".join(context_parts)
    
    def build_prompt(self, question: str, context: str) -> str:
        """构建提示词"""
        prompt = f"""你是一个专业的论文检索助手。请根据以下检索到的论文内容回答用户的问题。

检索到的论文:
{context}

用户问题: {question}

请基于上述论文内容回答问题。如果论文中没有相关信息，请说明。回答时请:
1. 引用具体的论文内容
2. 保持客观和准确
3. 使用中文回答
4. 如果有多篇论文，请综合分析

回答:"""
        
        return prompt
    
    def generate_answer(self, question: str, papers: List[Dict]) -> str:
        """
        生成回答
        
        Args:
            question: 用户问题
            papers: 检索到的论文列表
            
        Returns:
            生成的回答
        """
        if self.client is None:
            self.init_llm()
        
        # 构建上下文
        context = self.build_context(papers)
        
        # 构建提示词
        prompt = self.build_prompt(question, context)
        
        print(f"🔄 生成回答...")
        print(f"  问题: {question}")
        print(f"  论文数量: {len(papers)}")
        
        try:
            # 调用LLM
            response = self.client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": "你是一个专业的论文检索助手，擅长根据论文内容回答问题。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.llm_temperature,
                max_tokens=self.llm_max_tokens,
                top_p=self.llm_top_p
            )
            
            # 提取回答
            answer = response.choices[0].message.content
            
            print(f"✅ 回答生成完成")
            return answer
            
        except Exception as e:
            print(f"❌ 生成回答失败: {e}")
            return f"抱歉，生成回答时出现错误: {e}"
    
    def answer_question(self, question: str, papers: List[Dict]) -> Dict:
        """
        回答问题
        
        Args:
            question: 用户问题
            papers: 检索到的论文列表
            
        Returns:
            包含回答和引用信息的字典
        """
        # 生成回答
        answer = self.generate_answer(question, papers)
        
        # 构建引用信息
        citations = []
        for i, paper in enumerate(papers, 1):
            citation = {
                "index": i,
                "id": paper.get("id", ""),
                "title": paper.get("metadata", {}).get("title", ""),
                "authors": paper.get("metadata", {}).get("authors", ""),
                "score": paper.get("score", 0)
            }
            citations.append(citation)
        
        # 构建结果
        result = {
            "question": question,
            "answer": answer,
            "citations": citations,
            "paper_count": len(papers)
        }
        
        return result
    
    def summarize_papers(self, papers: List[Dict]) -> str:
        """总结论文"""
        if self.client is None:
            self.init_llm()
        
        # 构建上下文
        context = self.build_context(papers)
        
        # 构建提示词
        prompt = f"""请总结以下论文的主要内容、方法和结论:

{context}

请提供:
1. 研究主题概述
2. 主要方法/技术
3. 关键发现/结论
4. 研究意义

总结:"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": "你是一个专业的论文总结助手。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.llm_temperature,
                max_tokens=self.llm_max_tokens,
                top_p=self.llm_top_p
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"❌ 总结失败: {e}")
            return f"总结失败: {e}"

def main():
    """主函数"""
    print("=" * 50)
    print("📚 ArXiv论文问答系统")
    print("=" * 50)
    
    # 创建问答系统
    qa = PaperQA()
    
    # 示例论文数据
    sample_papers = [
        {
            "id": "1",
            "content": "标题: Attention Is All You Need\n\n分类: cs.CL, cs.LG\n\n摘要: The dominant sequence transduction models are based on complex recurrent or convolutional neural networks... We propose a new simple network architecture, the Transformer, based solely on attention mechanisms...",
            "metadata": {
                "title": "Attention Is All You Need",
                "authors": "Ashish Vaswani, Noam Shazeer, Niki Parmar",
                "categories": "cs.CL, cs.LG"
            },
            "score": 0.95
        },
        {
            "id": "2",
            "content": "标题: BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding\n\n分类: cs.CL, cs.AI\n\n摘要: We introduce a new language representation model called BERT, which stands for Bidirectional Encoder Representations from Transformers...",
            "metadata": {
                "title": "BERT: Pre-training of Deep Bidirectional Transformers",
                "authors": "Jacob Devlin, Ming-Wei Chang, Kenton Lee",
                "categories": "cs.CL, cs.AI"
            },
            "score": 0.88
        }
    ]
    
    # 示例问题
    question = "这些论文提出了什么主要方法？"
    
    print(f"\n🎯 问题: {question}")
    print(f"📄 论文数量: {len(sample_papers)}")
    
    # 生成回答
    result = qa.answer_question(question, sample_papers)
    
    # 显示结果
    print(f"\n💡 回答:")
    print(result["answer"])
    
    print(f"\n📚 引用论文:")
    for citation in result["citations"]:
        print(f"  [{citation['index']}] {citation['title']}")
        print(f"      作者: {citation['authors']}")
        print(f"      相似度: {citation['score']:.3f}")

if __name__ == "__main__":
    main()