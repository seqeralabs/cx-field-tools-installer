import sys
from pathlib import Path

# sys.dont_write_bytecode = True


# This did not work with `parents[1]` but does work with `parents[0]`
# https://stackoverflow.com/questions/27844088/python-get-directory-two-levels-up
# Assumes following path: .. > installer > validation > check_configuration.py
parent_dir = Path(__file__).resolve().parents[0]
sys.path.append(str(parent_dir))
