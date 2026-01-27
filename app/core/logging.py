import sys
import logging
from loguru import logger
from app.settings import settings

class InterceptHandler(logging.Handler):
    """
    Redirects standard logging messages to Loguru.
    """
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

def setup_logging():
    """
    Configures Loguru based on settings.
    """
    # Remove default handler
    logger.remove()

    # Add console sink
    logger.add(
        sys.stderr,
        level=settings.LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )

    # Add file sink
    if settings.LOG_FILE:
        logger.add(
            settings.LOG_FILE,
            level=settings.LOG_LEVEL,
            rotation="10 MB",
            retention="10 days",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
        )

    # Intercept everything from standard logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    # Intercept specific uvicorn loggers to suppress duplicates but capture relevant info
    for log_name in ["uvicorn", "uvicorn.error", "uvicorn.access", "litestar"]:
        mod_logger = logging.getLogger(log_name)
        mod_logger.handlers = [InterceptHandler()]
        mod_logger.propagate = False

    logger.info(f"Logging configured at level {settings.LOG_LEVEL}")
