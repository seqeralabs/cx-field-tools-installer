# README

## Structural Behaviour Of Note

1. Any `.py` file that can be invoked directly (_rather than being imported by another Python file_) needs to include a `sys.path` hack to make sure we can import necessary libraries from parent folders (_hack source: [https://stackoverflow.com/questions/27844088/python-get-directory-two-levels-up](https://stackoverflow.com/questions/27844088/python-get-directory-two-levels-up)_):

    ```python
    import sys
    from pathlib import Path

    # 0-based; need to get up to `scripts` folder
    base_import_dir = Path(__file__).resolve().parents[2]
    if base_import_dir not in sys.path:
        sys.path.append(str(base_import_dir))
    ```

2. `__init__.py` in script root folder must include a `sys.path` hack to make sure we can import submodules.

    ```python
    import sys
    from pathlib import Path

    base_import_dir  = Path(__file__).resolve().parents[0]

    if base_import_dir not in sys.path:
        sys.path.append(str(base_import_dir))
    ```


#### Notes

1. Number of `parents[x]` used depends on how far down in tree file is.

2. IMO there's minimal opportunity to make the directly-called Python files more DRY. Importing another function to execute this code won't work, since we have the same import problem the code is supposed to solve.

3. `imp` and `importlib` modules might be way to do this but the implementation is not super clear to me.

    ```python
    
    # Example:
    import imp
    from pathlib import Path

    imp.load_source("__main__", f"{Path(__file__).resolve().parents[2]}/__init__.py")
    ```