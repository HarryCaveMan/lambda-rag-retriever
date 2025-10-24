from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer
from pydantic import BaseModel,ValidationError
from typing import List
from time import time
import logging

class Singleton(type):
    _instance = None
    def __call__(cls,*args,**kwargs):
        if not cls._instance:
            cls._instance = super(Singleton,cls).__call__(*args,**kwargs)
        return cls._instance

class EncoderService(metaclass=Singleton):
    def __init__(self,model_path: str, log_level: str = 'INFO') -> None:
        self.encoder = SentenceTransformer(model_path,trust_remote_code=True)
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        logger = logging.getLogger('service')
        logger.setLevel(log_level)
        self.logger = logger

    #Get embedding vectors for list of sentences
    def encode(self,sentences:List[str]) -> (List[float],int):
        tok_start = time()
        encoded_input = self.tokenizer(sentences,padding=True,truncation=True,return_tensors="pt")
        tok_latency = time()-tok_start        
        num_tokens = encoded_input.attention_mask.sum()
        infer_start = time()
        vecs = self.encoder.encode(sentences,convert_to_tensor=True).tolist()
        model_latency = time()-infer_start
        return vecs,num_tokens,tok_latency,model_latency