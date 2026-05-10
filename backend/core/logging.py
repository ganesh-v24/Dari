from loguru import logger
import sys
import io

def setup_logging():
    logger.remove()
    # Windows cp1252 console can't print emojis; force utf-8 wrapper
    stdout = (
        io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        if sys.platform == "win32" else sys.stdout
    )
    logger.add(
        stdout,
        format="{time} | {level} | {message}",
        level="INFO"
    )
