
import logging
import logging.handlers
import sys


# WARNING (June 17, 2024)
#
# Original logger configuration logic worked well for verification logic but broke when using TF `data.external` mechanism.
# (broke due to how the `data.external` mechanism reads stdout/stderr ... which log events wrote to by defaul). This was resolved
# by splitting the logger into two: one to handle verification via stdout/file, the other to handle TF external mechanism by
# buffering all log events in memory until a proper payload is returned to TF (with the buffered logs emitted afterwards).
# https://docs.python.org/3/library/logging.handlers.html
#
# Trial-and-error reworking logic finally got that working, but allowing logging.basicConfig to remain resulted in 
# double-entry log events. Not sure why and don't care to spend more time right now investigating. 
# 
# Ultimately made things more granular and less DRY, but it works so .....


formatter = logging.Formatter('%(asctime)s  %(filename)-15s:%(lineno)-4d %(levelname)-12s %(message)s')

# Validation Logger
logger = logging.getLogger('VALIDATION')
logger.setLevel(logging.DEBUG)

validation_file_handler = logging.FileHandler(filename='verify.log')
validation_stdout_handler = logging.StreamHandler(stream=sys.stdout)
validation_file_handler.setFormatter(formatter)
validation_stdout_handler.setFormatter(formatter)
logger.addHandler(validation_file_handler)
logger.addHandler(validation_stdout_handler)


# External Logger
external_logger = logging.getLogger('EXTERNAL')
external_logger.setLevel(logging.DEBUG)

data_external_file_handler = logging.FileHandler(filename="data_external.log")
data_external_memory_handler = logging.handlers.MemoryHandler(
    capacity=1024*100,
    flushLevel=logging.ERROR,
    target=data_external_file_handler,
    #target=logging.FileHandler(filename="data_external.log"),
    #flushOnClose=False,
)
data_external_file_handler.setFormatter(formatter)
external_logger.addHandler(data_external_memory_handler)




