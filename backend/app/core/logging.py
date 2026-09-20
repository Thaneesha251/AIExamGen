import logging
import sys
try:
    from app.core.config import settings
except ImportError:
    from backend.app.core.config import settings

def setup_logging():
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Silence noisy default loggers if needed
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    
    logger = logging.getLogger("aiexamgen")
    logger.info(f"Initialized application logger for {settings.APP_NAME} ({settings.APP_ENV})")
    return logger

logger = setup_logging()
