#!/usr/bin/env python3

import os, sys
#sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.dont_write_bytecode = True
# This suppresses the stacktrace emitted when assertion errors are thrown. Users will still see the
# human-friendly message, but not the rest of the noise. We'll need to socialize that that need to 
# search for the error message in this file to see what the offending values are.
# Longer-term we can consider externalizing errors to another file so that longer messages can be
# written and returned without cluttering up the evaluation logic.
sys.tracebacklimit = 0

import re
from types import SimpleNamespace
from typing import List

from utils.extractors import get_tfvars_as_json #convert_tfvars_to_dictionary
from utils.logger import logger
from utils.subnets import get_all_subnets


## ------------------------------------------------------------------------------------
## NOTE: See comments in utils/helpers.py for reasons why we created our own hacky tfvars parser.
## ------------------------------------------------------------------------------------


## ------------------------------------------------------------------------------------
## HELPER FUNCTIONS
## ------------------------------------------------------------------------------------


## ------------------------------------------------------------------------------------
## MAIN
## ------------------------------------------------------------------------------------
if __name__ == '__main__':

    logger.info("")
    logger.info("Beginning tfvars configuration check.")

    # Generate dictionary from tfvars then convert to SimpleNamespace for cleaner dot-notation access.
    # Kept the two objects different for convenience when .keys() method is required.
    data_dictionary = get_tfvars_as_json()
    data = SimpleNamespace(**data_dictionary)


    # Check minimum container version
    if data.flag_create_external_db and data.db_deletion_protection:
        raise AssertionError(" You have deletion protection on your RDS instance. Please update the resource to remove protection before running `terraform destroy`.")