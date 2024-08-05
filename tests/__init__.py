import sys
from pathlib import Path

# Load `PROJECT_ROOT/scripts/` into `sys.path`
base_import_dir = Path(__file__).resolve().parents[0]

if base_import_dir not in sys.path:
    sys.path.append(str(base_import_dir))
