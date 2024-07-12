# Centralizes common functions which will be needed across scripts called by TF `data.external`.
import json
from typing import Any

from utils.logger import external_logger


# https://www.reddit.com/r/learnpython/comments/y02net/is_there_a_better_way_to_store_full_dictionary/
def getDVal(d : dict, listPath : list) -> Any:
    '''
    Recursively loop through a dictionary object to get to the target nested key.
    This allows us to specify a TF objecy and the exact subpath to slice from.
    Note: The path must be defined as discrete elements in a list.
    '''
    for key in listPath:
        d = d[key]
    return d


def convert_booleans_to_strings(payload: dict) -> dict: 
    '''
    TF data.external freaks out if JSON true/false values not returned as strings.
    Unfortunately, json.dumps will convert True/False to true/false, but not turn to string.
    This function fixes the json.dumps payload so it's acceptable to TF.
    '''
    for k,v in payload.items():
        external_logger.debug(f"k is {k} and v is {v}.")
        if isinstance(v, bool):
            payload[k] = "true" if v == True else "false"
    return payload


def return_tf_payload(status: str, values: dict):
    '''
    Package the payload to return to TF data.external.
    Note: Using external_logger due to the stdout/stderr problem.
    '''
    external_logger.debug(f"Payload is: {values}")

    payload = {'status': status, **values}
    payload = convert_booleans_to_strings(payload)
    print(json.dumps(payload))

    external_logger.error("Flushing.")
    exit(0)