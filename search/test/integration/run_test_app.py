from pathlib import Path
from sys import path as PYTHONPATH

cur_dir:Path = Path(__file__).parent.absolute()

SRC_DIR = cur_dir.parent/"src"/"python"

PYTHONPATH.append(str(SRC_DIR))
from lambda_function.service import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app,host='0.0.0.0',proxy_headers=True,port=5000)