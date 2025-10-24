import logging
from typing import List
from os import environ as env
from fastapi import FastAPI
from fastapi.exceptions import HTTPException
from mangum import Mangum
from .db_client import LanceDB
from .utils import full_traceback_str
from .models.db import (
    TextEmbeddingSchema,
    InitIndexFromData,
    SearchIndexRequest,
    TableNotSetException,
    TableNotFoundException,
    TableInitStatus,
    InitResponse,
    SearchResponse
)

DATA_S3_BUCKET = env.get("DATA_S3_BUCKET")

LOGGER = logging.getLogger("rag-search.service")
LOG_LEVEL = env.get("LOG_LEVEL","INFO")
LOGGER.setLevel(LOG_LEVEL)

app = FastAPI(
    title="rag-search",
    version="0.1.0"
)

@app.post("/init_from_data")
def init_table_from_data(init_req: InitIndexFromData) -> InitResponse:
    LOGGER.info("Init request started")
    LOGGER.debug(f"Initial path: {init_req.data_loc}")
    if DATA_S3_BUCKET is not None and len(DATA_S3_BUCKET)>0:
        init_req.data_loc = f"s3://{DATA_S3_BUCKET}/{init_req.data_loc}"
        LOGGER.debug(f"Rewrote path: {init_req.data_loc}")
    db = LanceDB(init_req.data_loc)
    try:
        db.init_from_data(init_req)
        LOGGER.debug(f"Initialized table: {init_req.table_name}")
        return InitResponse(status=TableInitStatus.SUCCESS)
    except Exception as e:
        LOGGER.error(full_traceback_str(e))
        return InitResponse(status=TableInitStatus.FAIL)
    finally:
        LOGGER.info("Init request completed")

@app.post("/search")
def search_table(search_req: SearchIndexRequest) -> SearchResponse:
    LOGGER.info("Search request received")
    LOGGER.debug(f"Initial path: {search_req.data_loc}")
    try:
        LOGGER.info("Connecting to index...")
        if DATA_S3_BUCKET is not None and len(DATA_S3_BUCKET)>0:
            search_req.data_loc = f"s3://{DATA_S3_BUCKET}/{search_req.data_loc}"
            LOGGER.debug(f"Rewrote path: {search_req.data_loc}")
        db = LanceDB(search_req.data_loc,search_req.table_name)
        LOGGER.info("Searching index...")
        results = db.search(search_req)
        LOGGER.info("Search complete!")
        return SearchResponse(results=results)
    except TableNotFoundException:
        raise HTTPException(status_code=404,detail=f"Table: {search_req.table_name} not found in DataSource: {search_req.data_loc}")
    finally:
        LOGGER.info("Search request complete!")

@app.get("/ping")
def ping() -> str:
    return "ALIVE"

handler = Mangum(app)