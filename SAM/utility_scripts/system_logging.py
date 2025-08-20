import logging
import sys


class ColorFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: "\033[36m",    # Cyan
        logging.INFO: "\033[97m",     # Bright White
        logging.WARNING: "\033[33m",  # Yellow
        logging.ERROR: "\033[31m",    # Red
        logging.CRITICAL: "\033[41m"  # Red background
    }
    RESET = "\033[0m"

    def format(self, record):
        log_color = self.COLORS.get(record.levelno, self.RESET)
        message = super().format(record)
        return f"{log_color}{message}{self.RESET}"


def setup_logger(name: str, level=logging.DEBUG):
    """Create or return a logger with consistent formatting across files."""
    handler = logging.StreamHandler(sys.stdout)
    formatter = ColorFormatter("%(asctime)s [%(levelname)s] %(message)s")
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding multiple handlers if setup_logger is called repeatedly
    if not logger.handlers:
        logger.addHandler(handler)
        logger.propagate = False

    return logger