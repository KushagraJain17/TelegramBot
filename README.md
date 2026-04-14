# Instagram Downloader Telegram Bot 📸🤖

A fast and optimized Telegram bot that downloads Instagram Reels, Posts, and IGTV videos directly to your Telegram chat. 

## ✨ Features
- **Instant Media Fetching:** Send an Instagram link and instantly receive the media.
- **Supports All Formats:** Downloads photos, videos, and multi-image/video carousel posts.
- **Optimized Downloader:** Uses concurrent async downloads for high performance.
- **Limits & Checks:** Validates file sizes automatically (defaults to max 50MB for Telegram compatibility).

## 🚀 Setup & Installation (Local)

### Prerequisites
- Python 3.9+
- A Telegram Bot Token from [@BotFather](https://t.me/botfather)
- An Instagram account (recommended to use an alternate/burner account to avoid rate limits or bans).

### 1. Clone the repository
```bash
git clone https://github.com/KushagraJain17/TelegramBot.git
cd TelegramBot
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file in the root directory and add the following keys:
```env
BOT_TOKEN=your_telegram_bot_token_here
INSTA_USER=your_instagram_username
INSTA_PASS=your_instagram_password
MAX_FILESIZE_MB=50
```

### 4. Run the Bot
```bash
python bot.py
```
You should see: `🤖 Instagram Bot is running…`. Go to Telegram and start sending links!

---

## ☁️ Deployment (Render)

This repository includes a `render.yaml` file, which makes it extremely easy to deploy on [Render](https://render.com) using their Blueprint infrastructure.

1. Create an account on Render.
2. In the Render Dashboard, click **New +** and select **Blueprint**.
3. Connect this GitHub repository.
4. Render will automatically detect the configuration for the **Background Worker**.
5. During setup, you will be prompted to provide your Environment Variables:
   - `BOT_TOKEN`
   - `INSTA_USER`
   - `INSTA_PASS`
6. Click **Apply** and wait for the deployment to finish!

## ⚠️ Notes on Instagram Blocks (403 Errors)
Instagram is very aggressive against automated scrapers. If you encounter `403 Forbidden` errors or get a `login_required` error:
- Ensure your `INSTA_USER` and `INSTA_PASS` are correct.
- Sometimes logging into that Instagram account manually on a web browser and approving the login attempt helps.
- Consider regularly rotating your Instagram bot account if you hit rate limit blocks frequently.
