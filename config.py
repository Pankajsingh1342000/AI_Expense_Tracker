from dotenv import load_dotenv
import os

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Use Railway volume path if set (persistent SQLite), else env override, else default
_volume_path = os.getenv("RAILWAY_VOLUME_MOUNT_PATH")
if _volume_path:
    DATABASE_URL = f"sqlite:///{_volume_path.rstrip('/')}/expenses.db"
else:
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./expenses.db")