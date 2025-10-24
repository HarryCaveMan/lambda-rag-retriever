import traceback

def full_traceback_str(e: Exception) -> str:
    return "".join(traceback.format_exception(type(e),e,e.__traceback__))