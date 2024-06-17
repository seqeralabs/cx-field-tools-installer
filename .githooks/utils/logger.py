
import logging
import sys

file_handler = logging.FileHandler(filename='tmp.log')
stdout_handler = logging.StreamHandler(stream=sys.stdout)
handlers = [file_handler, stdout_handler]

logging.basicConfig(
    level=logging.DEBUG, 
    # format='[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s',
    # https://stackoverflow.com/questions/57925917/python-logging-left-align-with-brackets
    format='%(asctime)s  %(filename)-15s:%(lineno)-4d %(levelname)-12s %(message)s',
    handlers=handlers
)

logger = logging.getLogger('LOGGER_NAME')