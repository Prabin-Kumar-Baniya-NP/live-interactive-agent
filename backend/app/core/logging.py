import logging
import sys
from datetime import datetime, timezone

from pythonjsonlogger import jsonlogger

from app.core.config import settings
from app.middleware.request_id import request_id_ctx


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)

        if not log_record.get("timestamp"):
            # Use ISO8601 with Z
            now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            log_record["timestamp"] = now

        if log_record.get("level"):
            log_record["level"] = log_record["level"].upper()
        else:
            log_record["level"] = record.levelname

        # Add Request ID
        try:
            request_id = request_id_ctx.get()
            if request_id:
                log_record["request_id"] = request_id
        except LookupError:
            pass


def setup_logging():
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO

    # JSON Handler
    json_handler = logging.StreamHandler(sys.stdout)
    formatter = CustomJsonFormatter("%(timestamp)s %(level)s %(name)s %(message)s")
    json_handler.setFormatter(formatter)

    # Root Logger
    root_logger = logging.getLogger()
    root_logger.handlers = [json_handler]
    root_logger.setLevel(log_level)

    # Uvicorn Loggers override
    # We want to replace standard uvicorn formatters with our JSON one
    for logger_name in ["uvicorn", "uvicorn.access", "uvicorn.error"]:
        logger = logging.getLogger(logger_name)
        logger.handlers = [json_handler]
        logger.propagate = False
        # Do not change level if not needed, or force it
        # logger.setLevel(log_level)
