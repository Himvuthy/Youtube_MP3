import os
import asyncio
import subprocess
import yt_dlp

from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    ContextTypes,
    filters,
)

# Debug checks
try:
    print("NODE:", subprocess.check_output(
        ["node", "--version"]).decode().strip())
except Exception as e:
    print("NODE NOT FOUND:", e)

try:
    print(subprocess.check_output(
        ["ffmpeg", "-version"]).decode().split("\n")[0])
except Exception as e:
    print("FFMPEG NOT FOUND:", e)

# Use Railway variable instead of hardcoded token
BOT_TOKEN = os.getenv("BOT_TOKEN")

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    url = update.message.text.strip()

    if "youtube.com" not in url and "youtu.be" not in url:
        await update.message.reply_text("Please send a valid YouTube link.")
        return

    msg = await update.message.reply_text("Downloading...")

    try:

        def download():

            ydl_opts = {
                "cookiefile": "cookies.txt",

                "format": "bestaudio/best",

                "outtmpl": os.path.join(
                    DOWNLOAD_DIR,
                    "%(title)s.%(ext)s"
                ),

                "writethumbnail": True,

                "extractor_args": {
                    "youtube": {
                        "player_client": [
                            "android",
                            "web"
                        ]
                    }
                },

                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "320",
                    },
                    {
                        "key": "FFmpegThumbnailsConvertor",
                        "format": "png",
                    },
                ],

                "quiet": False,
                "noplaylist": True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=True)

        info = await asyncio.to_thread(download)

        title = info.get("title", "Unknown Title")

        mp3_file = None
        thumbnail_file = None

        for file in os.listdir(DOWNLOAD_DIR):

            if not file.startswith(title):
                continue

            path = os.path.join(DOWNLOAD_DIR, file)

            if file.endswith(".mp3"):
                mp3_file = path

            elif file.endswith(".png"):
                thumbnail_file = path

        if thumbnail_file:
            with open(thumbnail_file, "rb") as photo:
                await update.message.reply_photo(photo)

        if mp3_file:
            with open(mp3_file, "rb") as audio:
                await update.message.reply_audio(
                    audio=audio,
                    title=title
                )

        await msg.edit_text("Done!")

    except Exception as e:
        await msg.edit_text(
            f"Download failed:\n{str(e)}"
        )


def main():

    if not BOT_TOKEN:
        raise ValueError(
            "BOT_TOKEN environment variable not found."
        )

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message
        )
    )

    print("Bot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()
