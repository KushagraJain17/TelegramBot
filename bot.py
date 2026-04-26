import os
from aiohttp import web
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    filters,
    CommandHandler
)

from config import BOT_TOKEN, INSTAGRAM_PATTERN
from instagram import handle_instagram

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_message:
        return
    await update.effective_message.reply_text(
        "👋 Hey! Here's what I can do:\n\n"
        "📸 *Instagram Downloader*\n"
        "Send me any Instagram Reel / Post / IGTV link "
        "and I'll send you the video.\n\n"
        "Just paste an Instagram link ⬇️",
        parse_mode="Markdown",
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Route text messages: Instagram links → downloader."""
    if not update.effective_message or not update.effective_message.text:
        return

    text = update.effective_message.text

    # Handle Instagram links only
    if INSTAGRAM_PATTERN.search(text):
        await handle_instagram(update, context)

# --- WEB SERVER FOR RENDER FREE TIER ---
async def head(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", head)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 10000)))
    await site.start()
    print(f"🌐 Web server started on port {os.environ.get('PORT', 10000)}")

if __name__ == "__main__":
    if not BOT_TOKEN:
        print("❌ ERROR: 'BOT_TOKEN' environment variable is missing!")
        exit(1)

    # This function starts the web server once the bot's event loop is ready
    async def post_init(application):
        if os.environ.get("RENDER"):
            import asyncio
            asyncio.create_task(start_web_server())
            print("🌐 Web server deployment detected (Render).")
        print("🤖 Instagram Bot is running…")

    # Initialize Telegram Bot
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Run the bot (this handles the event loop correctly)
    app.run_polling()
