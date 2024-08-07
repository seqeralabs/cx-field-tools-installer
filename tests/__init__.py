import sys
from pathlib import Path

# Load `PROJECT_ROOT/scripts/` into `sys.path`
base_import_dir = Path(__file__).resolve().parents[0]

if base_import_dir not in sys.path:
    sys.path.append(str(base_import_dir))


# import sys

# sys.dont_write_bytecode = True

# # https://stackoverflow.com/questions/3365740/how-to-import-all-submodules
# import pkgutil

# __all__ = []
# for loader, module_name, is_pkg in pkgutil.walk_packages(__path__):
#     __all__.append(module_name)
#     _module = loader.find_spec(module_name)
#     # _module = loader.find_module(module_name).load_module(module_name)
#     globals()[module_name] = _module
