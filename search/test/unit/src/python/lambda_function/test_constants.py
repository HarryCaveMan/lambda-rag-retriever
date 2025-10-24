from pathlib import Path

path_parts = list(Path(__file__).parent.absolute().parts)
path_parts.pop(-4)
path_parts.pop(-4)

SRC_DIR = Path(*path_parts[:-1])