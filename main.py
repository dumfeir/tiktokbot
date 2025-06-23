import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from keep_alive import keep_alive

BOT_TOKEN = os.getenv("BOT_TOKEN")

# ✅ استخراج ID الفيديو من رابط TikTok الكامل
def extract_id(url):
    try:
        if "/video/" in url:
            return url.split("/video/")[1].split("?")[0]
    except:
        return None

# ✅ حل الروابط المختصرة (مثل vt.tiktok.com) إلى رابط كامل
def resolve_redirect(url):
    try:
        response = requests.head(url, allow_redirects=True, timeout=5)
        return response.url
    except:
        return url

async def download_tiktok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if "tiktok.com" not in url:
        await update.message.reply_text("❌ أرسل رابط TikTok صحيح.")
        return

    await update.message.chat.send_action("upload_video")

    try:
        # ✅ حل الرابط إذا كان مختصرًا
        final_url = resolve_redirect(url)

        # ✅ استخراج ID الفيديو
        video_id = extract_id(final_url)
        if not video_id:
            await update.message.reply_text("❌ لم أتمكن من استخراج الفيديو.")
            return

        # ✅ طلب TikMate للحصول على رابط التنزيل
        api_url = f"https://tikmate.online/api/lookup?url={final_url}"
        response = requests.get(api_url).json()

        if 'token' not in response:
            await update.message.reply_text("❌ تعذر الحصول على الفيديو.")
            return

        token = response['token']
        download_url = f"https://tikmate.online/download/{token}/{video_id}.mp4"

        video_data = requests.get(download_url).content

        with open("video.mp4", "wb") as f:
            f.write(video_data)

        await update.message.reply_video(video=open("video.mp4", "rb"), caption="✅ تم التنزيل بدون علامة مائية!")
        os.remove("video.mp4")

    except Exception as e:
        await update.message.reply_text(f"⚠️ حدث خطأ أثناء التنزيل: {e}")

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
