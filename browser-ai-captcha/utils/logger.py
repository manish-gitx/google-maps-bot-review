import logging
from rich.logging import RichHandler
from rich.console import Console

console = Console()


def setup_logger(name: str = "bot", level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(level)
    handler = RichHandler(console=console, rich_tracebacks=True, show_path=False)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    return logger


log = setup_logger()
