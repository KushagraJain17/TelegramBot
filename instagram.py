"""
instagram.py — Fast Instagram downloader (In-Memory).
"""

import asyncio
import io
import os
import re

import aiohttp
import instaloader
from telegram import Update, InputMediaPhoto, InputMediaVideo
from telegram.ext import ContextTypes

from config import INSTAGRAM_PATTERN, MAX_VIDEO_SIZE, INSTA_USER, INSTA_PASS

import logging
logging.getLogger("instaloader").setLevel(logging.CRITICAL)

_L = instaloader.Instaloader(
    download_pictures=False,
    download_videos=False,
    download_video_thumbnails=False,
    download_geotags=False,
    download_comments=False,
    save_metadata=False,
    compress_json=False,
    quiet=True,
    max_connection_attempts=1,
    iphone_support=False,
)

SESSION_FILE = "insta_session"

def _setup_session():
    # If base64 session is provided via Env Var, write it to file to authenticate
    session_64 = os.environ.get("INSTA_SESSION64")
    if session_64:
        import base64
        try:
            with open(SESSION_FILE, "wb") as f:
                f.write(base64.b64decode(session_64))
        except Exception as e:
            print(f"❌ Failed to decode INSTA_SESSION64: {e}")

    if os.path.exists(SESSION_FILE):
        try:
            _L.load_session_from_file(INSTA_USER or "bot_user", filename=SESSION_FILE)
            return
        except Exception:
            pass

    if INSTA_USER and INSTA_PASS:
        try:
            _L.login(INSTA_USER, INSTA_PASS)
            _L.save_session_to_file(filename=SESSION_FILE)
        except Exception:
            pass

_setup_session()

# ── Fetch and Download ────────────────────────────────────────────────────────

def _extract_shortcode(url: str) -> str:
    m = re.search(r"/(?:p|reel|reels|tv)/([\w-]+)", url)
    if not m:
        raise ValueError(f"Cannot parse URL: {url}")
    return m.group(1)

async def _fetch_and_download(shortcode: str) -> list[dict]:
    # Run instaloader blocking call in a background thread
    post = await asyncio.to_thread(instaloader.Post.from_shortcode, _L.context, shortcode)
    
    nodes = list(post.get_sidecar_nodes())[:10] if post.typename == "GraphSidecar" else [post]
    caption = (post.caption or "")[:1024]
    
    items = []
    for i, n in enumerate(nodes):
        items.append({
            "type": "video" if n.is_video else "photo",
            "url": n.video_url if n.is_video else (n.display_url if hasattr(n, 'display_url') else n.url),
            "caption": caption if i == 0 else ""
        })

    # Download to memory concurrently
    async def _dl(session, item):
        try:
            # Add user-agent header to match instaloader
            headers = {"User-Agent": _L.context.user_agent}
            async with session.get(item["url"], headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    item["bytes"] = io.BytesIO(data)
                    item["size"] = len(data)
        except Exception:
            pass
        return item

    # Use a single session with proper connection limits
    connector = aiohttp.TCPConnector(limit=10)
    async with aiohttp.ClientSession(connector=connector) as session:
        await asyncio.gather(*[_dl(session, item) for item in items])
        
    return [i for i in items if "bytes" in i]

# ── Telegram Handler ─────────────────────────────────────────────────────────

async def handle_instagram(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    message = update.effective_message
    if not message or not message.text:
        return False

    match = INSTAGRAM_PATTERN.search(message.text)
    if not match:
        return False

    status_msg = await message.reply_text("⏳ Processing…")

    try:
        shortcode = _extract_shortcode(match.group(0))
        results = await _fetch_and_download(shortcode)

        if not results:
            raise ValueError("Failed to download media files.")

        if any(r.get("size", 0) > MAX_VIDEO_SIZE for r in results):
            await status_msg.edit_text("❌ File too large (max 50 MB).")
            return True

        await status_msg.edit_text("📤 Uploading…")

        if len(results) == 1:
            item = results[0]
            if item["type"] == "video":
                await message.reply_video(video=item["bytes"], caption=item["caption"])
            else:
                await message.reply_photo(photo=item["bytes"], caption=item["caption"])
        else:
            media = [
                InputMediaVideo(r["bytes"], caption=r["caption"]) if r["type"] == "video" 
                else InputMediaPhoto(r["bytes"], caption=r["caption"])
                for r in results
            ]
            await message.reply_media_group(media=media)

    except Exception as e:
        err = str(e).lower()
        if "private" in err or "not found" in err:
            await status_msg.edit_text("❌ Post not found or private.")
        elif "rate" in err or "429" in err:
            await status_msg.edit_text("❌ Rate limited. Try later.")
        else:
            await status_msg.edit_text("❌ Download failed.")
    finally:
        await status_msg.delete()

    return True