from datetime import datetime
import logging
import os
from pathlib import Path
import sys

# ───────────────────────────────────────────────────────────────────────
# LOGGER (SIMPLE FILE+CONSOLE LOGGER)
# ───────────────────────────────────────────────────────────────────────

def setup_logger(log_dir: Path, logger_name: str = "backup_cli") -> logging.Logger:
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
    logfile = log_dir / f"{timestamp}.log"

    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)

    if logger.hasHandlers():
        return logger

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s [%(filename)s:%(lineno)d]: %(message)s",
        datefmt="%d-%m-%Y %H:%M:%S"
    )

    fh = logging.FileHandler(logfile, encoding="utf-8")
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger