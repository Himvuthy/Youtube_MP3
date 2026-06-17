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

# =========================
# DEBUG INFO
# =========================
import subprocess

print(
    subprocess.run(
        ["yt-dlp", "-F", "https://youtu.be/bEjfvakuDBM"],
        capture_output=True,
        text=True
    ).stdout
)
try:
    print("NODE:", subprocess.check_output(
        ["node", "--version"]
    ).decode().strip())
except Exception as e:
    print("NODE NOT FOUND:", e)

try:
    print(
        subprocess.check_output(
            ["ffmpeg", "-version"]
        ).decode().split("\n")[0]
    )
except Exception as e:
    print("FFMPEG NOT FOUND:", e)

# =========================
# CONFIG
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")


DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# =========================
# TELEGRAM HANDLER
# =========================

async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    url = update.message.text.strip()

    if "youtube.com" not in url and "youtu.be" not in url:
        await update.message.reply_text(
            "Please send a valid YouTube link."
        )
        return

    status = await update.message.reply_text(
        "Downloading..."
    )

    try:

        def download():

            ydl_opts = {
                "format": "bestaudio/best",

                "outtmpl": os.path.join(
                    DOWNLOAD_DIR,
                    "%(title)s.%(ext)s"
                ),

                "writethumbnail": True,

                "noplaylist": True,

                "quiet": False,

                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    },
                    {
                        "key": "FFmpegThumbnailsConvertor",
                        "format": "png",
                    },
                ],
            }

            with yt_dlp.YoutubeDL({}) as ydl:
                info = ydl.extract_info(url, download=False)

                print("FORMATS:")
                for f in info.get("formats", []):
                    print(
                    f"{f.get('format_id')} | "
                    f"{f.get('ext')} | "
                    f"{f.get('vcodec')} | "
                    f"{f.get('acodec')}"
                    )    

    

        info = await asyncio.to_thread(download)

        title = info.get(
            "title",
            "Unknown Title"
        )

        mp3_file = None
        thumbnail_file = None

        for file in os.listdir(DOWNLOAD_DIR):

            if not file.startswith(title):
                continue

            full_path = os.path.join(
                DOWNLOAD_DIR,
                file
            )

            if file.endswith(".mp3"):
                mp3_file = full_path

            elif file.endswith(".png"):
                thumbnail_file = full_path

        if thumbnail_file:

            with open(thumbnail_file, "rb") as photo:

                await update.message.reply_photo(
                    photo=photo
                )

        if mp3_file:

            with open(mp3_file, "rb") as audio:

                await update.message.reply_audio(
                    audio=audio,
                    title=title
                )

        await status.edit_text("Done!")

        # Cleanup
        if mp3_file and os.path.exists(mp3_file):
            os.remove(mp3_file)

        if thumbnail_file and os.path.exists(thumbnail_file):
            os.remove(thumbnail_file)

    except Exception as e:

        print("ERROR:", str(e))

        await status.edit_text(
            f"Download failed:\n{str(e)}"
        )

# =========================
# MAIN
# =========================

def main():

    if not BOT_TOKEN:
        raise ValueError(
            "BOT_TOKEN environment variable not found."
        )

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

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
