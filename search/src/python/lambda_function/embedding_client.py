import requests
import json
import logging
from pathlib import Path
from functools import cached_property
from os import environ as env
from .utils import full_traceback_str
from .models.embedding import ( 
    Embeddings,
    OpenAIEmbeddingRequest,
    OpenAISentenceEmbedding,
    OpenAIUsageMetrics,
    OpenAIEmbeddingResponse
)
from .models.api import ErrorResponse
from typing import Dict,List,Optional,Union
from pydantic import ValidationError
from lancedb.embeddings import registry,TextEmbeddingFunction,EmbeddingFunctionRegistry

LOGGER = logging.getLogger("rag-search.service")
LOG_LEVEL = env.get("LOG_LEVEL","INFO")
LOGGER.setLevel(LOG_LEVEL)

EMBEDDING_API_MODEL = env.get("EMBEDDING_API_MODEL","text-embedding-3-small")

EMBEDDING_API_KEY = EMBEDDING_API_KEY = env.get("EMBEDDING_API_KEY")
if EMBEDDING_API_KEY is None:
    with open(Path(__file__).parent/".env") as envfile:
        EMBEDDING_API_KEY = json.load(envfile)["openai_key"]

EMBEDDING_API_ENDPOINT = env.get("EMBEDDING_API_ENDPOINT","https://api.openai.com/v1/embeddings")

EMBEDDING_API_MODEL = env.get("EMBEDDING_API_MODEL","text-embedding-3-small")

MODEL_DIM = int(env.get("MODEL_DIM","1536"))

@registry.register("text-embedding")
class EmbeddingClient(TextEmbeddingFunction):
    api_endpoint: str
    api_key: str
    model: str
    dims: int

    def encode_sentences_rest(self,texts:Union[str,List[str]]) -> (Union[Embeddings,ErrorResponse],int):
        model_req = OpenAIEmbeddingRequest(
            input=texts,
            model=self.model
        )
        model_res = None
        try:
            model_res = self._client.post(
                self.api_endpoint,
                json=model_req.model_dump()
            )
            embedding_res: OpenAIEmbeddingResponse = OpenAIEmbeddingResponse.model_validate(model_res.json())
        except ValidationError as ve:
                err: str = model_res.reason
                status_code: int = model_res.status_code
                return ErrorResponse(error=err),status
        except Exception as e:
            err: str = full_traceback_str(e)
            return ErrorResponse(error=err),500
        if type(texts) == str:
            texts = [texts]
        vectors = [res.embedding for res in embedding_res.data]
        return Embeddings(vectors=vectors,texts=texts),200

    def generate_embeddings(self,texts:Union[str,List[str]]):
        result,status_code = self.encode_sentences_rest(texts)
        if status_code >= 400:
            raise Exception(result.errors)
        return result.vectors
    # Doesn't really matter in lambda but could matter elsewhere
    @cached_property
    def _ndims(self):
        return self.dims

    def ndims(self):
        return self._ndims

    @cached_property
    def _client(self):
        client = requests.Session()
        client.headers.update(
            {
                "Authorization": f"Bearer {self.api_key}",
                "content-type": "application/json"
            }
        )
        return client    

model_registry = EmbeddingFunctionRegistry.get_instance()
text_embedding_udf = model_registry.get("text-embedding").create(
    api_endpoint=EMBEDDING_API_ENDPOINT,
    api_key=EMBEDDING_API_KEY,
    model=EMBEDDING_API_MODEL,
    dims=MODEL_DIM
)