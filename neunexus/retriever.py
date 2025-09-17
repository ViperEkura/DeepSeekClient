import re
import numpy as np
from typing import Dict, List, Union
import requests


class Retriever:
    def __init__(self, api_key: str, model_name: str = "text-embedding-v1"):
        """初始化检索器"""
        self.api_key = api_key
        self.model_name = model_name
        self.api_url = "https://dashscope.aliyuncs.com/api/v1/services/embeddings/text-embedding/embedding"
        self.docs: Dict[str, np.ndarray] = {}
        
    def encode(self, sentences: Union[str, List[str]]) -> np.ndarray:
        """使用阿里云API将文本转换为嵌入向量"""
        
        if isinstance(sentences, str):
            sentences = [sentences]
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model_name,
            "input": {
                "texts": sentences
            }
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            
            if "output" in result and "embeddings" in result["output"]:
                embeddings = [np.array(embedding["embedding"]) for embedding in result["output"]["embeddings"]]
                return np.array(embeddings)
            else:
                raise Exception(f"API响应格式错误: {result}")
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"API请求失败: {e}")
        except Exception as e:
            raise Exception(f"处理嵌入时出错: {e}")
    
    def cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """计算两个向量的余弦相似度"""

        if vec1.ndim > 1:
            vec1 = vec1.flatten()
        if vec2.ndim > 1:
            vec2 = vec2.flatten()
            
        dot_product = np.dot(vec1, vec2)
        norm_vec1 = np.linalg.norm(vec1)
        norm_vec2 = np.linalg.norm(vec2)
        
        if norm_vec1 == 0 or norm_vec2 == 0:
            return 0.0
            
        return dot_product / (norm_vec1 * norm_vec2)
    
    def chunk(self, text: str, threshold: float = 0.5) -> List[List[str]]:
        """将文本分块，基于语义相似度"""
        delimiters: str = r"[。！？.!?\n]+"
        sentences = [s.strip() for s in re.split(delimiters, text) if s.strip()]
        if not sentences:
            return []
        
        embeddings = self.encode(sentences)
        
        chunks = []
        current_chunk = [sentences[0]]
        current_embeddings = [embeddings[0]]
        
        for i in range(1, len(sentences)):
            # 计算当前块的平均嵌入与当前句子的相似度
            current_mean_embedding = np.mean(current_embeddings, axis=0)
            similarity = self.cosine_similarity(current_mean_embedding, embeddings[i])
            
            if similarity >= threshold:
                current_chunk.append(sentences[i])
                current_embeddings.append(embeddings[i])
            else:
                chunks.append(current_chunk)
                current_chunk = [sentences[i]]
                current_embeddings = [embeddings[i]]
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks


    def add_docs(self, content: Union[str, List[str]], threshold: float = 0.5):
        """添加文档到检索库"""
        
        if isinstance(content, str):
            chunks = self.chunk(content, threshold)
            for chunk in chunks:
                chunk_text = "\n".join(chunk)
                self.docs[chunk_text] = self.encode(chunk_text).flatten()
        elif isinstance(content, list):
            for text in content:
                chunks = self.chunk(text, threshold)
                for chunk in chunks:
                    chunk_text = "\n".join(chunk)
                    self.docs[chunk_text] = self.encode(chunk_text).flatten()
                    
    
    def retrieve(self, query: str, top_k: int = 5) -> List[tuple]:
        """检索最相关的文档片段并返回相似度分数"""
        
        if not self.docs:
            return []
            
        query_embedding = self.encode(query).flatten()
        doc_contents = list(self.docs.keys())
        doc_embeddings = np.array(list(self.docs.values()))
        
        similarities = []
        for doc_embedding in doc_embeddings:
            similarity = self.cosine_similarity(query_embedding, doc_embedding)
            similarities.append(similarity)
        
        similarities = np.array(similarities)
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        filtered_top_k = min(top_k, len(doc_contents))
        top_indices = top_indices[:filtered_top_k]
        
        return [(doc_contents[i], similarities[i]) for i in top_indices]


if __name__ == "__main__":

    retriever = Retriever(api_key="your_aliyun_api_key_here")

    documents = [
        "这是第一个文档的内容。包含一些相关信息。",
        "这是第二个文档的内容。包含其他相关信息。"
    ]
    retriever.add_docs(documents)
    
    # 检索
    query = "相关信息"
    results = retriever.retrieve(query, top_k=3)
    print(f"查询: '{query}'")
    print("检索结果:", results)
    
    # 检索带分数
    results_with_scores = retriever.retrieve(query, top_k=3)
    print("\n带分数的检索结果:")
    for content, score in results_with_scores:
        print(f"相似度: {score:.4f} - 内容: {content[:50]}...")