from pydantic import BaseModel
from typing import List,Optional,Union,Any

class OpenAIEmbeddingRequest(BaseModel):
    input: Union[str,List[str]]
    model: str

class OpenAISentenceEmbedding(BaseModel):
    object: str
    index: int
    embedding: List[float]

class OpenAIUsageMetrics(BaseModel):
    prompt_tokens: int
    total_tokens: int

class OpenAIEmbeddingResponse(BaseModel):
    object: str
    data: List[OpenAISentenceEmbedding]
    model: str
    usage: OpenAIUsageMetrics

class Embeddings(BaseModel):
    vectors: List[List[float]]
    texts: List[str]