"""
翻译模块 - 使用小米mimo API进行论文标题和摘要翻译
"""

import sys
import json
import os
import time
from pathlib import Path
from typing import List, Dict, Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from configs.config import settings


class PaperTranslator:
    """论文翻译器"""
    
    def __init__(self):
        self.client = None
        self.cache_dir = project_root / "data" / "translations"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def init_client(self):
        """初始化API客户端"""
        if self.client is None:
            from openai import OpenAI
            self.client = OpenAI(
                api_key=settings.mimo_api_key,
                base_url=settings.mimo_api_base_url,
                timeout=60.0
            )
    
    def translate_batch(self, texts: List[str], text_type: str = "title", batch_size: int = 5) -> List[str]:
        """
        批量翻译文本
        
        Args:
            texts: 待翻译文本列表
            text_type: "title" 或 "abstract"
            batch_size: 每批翻译数量
            
        Returns:
            翻译后的文本列表
        """
        self.init_client()
        
        results = []
        total = len(texts)
        
        for i in range(0, total, batch_size):
            batch = texts[i:i+batch_size]
            batch_num = i // batch_size + 1
            total_batches = (total + batch_size - 1) // batch_size
            
            print(f"  翻译进度: {batch_num}/{total_batches} ({len(results)}/{total} 条)")
            
            translated = self._translate_single_batch(batch, text_type)
            results.extend(translated)
            
            # 避免API限速
            if i + batch_size < total:
                time.sleep(1)
        
        return results
    
    def _translate_single_batch(self, texts: List[str], text_type: str) -> List[str]:
        """翻译单批次文本"""
        if not texts:
            return []
        
        # 根据文本类型构建提示词
        if text_type == "title":
            prompt = self._build_title_prompt(texts)
        else:
            prompt = self._build_abstract_prompt(texts)
        
        try:
            response = self.client.chat.completions.create(
                model=settings.llm_model,
                messages=[
                    {"role": "system", "content": "你是一个专业的学术论文翻译助手，擅长将英文学术论文标题翻译为中文。翻译要求：准确、简洁、符合中文学术表达习惯。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=4096,
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # 解析翻译结果
            translated = self._parse_translation_result(result_text, len(texts))
            
            # 如果解析结果数量不匹配，逐条翻译
            if len(translated) != len(texts):
                print(f"    批量翻译结果数量不匹配，改为逐条翻译")
                translated = []
                for text in texts:
                    single = self._translate_single(text, text_type)
                    translated.append(single)
            
            return translated
            
        except Exception as e:
            print(f"    翻译失败: {e}")
            # 翻译失败时返回原文
            return texts
    
    def _build_title_prompt(self, titles: List[str]) -> str:
        """构建标题翻译提示词"""
        numbered = "\n".join([f"{i+1}. {t}" for i, t in enumerate(titles)])
        return f"""请将以下英文学术论文标题翻译为中文。要求：
1. 每行一个翻译结果
2. 保持学术风格
3. 保留编号格式
4. 准确翻译专业术语

原文：
{numbered}

请直接输出翻译结果（保持编号）："""
    
    def _build_abstract_prompt(self, abstracts: List[str]) -> str:
        """构建摘要翻译提示词"""
        separated = "\n---\n".join([f"[{i+1}] {a}" for i, a in enumerate(abstracts)])
        return f"""请将以下英文学术论文摘要翻译为中文。要求：
1. 保持学术风格和专业术语
2. 用 "---" 分隔不同摘要的翻译结果
3. 保留编号标签 [1] [2] 等
4. 翻译要准确、通顺

原文：
{separated}

请输出翻译结果（用 --- 分隔）："""
    
    def _parse_translation_result(self, text: str, expected_count: int) -> List[str]:
        """解析翻译结果"""
        # 尝试按行解析（标题翻译）
        lines = [l.strip() for l in text.strip().split("\n") if l.strip()]
        
        # 去除编号前缀
        results = []
        for line in lines:
            # 去除 "1. " "1、" "1)" 等格式
            if ". " in line[:5]:
                line = line.split(". ", 1)[1]
            elif "、" in line[:5]:
                line = line.split("、", 1)[1]
            elif ")" in line[:5]:
                line = line.split(")", 1)[1]
            results.append(line)
        
        # 如果按行解析数量不匹配，尝试按 --- 分隔（摘要翻译）
        if len(results) != expected_count:
            parts = [p.strip() for p in text.split("---") if p.strip()]
            if len(parts) == expected_count:
                results = []
                for part in parts:
                    # 去除 [1] 等标签
                    if part.startswith("["):
                        part = part.split("]", 1)[1].strip()
                    results.append(part)
        
        return results
    
    def _translate_single(self, text: str, text_type: str) -> str:
        """翻译单条文本"""
        try:
            if text_type == "title":
                prompt = f"请将以下英文学术论文标题翻译为中文，只输出翻译结果：\n\n{text}"
            else:
                prompt = f"请将以下英文学术论文摘要翻译为中文，只输出翻译结果：\n\n{text[:2000]}"
            
            response = self.client.chat.completions.create(
                model=settings.llm_model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2048,
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"    单条翻译失败: {e}")
            return text
    
    def translate_papers(self, papers: List[Dict]) -> List[Dict]:
        """
        翻译论文列表（标题和摘要）
        
        Args:
            papers: 论文列表
            
        Returns:
            添加了中文字段的论文列表
        """
        print(f"\n开始翻译 {len(papers)} 篇论文...")
        
        # 检查缓存
        cache_file = self.cache_dir / "translations.json"
        cached = self._load_cache(cache_file)
        
        # 筛选需要翻译的论文
        to_translate = []
        for paper in papers:
            paper_id = paper.get("id", "")
            if paper_id not in cached:
                to_translate.append(paper)
        
        if not to_translate:
            print("所有论文已有翻译缓存，跳过翻译")
        else:
            print(f"需要翻译 {len(to_translate)} 篇（已有缓存 {len(papers) - len(to_translate)} 篇）")
            
            # 提取标题和摘要
            titles = [p.get("title", "") for p in to_translate]
            abstracts = [p.get("abstract", "") for p in to_translate]
            
            # 批量翻译标题
            print("\n翻译标题...")
            titles_zh = self.translate_batch(titles, text_type="title", batch_size=5)
            
            # 批量翻译摘要
            print("\n翻译摘要...")
            abstracts_zh = self.translate_batch(abstracts, text_type="abstract", batch_size=3)
            
            # 更新缓存
            for i, paper in enumerate(to_translate):
                paper_id = paper.get("id", "")
                cached[paper_id] = {
                    "title_zh": titles_zh[i] if i < len(titles_zh) else paper.get("title", ""),
                    "abstract_zh": abstracts_zh[i] if i < len(abstracts_zh) else paper.get("abstract", "")
                }
            
            # 保存缓存
            self._save_cache(cache_file, cached)
            print(f"\n翻译完成，已缓存 {len(cached)} 篇")
        
        # 为所有论文添加中文字段
        for paper in papers:
            paper_id = paper.get("id", "")
            if paper_id in cached:
                paper["title_zh"] = cached[paper_id].get("title_zh", paper.get("title", ""))
                paper["abstract_zh"] = cached[paper_id].get("abstract_zh", paper.get("abstract", ""))
            else:
                paper["title_zh"] = paper.get("title", "")
                paper["abstract_zh"] = paper.get("abstract", "")
        
        return papers
    
    def _load_cache(self, cache_file: Path) -> Dict:
        """加载翻译缓存"""
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_cache(self, cache_file: Path, cache: Dict):
        """保存翻译缓存"""
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存缓存失败: {e}")


def main():
    """测试翻译模块"""
    translator = PaperTranslator()
    
    # 测试单条翻译
    test_title = "Attention Is All You Need"
    print(f"原文: {test_title}")
    
    translator.init_client()
    result = translator._translate_single(test_title, "title")
    print(f"译文: {result}")


if __name__ == "__main__":
    main()
