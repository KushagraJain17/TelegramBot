"""
instagram.py — Fast Instagram downloader (Optimized).
"""

import asyncio
import logging
import os
import re
import shutil
import tempfile

import aiohttp
import instaloader
from telegram import Update, InputMediaPhoto, InputMediaVideo
from telegram.ext import ContextTypes

from config import INSTAGRAM_PATTERN, MAX_VIDEO_SIZE, INSTA_USER, INSTA_PASS

# ── Constants ─────────────────────────────────────────────────────────────────

_CAPTION_LIMIT  = 1024
_UPLOAD_TIMEOUT = 120
_MAX_ITEMS      = 10

_DL_TIMEOUT = aiohttp.ClientTimeout(
    total=25,
    sock_connect=10,
    sock_read=20
)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.instagram.com/",
}

logging.getLogger("instaloader").setLevel(logging.CRITICAL)

# ── Instaloader Setup ─────────────────────────────────────────────────────────

_L = instaloader.Instaloader(
    download_pictures=False,
    download_videos=False,
    download_video_thumbnails=False,
    download_geotags=False,
    download_comments=False,
    save_metadata=False,
    compress_json=False,
    quiet=True,
    request_timeout=10,
    max_connection_attempts=1,
)

_L.context._session.headers.update(_HEADERS)

SESSION_FILE = "insta_session"

def _setup_session():
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

def _get_cookies():
    try:
        return _L.context._session.cookies.get_dict()
    except Exception:
        return {}

# ── Helpers ───────────────────────────────────────────────────────────────────

def _extract_shortcode(url: str) -> str:
    m = re.search(r"/(?:p|reel|reels|tv)/([\w-]+)", url)
    if not m:
        raise ValueError(f"Cannot parse URL: {url}")
    return m.group(1)

def _make_caption(raw: str) -> str:
    return raw[:_CAPTION_LIMIT] if raw else ""

# ── URL Collector ─────────────────────────────────────────────────────────────

def _collect_urls(shortcode: str) -> list[dict]:
    post = instaloader.Post.from_shortcode(_L.context, shortcode)

    caption = post.caption or ""

    items = []

    if post.typename == "GraphSidecar":
        for i, node in enumerate(post.get_sidecar_nodes()):
            if i >= _MAX_ITEMS:
                break

            items.append({
                "type": "video" if node.is_video else "photo",
                "url": node.video_url if node.is_video else node.display_url,
                "caption": caption if i == 0 else "",
            })
    else:
        items.append({
            "type": "video" if post.is_video else "photo",
            "url": post.video_url if post.is_video else post.url,
            "caption": caption,
            "duration": getattr(post, "video_duration", None),
        })

    return items

# ── Optimized Downloader ─────────────────────────────────────────────────────

async def _download_file(session: aiohttp.ClientSession, url: str, path: str) -> bool:
    cookies = _get_cookies()

    for attempt in range(3):
        try:
            async with session.get(url, headers=_HEADERS, cookies=cookies) as resp:

                if resp.status != 200:
                    if resp.status == 403:
                        await asyncio.sleep(0.8 * (attempt + 1))
                        continue
                    return False

                size = 0
                with open(path, "wb") as f:
                    async for chunk in resp.content.iter_chunked(131072):
                        size += len(chunk)
                        f.write(chunk)

                return size > 0

        except Exception:
            if attempt == 2:
                return False

    return False

# ── Concurrent Downloader ─────────────────────────────────────────────────────

async def _download_all(url_items: list[dict], target_dir: str) -> list[dict]:

    connector = aiohttp.TCPConnector(
        limit=8,
        ttl_dns_cache=300,
        enable_cleanup_closed=True
    )

    async with aiohttp.ClientSession(
        connector=connector,
        timeout=_DL_TIMEOUT
    ) as session:

        tasks = []
        paths = []

        for i, item in enumerate(url_items):
            ext = ".mp4" if item["type"] == "video" else ".jpg"
            path = os.path.join(target_dir, f"item_{i}{ext}")

            paths.append(path)
            tasks.append(_download_file(session, item["url"], path))

        results = await asyncio.gather(*tasks)

    output = []
    for item, path, ok in zip(url_items, paths, results):
        if ok:
            output.append({
                **item,
                "path": path,
                "size": os.path.getsize(path),
            })

    return output

# ── Main Fetcher ─────────────────────────────────────────────────────────────

async def _fetch_post(shortcode: str, tmp_dir: str) -> list[dict]:
    target_dir = os.path.join(tmp_dir, shortcode)
    os.makedirs(target_dir, exist_ok=True)

    loop = asyncio.get_running_loop()
    url_items = await loop.run_in_executor(None, _collect_urls, shortcode)

    if not url_items:
        raise ValueError("No media found in this post.")

    results = await _download_all(url_items, target_dir)

    if not results:
        raise ValueError("Failed to download media files.")

    return results

# ── Telegram Handler ─────────────────────────────────────────────────────────

async def handle_instagram(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    message = update.effective_message
    if not message or not message.text:
        return False

    match = INSTAGRAM_PATTERN.search(message.text)
    if not match:
        return False

    url = match.group(0)
    status_msg = await message.reply_text("⏳ Downloading…")
    tmp_dir = tempfile.mkdtemp()

    try:
        shortcode = _extract_shortcode(url)
        results = await _fetch_post(shortcode, tmp_dir)

        for r in results:
            if r["size"] > MAX_VIDEO_SIZE:
                await status_msg.edit_text("❌ File too large (max 50 MB).")
                return True

        await status_msg.edit_text("📤 Uploading…")

        if len(results) == 1:
            item = results[0]
            cap = _make_caption(item.get("caption", ""))

            with open(item["path"], "rb") as fh:
                if item["type"] == "video":
                    await message.reply_video(video=fh, caption=cap)
                else:
                    await message.reply_photo(photo=fh, caption=cap)

        else:
            handles, media = [], []

            for i, item in enumerate(results):
                fh = open(item["path"], "rb")
                handles.append(fh)

                cap = _make_caption(item.get("caption", "")) if i == 0 else ""

                media.append(
                    InputMediaVideo(fh, cap)
                    if item["type"] == "video"
                    else InputMediaPhoto(fh, cap)
                )

            try:
                await message.reply_media_group(media=media)
            finally:
                for fh in handles:
                    fh.close()

        await status_msg.delete()

    except Exception as e:
        err = str(e).lower()

        if "private" in err or "not found" in err:
            await status_msg.edit_text("❌ Post not found or private.")
        elif "rate" in err or "429" in err:
            await status_msg.edit_text("❌ Rate limited. Try later.")
        else:
            await status_msg.edit_text("❌ Download failed.")

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    return True