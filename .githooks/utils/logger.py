
import logging
import logging.handlers
import sys

validation_file_handler = logging.FileHandler(filename='verify.log')
validation_stdout_handler = logging.StreamHandler(stream=sys.stdout)

data_external_file_handler = logging.FileHandler(filename="data_external.log")
data_external_memory_handler = logging.handlers.MemoryHandler(
    capacity=1024*100,
    flushLevel=logging.ERROR,
    target=data_external_file_handler,
    #target=logging.FileHandler(filename="data_external.log"),
    #flushOnClose=False,
)

# WARNING!! 
# `handler[...]` population here works for `make verify` but breaks TF `data.external`
# I have removed and attach formatting one-by-one. It's stupid, but it works.
# handlers = [validation_file_handler, validation_stdout_handler]  # DONT UNCOMMENT
logging.basicConfig(
    level=logging.DEBUG, 
    # https://stackoverflow.com/questions/57925917/python-logging-left-align-with-brackets
    format='%(asctime)s  %(filename)-15s:%(lineno)-4d %(levelname)-12s %(message)s',
    # handlers=handlers  # DONT UNCOMMENT
)


# https://docs.python.org/3/library/logging.handlers.html
# MemoryHandler is needed due to how data flows to/from TF `data.external`. Using 2 loggers to keep 
# better isolation between tfvars verification logic and content-generating scripts.

logger = logging.getLogger('VALIDATION')
logger.addHandler(validation_file_handler)
logger.addHandler(validation_stdout_handler)

external_logger = logging.getLogger('EXTERNAL')
external_logger.addHandler(data_external_memory_handler)

# data_external_memory_handler.setFormatter(formatter)  # No timestamp. Dunno why.
formatter = logging.Formatter('%(asctime)s  %(filename)-15s:%(lineno)-4d %(levelname)-12s %(message)s')
validation_file_handler.setFormatter(formatter)
validation_stdout_handler.setFormatter(formatter)
data_external_file_handler.setFormatter(formatter)

