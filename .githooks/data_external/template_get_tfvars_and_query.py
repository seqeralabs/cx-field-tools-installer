#!/usr/bin/env python3
import os
import json
import sys
from types import SimpleNamespace

sys.dont_write_bytecode = True


## ------------------------------------------------------------------------------------
## Extract TFvars and get query values
## ------------------------------------------------------------------------------------
# NOTE! This part is a bit convoluted but there's a method to the madness:
#   - Script executes from `~/cx-field-tools-installer`. 
#   - Change into .githooks (to avoid the `.` import problem), import, return to project root to extract tfvars.
#   - Error thrown without workaround: `ImportError: attempted relative import with no known parent package`
#   - Query object to receive objects via TF data call (i.e. resources)
project_root = os.getcwd()
os.chdir(f"{project_root}/.githooks")
sys.path.append(".")

from utils.extractors import get_tfvars_as_json #convert_tfvars_to_dictionary
from utils.logger import external_logger
from utils.common_data_external_functions import getDVal, return_tf_payload

os.chdir(project_root)
data_dictionary = get_tfvars_as_json()
data = SimpleNamespace(**data_dictionary)

# Much simpler way to get variable passed in (via Terraform sending to stdin)
query = json.load(sys.stdin)
# query = SimpleNamespace(**query)
## ------------------------------------------------------------------------------------


def populate_values(query):

    external_logger.debug(f"Query is: {query}")

    # Add logic here

    values = {
        "key": "value"
    }

    return values


if __name__ == '__main__':
    values = populate_values(query)
    return_tf_payload("0", values)

