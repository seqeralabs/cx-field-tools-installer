import logging
import sys
from logging import handlers
from pathlib import Path

# Assumes structure: .. > scripts > installer > utils > logger.py; with logs folder peer to installer
top_dir = Path(__file__).resolve().parents[2]
log_path = Path(f"{top_dir}/logs/logger.log")

# Channge to RotatingFilehandler to not have infinite growth.
# file_handler = logging.FileHandler(filename=log_path)
file_handler = handlers.RotatingFileHandler(
    filename=log_path,
    mode="a",
    maxBytes=5 * 1024,  # 5 * 1024 * 1024,
    backupCount=1,
    encoding=None,
    delay=False,
)
stdout_handler = logging.StreamHandler(stream=sys.stdout)
handlers = [file_handler, stdout_handler]

logging.basicConfig(
    level=logging.INFO,
    # format='[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s',
    # https://stackoverflow.com/questions/57925917/python-logging-left-align-with-brackets
    format="%(asctime)s  %(filename)-15s:%(lineno)-4d %(levelname)-12s %(message)s",
    handlers=handlers,
)

logger = logging.getLogger("LOGGER_NAME")
