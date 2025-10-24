ARG PY_VER=3.12
FROM public.ecr.aws/lambda/python:$PY_VER

ARG MODEL_NAME
ENV MODEL_NAME=$MODEL_NAME
ENV TRANSFORMERS_OFFLINE=1
ENV TRANSFORMERS_CACHE=/tmp/transformers_cache
ENV HF_MODULES_CACHE=/tmp/hf_modules

COPY models/${MODEL_NAME} ${LAMBDA_TASK_ROOT}/models/${MODEL_NAME}

COPY requirements.txt .

RUN mkdir -p $TRANSFORMERS_CACHE && mkdir -p $HF_MODULES_CACHE && pip install -r requirements.txt

COPY *.py ${LAMBDA_TASK_ROOT}

CMD [ "lambda_function.handler" ]