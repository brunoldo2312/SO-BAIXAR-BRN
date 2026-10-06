"""brn_logger.py — Logger do no BRN."""
import os
import sys
import json
import logging
from datetime import datetime


_ROOT = None


def setup_logger(level="INFO", log_file=None):
    global _ROOT

    if _ROOT is not None:
        return _ROOT

    root = logging.getLogger()
    root.setLevel(getattr(logging, str(level).upper(), logging.INFO))

    for h in list(root.handlers):
        root.removeHandler(h)

    fmt = "%(asctime)s [%(levelname)s] %(message)s"
    dfmt = "%H:%M:%S"

    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(logging.Formatter(fmt, dfmt))
    root.addHandler(ch)

    if log_file:
        try:
            fh = logging.FileHandler(log_file, encoding="utf-8")
            fh.setFormatter(logging.Formatter(fmt, dfmt))
            root.addHandler(fh)
        except Exception as e:
            print(f"[logger] aviso: nao consegui abrir {log_file}: {e}")

    _ROOT = root
    return root


def get_logger(name="brn"):
    return logging.getLogger(name)