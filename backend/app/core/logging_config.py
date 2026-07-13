import logging
from logging.config import dictConfig
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parents[2] / "logs"
LOG_FILE = LOG_DIR / "backend.log"

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        },
        "uvicorn_default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(levelprefix)s %(asctime)s | %(message)s",
            "use_colors": None,
        },
        "uvicorn_access": {
            "()": "uvicorn.logging.AccessFormatter",
            "fmt": '%(levelprefix)s %(asctime)s | %(client_addr)s - "%(request_line)s" %(status_code)s',
            "use_colors": None,
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "uvicorn_default",
            "stream": "ext://sys.stderr",
        },
        "access_console": {
            "class": "logging.StreamHandler",
            "formatter": "uvicorn_access",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.FileHandler",
            "formatter": "default",
            "filename": str(LOG_FILE),
            "encoding": "utf-8",
            "mode": "a",
        },
    },
    "loggers": {
        "uvicorn": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "uvicorn.error": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "uvicorn.access": {
            "handlers": ["access_console", "file"],
            "level": "INFO",
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "INFO",
    },
}


def configure_logging() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    dictConfig(LOGGING_CONFIG)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
