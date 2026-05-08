import sys


sys.dont_write_bytecode = True

# https://stackoverflow.com/questions/3365740/how-to-import-all-submodules
import pkgutil  # noqa: E402  (deliberate ordering after sys flag)


__all__ = []
for loader, module_name, _is_pkg in pkgutil.walk_packages(__path__):
    __all__.append(module_name)
    _module = loader.find_spec(module_name)
    # _module = loader.find_module(module_name).load_module(module_name)
    globals()[module_name] = _module
