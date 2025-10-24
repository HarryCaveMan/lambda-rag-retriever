from functools import cached_property
from typing import List,Dict,Union,Any, Optional
import lancedb
from lancedb.embeddings import EmbeddingFunctionConfig
from .models.db import (
    TextEmbeddingSchema,
    InitIndexFromData,
    InitIndexFromTranscript,
    SearchIndexRequest,
    TableNotSetException,
    TableNotFoundException,
    BM25_INDEX
)
from .embedding_client import text_embedding_udf

class LanceDB:
    def __init__(self,data_loc,table_name) -> None:
        self._data_loc: str
        self._table_name: Optional[str] = None

    def init_from_data(self,req: InitIndexFromData) -> None:
        tbl = self._db.create_table(
            req.table_name,
            schema=TextEmbeddingSchema
        )
        tbl.add(
            req.model_dump()['data'],
            on_bad_vectors="fill"
        )
        if req.bm25_index:
            tbl.create_fts_index(
                BM25_INDEX,
                use_tantivy=False,
                language="English",
                stem=True,
                ascii_folding=True
            )
        self._table_name = tbl

    @cached_property
    def _db(self):
        return lancedb.connect(self._data_loc)

    @cached_property
    def _table(self):
        try:
            return self._db.open_table(self._table_name)
        except FileNotFoundError:
            raise TableNotFoundException(self._table_name)

    def attach_table(self,table_name) -> None:
        self._table_name = table_name

    def search(self,req: SearchIndexRequest) -> List[TextEmbeddingSchema]:
        if self._table_name is None:
            raise TableNotSetException
        return self._table.search(req.query)\
                .limit(req.top_n)\
                .to_pydantic(TextEmbeddingSchema)

    def drop_table(self,table_name):
        try:
            self._db.drop_table(table_name)
        except FileNotFoundError:
            raise TableNotFoundException(table_name)