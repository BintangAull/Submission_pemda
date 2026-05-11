
import os
from dotenv import load_dotenv
# untuk semua variable agar lebih clean dan profesional

# konfigurasi scraping data
BASE_URL = "https://fashion-studio.dicoding.dev"
MAX_PAGE = 50
REQUEST_TIMEOUT = 10
MIN_DELAY = 3
MAX_DELAY = 6

# user agent
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


# konfigurasi database anda
# load file .env
load_dotenv()  # load dari file .env
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in environment variables")