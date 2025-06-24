import sys
from pathlib import Path

# Let tests inherit ability to import code from top-level
base_import_dir = Path(__file__).resolve().parents[1]
print(f"{base_import_dir=}")
if base_import_dir not in sys.path:
    sys.path.append(str(base_import_dir))
