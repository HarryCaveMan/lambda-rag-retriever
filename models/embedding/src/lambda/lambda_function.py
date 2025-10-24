from os import environ as env
from time import time
from typing import Dict,Union,Any
from pydantic import ValidationError

from api import Request,Response,ErrorResponse
from service import EncoderService

LAMBDA_TASK_ROOT=env.get("LAMBDA_TASK_ROOT")
MODEL_NAME=env.get("MODEL_NAME")
MODEL_PATH=f"{LAMBDA_TASK_ROOT}/models/{MODEL_NAME}"

def handler(event: Dict[str,Any],context: Any) -> Dict[str,Union[str,int]]:
    service: EncoderService = EncoderService(MODEL_PATH)
    http_body: str = event.get("body")
    if http_body is not None:
        try: 
            req: Request = Request.model_validate_json(http_body)
        except ValidationError as e:
            response_status = 400
            errs = e.errors()
            for err in errs:
                err["loc"] = ".".join(err["loc"])
            response_json = ErrorResponse(errors=errs).model_dump_json()
            req = None
        if req is not None:
            try:
                sentence_embeddings,n_tokens,tokenization_latency,model_latency = service.encode(req.sentences)
                res_data = {
                    "crid":req.crid,
                    "sentence_embeddings":sentence_embeddings
                }
                if req.extra_stats:
                    res_data["n_tokens"] = n_tokens
                    res_data["tokenization_latency"] = tokenization_latency
                    res_data["model_latency"] = model_latency
                response_status = 200
                response_json = Response.model_validate(res_data).model_dump_json(exclude_none=True)
            except Exception as e:
                response_status = 500
                response_json = ErrorResponse(errors=["model error, view service logs"]).model_dump_json()
                service.logger.info("Model Error!",exc_info=True)
    else:
        response_status = 400
        response_json = ErrorResponse(errors=["http POST body required"]).model_dump_json()

    return {
        "headers":{"Content-type":"application/json"},
        "statusCode":response_status,
        "body":response_json
    }