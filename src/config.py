import logging
from pathlib import Path

from starlette.config import Config
from starlette.datastructures import Secret

config = Config(".env")

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL: int = config("LOG_LEVEL", cast=int, default=logging.INFO)

ENVIRONMENT: str = config("ENVIRONMENT", default="local")
PROJECT_NAME: str = config("PROJECT_NAME", default="trustpilot-reviews")

# Default db location is directory located one level above the directory containing the application
DATABASE_PATH: Path = config("DATABASE_PATH", default=Path(__file__).resolve().parents[1], cast=Path)
DATABASE_NAME: str = config("DATABASE_NAME", default="reviews")
DATABASE: Path = DATABASE_PATH / (DATABASE_NAME + ".db")
DATABASE_PASSPHRASE: str = config("DATABASE_PASSPHRASE", cast=Secret)
