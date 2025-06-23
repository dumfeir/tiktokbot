import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from keep_alive import keep_alive

BOT_TOKEN = os.getenv("BOT_TOKEN")  # ضع التوكن في .env أو مباشرة هنا

async def download_tiktok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if "tiktok.com" not in url:
        await update.message.reply_text("❌ هذا ليس رابط TikTok صحيح.")
        return

    await update.message.chat.send_action("upload_video")

    api_url = f"https://api.tikwm.com/?url={url}"

    try:
        response = requests.get(api_url).json()

        if not response["data"]:
            await update.message.reply_text("❌ تعذر الحصول على الفيديو.")
            return

        video_url = response["data"]["play"]

        video_data = requests.get(video_url).content

        with open("video.mp4", "wb") as f:
            f.write(video_data)

        await update.message.reply_video(video=open("video.mp4", "rb"), caption="✅ تم التنزيل بدون علامة مائية!")

        os.remove("video.mp4")

    except Exception as e:
        await update.message.reply_text(f"⚠️ حدث خطأ: {e}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    keep_alive()

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_tiktok))

    import nest_asyncio
    nest_asyncio.apply()

    print("✅ Bot is running...")
    app.run_polling()
