import os
import re
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ.get("BOT_TOKEN")
INSTA_USER = os.environ.get("INSTA_USER")
INSTA_PASS = os.environ.get("INSTA_PASS")

# Instagram Config
MAX_VIDEO_SIZE = int(os.environ.get("MAX_FILESIZE_MB", 50)) * 1024 * 1024
INSTAGRAM_PATTERN = re.compile(
    r"https?://(?:www\.)?instagram\.com/"
    r"(?:reel|reels|p|tv)/[\w-]+",
    re.IGNORECASE,
)
