from pydantic import BaseModel,Field
from lancedb.pydantic import LanceModel,Vector
from lancedb.embeddings import get_registry
from typing import List,Optional,Union,Any
from enum import Enum

from ..embedding_client import text_embedding_udf as func
class TextEmbeddingSchema(LanceModel):
    vector: Vector(func.ndims()) = func.VectorField()
    text: str = func.SourceField()

BM25_INDEX = "text"

class TableInitStatus(str,Enum):
    SUCCESS="SUCCESS"
    FAIL="FAIL"

class InitResponse(BaseModel):
    status: TableInitStatus

class Text(BaseModel):
    text: str = Field(...,description="The text data to be added to the index")

class InitIndexFromData(BaseModel):
    data: List[Text] = Field(...,description="The data as a list of Test object")
    data_loc: str = Field(...,description="The data location to cconnect to")
    table_name: str = Field(...,description="The table containing the search indexes")
    bm25_index: Optional[bool] = Field(...,description="Whether or not to do a full-text-search (BM25) index")

class InitIndexFromTranscript(BaseModel):
    bm25: bool = True

class SearchIndexRequest(BaseModel):
    data_loc: str = Field(...,description="The data location to cconnect to")
    table_name: str = Field(...,description="The table containing the search indexes")
    query: str
    top_n: int = 10
    search_type: str
    
class SearchResponse(BaseModel):
    results: List[TextEmbeddingSchema] = Field(...,description="The search results. List of {\"vector\":List[float],\"text\":str}")

# Just Exceptions with descriptive names and messages...

TABLE_NOT_SET_MESSAGE=\
"""
No table set, either:
  - init a table from data
  - connect to an existing table with attach_table(table_name)
BEFORE performing a search        
"""

TABLE_NOT_FOUND_MESSAGE=\
"""
Table $$TABLE$$ not found in this data source, either 
  - create table 
  - connect to correct data source
  - do nothing (if this is a drop_table)
"""

class TableNotSetException(Exception):
    message = TABLE_NOT_SET_MESSAGE
    def __init__(self):
        super().__init__(self.message)

class TableNotFoundException(Exception):
    message = TABLE_NOT_FOUND_MESSAGE
    def __init__(self, table_name: str):
        super().__init__(self.message.replace("$$TABLE$$",table_name))