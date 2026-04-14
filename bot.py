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

if __name__ == "__main__":
    if not BOT_TOKEN:
        print("❌ ERROR: 'BOT_TOKEN' environment variable is missing!")
        exit(1)

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("🤖 Instagram Bot is running…")
    app.run_polling()
