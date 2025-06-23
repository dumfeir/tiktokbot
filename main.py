import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from keep_alive import keep_alive

BOT_TOKEN = os.getenv("BOT_TOKEN")

# استخراج ID الفيديو من رابط التيك توك
def extract_id(url):
    try:
        video_id = url.split("/video/")[1].split("?")[0]
        return video_id
    except:
        return None

async def download_tiktok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if "tiktok.com" not in url:
        await update.message.reply_text("❌ أرسل رابط TikTok صالح.")
        return

    await update.message.chat.send_action("upload_video")

    try:
        video_id = extract_id(url)
        if not video_id:
            await update.message.reply_text("❌ لم أتمكن من استخراج الفيديو.")
            return

        # TikMate API: الحصول على رابط التنزيل
        api_url = f"https://tikmate.online/api/lookup?url={url}"
        response = requests.get(api_url).json()

        if 'token' not in response:
            await update.message.reply_text("❌ تعذر الحصول على الفيديو.")
            return

        token = response['token']
        download_url = f"https://tikmate.online/download/{token}/{video_id}.mp4"

        video_data = requests.get(download_url).content

        with open("video.mp4", "wb") as f:
            f.write(video_data)

        await update.message.reply_video(video=open("video.mp4", "rb"), caption="✅ تم التنزيل بدون علامة مائية.")
        os.remove("video.mp4")

    except Exception as e:
        await update.message.reply_text(f"⚠️ خطأ أثناء التنزيل: {e}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    import nest_asyncio

    load_dotenv()
    keep_alive()

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_tiktok))

    nest_asyncio.apply()
    print("✅ Bot is running...")
    app.run_polling()
