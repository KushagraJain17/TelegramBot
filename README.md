# Instagram Telegram Bot 📸🤖

A simple, optimized Telegram bot that downloads Instagram Reels, Posts, and Carousels directly to your chat.

## 🚀 Setup & Run

1. **Clone & Install**
   ```bash
   git clone https://github.com/KushagraJain17/TelegramBot.git
   cd TelegramBot
   pip install -r requirements.txt
   ```

2. **Generate Instagram Session**
   To securely download from Instagram without getting blocked, you need to generate a session string first.
   ```bash
   python get_session.py
   ```
   Follow the prompts to log in. At the end, copy the long `INSTA_SESSION64` base64 string it provides.

3. **Run Locally**
   Create a `.env` file in the folder with your details:
   ```env
   BOT_TOKEN=your_telegram_bot_token
   INSTA_SESSION64=the_string_you_just_copied
   ```
   Start the bot:
   ```bash
   python bot.py
   ```

## ☁️ Deploying to Render
1. Create a **Web Service** on Render and connect this GitHub repository.
2. Render will automatically detect the `render.yaml` configuration.
3. In the Render Dashboard, add your Environment Variables:
   - `BOT_TOKEN`: Your Telegram Bot token.
   - `INSTA_SESSION64`: The string you generated from `get_session.py`.
4. Deploy and enjoy your fast bot!
