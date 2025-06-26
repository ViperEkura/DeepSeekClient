import torch
import torch.nn.functional as F
from typing import Dict, List, Union
from torch import Tensor
from sentence_transformers import SentenceTransformer


class Retriever:
    def __init__(self):
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2", device=device)
        self.docs: Dict[str, Tensor] = {}
        
    def encode(self, sentences: str):
        return self.model.encode(sentences, convert_to_tensor=True)

    def chunk(self, sentences: str, threshold: float = 0.5) -> List[List[str]]:
        delimiters: str = r"[。！？.!?\n]+"
        sentences = [s.strip() for s in re.split(delimiters, sentences) if s.strip()]
        if not sentences:
            return []
        
        embeddings = self.encode(sentences)
        embeddings_tensor = torch.tensor(embeddings)
        
        chunks = []
        current_chunk = [sentences[0]]
        current_embedding = embeddings_tensor[0].unsqueeze(0) 
        
        for i in range(1, len(sentences)):
            similarity = F.cosine_similarity(
                current_embedding.mean(dim=0, keepdim=True),
                embeddings_tensor[i].unsqueeze(0)
            )
            
            if similarity.item() >= threshold:
                current_chunk.append(sentences[i])
                current_embedding = torch.cat([current_embedding, embeddings_tensor[i].unsqueeze(0)])
            else:
                chunks.append(current_chunk)
                current_chunk = [sentences[i]]
                current_embedding = embeddings_tensor[i].unsqueeze(0)
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def add_docs(self, content: Union[str, List[str]], threshold: float = 0.5):
        if isinstance(content, str):
            chunks = self.chunk(content, threshold)
            for chunk in chunks:
                chunk_text = "\n".join(chunk)
                self.docs[chunk_text] = self.encode(chunk_text)
        elif isinstance(content, list):
            for text in content:
                chunks = self.chunk(text, threshold)
                for chunk in chunks:
                    chunk_text = "\n".join(chunk)
                    self.docs[chunk_text] = self.encode(chunk_text)
    
    def retrieve(self, query: str, top_k: int = 5) -> List[str]:
        query_embedding = self.encode(query)
        doc_contents = list(self.docs.keys())
        doc_embeddings = torch.stack(list(self.docs.values()))
        filted_top_k = min(top_k, len(doc_contents))
        
        scores = F.cosine_similarity(query_embedding.unsqueeze(0), doc_embeddings)
        top_indices = torch.topk(scores, k=filted_top_k).indices.tolist()
        
        return [doc_contents[i] for i in top_indices]