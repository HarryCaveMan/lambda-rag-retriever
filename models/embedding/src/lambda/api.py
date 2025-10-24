from pydantic import BaseModel
from typing import List,Optional,Any

class Request(BaseModel):
    crid: Optional[Any] = None
    extra_stats: Optional[bool] = None
    sentences: List[str]

class Response(BaseModel):
    crid: Optional[Any] = None
    n_tokens: Optional[int] = None
    tokenization_latency: Optional[float] = None
    model_latency: Optional[float] = None
    sentence_embeddings: List[List[float]]

class ErrorResponse(BaseModel):
    crid: Optional[Any] = None
    errors: List[Any]