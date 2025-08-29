import logging


def get_logger(name: str | None = None) -> logging.Logger:
    logger = logging.getLogger(name or "shelf")

    if not logger.hasHandlers():
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()

        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s in %(name)s: %(message)s",
        )

        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


logger = get_logger()
