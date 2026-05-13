import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logger(module_name):
    """
    Mesin Pencatat (Blackbox) Enterprise.
    Otomatis merotasi file agar tidak menghabiskan memori server.
    """
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(log_dir, "lintas_blackbox.log")

    logger = logging.getLogger(module_name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        # Rotating: Maksimal 5MB per file, simpan 3 backup (Total 15MB)
        file_handler = RotatingFileHandler(
            log_file, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8'
        )
        
        formatter = logging.Formatter(
            fmt="[%(asctime)s] [%(levelname)s] [%(name)s] : %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Output ke terminal console untuk debugging
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger