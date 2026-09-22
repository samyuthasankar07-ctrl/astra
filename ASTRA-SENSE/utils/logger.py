import logging
from pathlib import Path
from config import LOG_DIR

def get_logger(name='astra'):
    logger=logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        fh=logging.FileHandler(Path(LOG_DIR)/'astra_sense.log', encoding='utf-8')
        fh.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s'))
        logger.addHandler(fh)
        sh=logging.StreamHandler(); sh.setFormatter(logging.Formatter('%(levelname)s: %(message)s')); logger.addHandler(sh)
    return logger
