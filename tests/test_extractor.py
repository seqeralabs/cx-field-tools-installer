import os
import sys
from types import SimpleNamespace

sys.dont_write_bytecode = True

# NOTE! This part is a bit convoluted but there's a method to the madness:
# - Script executes from `/~/cx-field-tools-installer`.
# - Need to change dir into .githooks (to avoid the `.` import problem), import, then return to project root so the extractor can find tfvars.
# - Error this is solving: `ImportError: attempted relative import with no known parent package``
project_root = os.getcwd()
os.chdir(f"{project_root}/.githooks")
sys.path.append(".")
from utils.extractors import get_tfvars_as_json  # convert_tfvars_to_dictionary

# Extract tfvars just like we do with the Python validation script
os.chdir(project_root)
data_dictionary = get_tfvars_as_json()
data = SimpleNamespace(**data_dictionary)


def test_tfvars_app_name():
    assert data.app_name == "tower-dev"


def test_tfvars_app_name2():
    assert data.app_name == "tower-dev2"
