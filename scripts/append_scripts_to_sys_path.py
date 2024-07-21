import sys
from pathlib import Path

# https://stackoverflow.com/questions/27844088/python-get-directory-two-levels-up
# Assumes following path: .. > installer > validation > check_configuration.py
parent_dir = Path(__file__).resolve().parents[0]
sys.path.append(str(parent_dir))
