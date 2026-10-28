import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine import URL

load_dotenv(Path(__file__).resolve().parents[2] / "database" / "v3" / ".env")
DB_HOST = os.getenv("BIOSAKA_DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("BIOSAKA_DB_PORT", "3307"))
DB_NAME = os.getenv("BIOSAKA_DB_NAME", "biosaka_v3_dev")
DB_USER = os.getenv("BIOSAKA_DB_USER", "biosaka")
DB_PASSWORD = os.environ["BIOSAKA_DB_PASSWORD"]
API_TOKEN = os.environ["BIOSAKA_API_TOKEN"]
if len(API_TOKEN) < 32:
    raise ValueError("BIOSAKA_API_TOKEN deve ter pelo menos 32 caracteres.")
DATABASE_URL = URL.create("mysql+pymysql", username=DB_USER, password=DB_PASSWORD,
                          host=DB_HOST, port=DB_PORT, database=DB_NAME, query={"charset": "utf8mb4"})
CORS_ORIGINS = os.getenv("BIOSAKA_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
