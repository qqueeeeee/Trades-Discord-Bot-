import pathlib
import os
import logging
from dotenv import load_dotenv
from logging.config import dictConfig

load_dotenv()

DISCORD_SECRET = os.getenv('DISCORD_TOKEN')

BASE_DIR = pathlib.Path(__file__).parent

COGS_DIR = BASE_DIR / "cogs"

DB_TOKEN =  os.getenv("INFLUXDB_TOKEN")

