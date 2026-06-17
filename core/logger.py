import logging
from logging.handlers import RotatingFileHandler
import os
import sys

def setup_logger(module_name):
    """
    Mesin Pencatat (Blackbox) Enterprise.
    Cloud-Safe: Tidak akan membuat aplikasi crash di lingkungan Read-Only.
    """
    logger = logging.getLogger(module_name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        formatter = logging.Formatter(
            fmt="[%(asctime)s] [%(levelname)s] [%(name)s] : %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        # 1. Output ke terminal console untuk debugging (Selalu Berhasil)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # 2. Coba buat file log. Jika ditolak server Cloud, lewati tanpa error.
        try:
            log_dir = "logs"
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)

            log_file = os.path.join(log_dir, "lintas_blackbox.log")
            
            file_handler = RotatingFileHandler(
                log_file, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            # Mode degraded (Cloud): Abaikan file writing, cukup tulis ke console.
            logger.warning(f"File logging dinonaktifkan (Environment Cloud/Read-Only). Error: {e}")

    return logger
