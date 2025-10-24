from pydantic import BaseModel,Field
from typing import List,Optional,Union,Any

class SearchRequest(BaseModel):
    query: str = Field(...,description="The query to search against the index")
    top_n: int = Field(10,description="Number of results to return from EACH search performed (results will be concatenated)")
    vector: bool = Field(True,description="Whether to perform ANN vector search (default true)")
    bm25: bool = Field(True,description="Whether to perform BM25 text search (default true)")

class ErrorResponse(BaseModel):
    errors: List[Any] = Field(...,description="Catch all response for various types of internal errors")