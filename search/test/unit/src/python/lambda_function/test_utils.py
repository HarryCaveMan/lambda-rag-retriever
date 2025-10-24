from sys import path as PYTHONPATH
from typing import List

from test_constants import SRC_DIR
PYTHONPATH.append(str(SRC_DIR))

from lambda_function.utils import full_traceback_str

def test_full_traceback_str():
    try:
        raise Exception("This is a fake error")
    except Exception as e:
        tbs = full_traceback_str(e)