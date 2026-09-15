"""
Cấu hình ứng dụng - Load từ file .env bằng python-dotenv
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Tìm thư mục gốc của dự án
BASE_DIR = Path(__file__).resolve().parent.parent

# Load biến môi trường từ .env
load_dotenv(dotenv_path=BASE_DIR / ".env")

# Các thông số cấu hình
APP_ENV = os.getenv("APP_ENV", "development")
APP_PORT = int(os.getenv("APP_PORT", "8501"))

AUTO_REFRESH_INTERVAL = int(os.getenv("AUTO_REFRESH_INTERVAL", "10"))
CACHE_EXPIRY_HOURS = int(os.getenv("CACHE_EXPIRY_HOURS", "2"))

# Danh sách mã mặc định
raw_tickers = os.getenv("DEFAULT_TICKERS", "VNM,HPG,FPT,SSI,MWG,TCB,VHM,VIC")
DEFAULT_TICKERS = [t.strip().upper() for t in raw_tickers.split(",") if t.strip()]

# Đường dẫn TinyDB và Cache
TINYDB_PATH = BASE_DIR / os.getenv("TINYDB_PATH", "data_store/watchlist.json")
CACHE_DIR = BASE_DIR / os.getenv("CACHE_DIR", "data_store/cache")

# Nguồn dữ liệu
DEFAULT_DATA_SOURCE = os.getenv("DEFAULT_DATA_SOURCE", "VCI")

# Đảm bảo các thư mục lưu trữ luôn tồn tại
TINYDB_PATH.parent.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)
