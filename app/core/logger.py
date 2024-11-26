import logging
import sys

logger = logging.getLogger('main-logger')
logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)


def log_request_body(request_id, body):
    logger.info('Request: %s - Body: %s', request_id, body)


def log_error(msg):
    logger.error(msg)
