import logging
import sys
import uuid
from contextvars import ContextVar

trace_id_ctx: ContextVar[str] = ContextVar("trace_id", default="")


class TraceIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.trace_id = trace_id_ctx.get() or "-"
        return True


def get_logger(name: str = "orchestrator") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.addFilter(TraceIdFilter())
        formatter = logging.Formatter(
            fmt="%(asctime)s %(levelname)s trace_id=%(trace_id)s %(name)s %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%SZ",
        )
        handler.setFormatter(formatter)
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)
    return logger


def set_trace_id(value: str | None = None) -> str:
    tid = value or str(uuid.uuid4())
    trace_id_ctx.set(tid)
    return tid


# Ensure base logger exists early
get_logger("orchestrator")
