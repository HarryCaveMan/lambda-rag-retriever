from sys import path as PYTHONPATH
from os import environ as env
from typing import List
from fastapi.exceptions import HTTPException
from copy import deepcopy

from test_constants import SRC_DIR
PYTHONPATH.append(str(SRC_DIR))


from lambda_function.db_client import LanceDB
from lambda_function.models.db import (
    TextEmbeddingSchema,
    InitIndexFromData,
    SearchIndexRequest,
    TableNotSetException,
    TableNotFoundException,
    Text
)

def test_service(s3=False):
    BASE_DATA_LOC: str = "data/test_1"
    DATA_S3_BUCKET: Optional[str] = None
    if not s3:
        env["DATA_S3_BUCKET"] = ''
        data_loc = BASE_DATA_LOC
    else:
        DATA_S3_BUCKET = env["DATA_S3_BUCKET"]
        data_loc = f"s3://{DATA_S3_BUCKET}/{BASE_DATA_LOC}"

    from lambda_function.service import init_table_from_data,search_table,ping
    init_req: InitIndexFromData = InitIndexFromData(
        data_loc=data_loc,
        table_name="test",
        bm25_index=True,
        data=[
            Text(text="hi I am Harris"),
            Text(text="the hypotenuse is the square root of the sum of the other sides squared")
        ]
    )
    search_req: SearchIndexRequest = SearchIndexRequest(
        data_loc=data_loc,
        table_name="test",
        query="what is the hypotenuse?",
        top_n=2,
        search_type="hybrid"
    )
    db = LanceDB(data_loc)
    try:
        db.drop_table(init_req.table_name)
    except TableNotFoundException:
        pass
    try:
        db.search(search_req)
    except TableNotSetException:
        pass
    print(init_req)  
    db.init_from_data(init_req)
    try:
        fake_db = LanceDB(data_loc,"faketable")
    except TableNotFoundException:
        pass
    try:
        db.drop_table("faketable")
    except TableNotFoundException:
        pass
    results: List[TextEmbeddingSchema] = db.search(search_req)
    print(f"Dropping table {init_req}")
    db.drop_table(init_req.table_name)
    ping()
    search_req.data_loc = BASE_DATA_LOC
    init_req.data_loc = BASE_DATA_LOC
    init_table_from_data(init_req)
    search_table(search_req)
    try:
        search_req.data_loc = BASE_DATA_LOC
        search_req.table_name = "faketable"
        search_table(search_req)
    except HTTPException:
        pass
    try:        
        init_req.data_loc = BASE_DATA_LOC
        init_req.table_name =" "
        init_table_from_data(init_req)
    except ValueError:
        pass