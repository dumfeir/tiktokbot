import os
import re
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from keep_alive import keep_alive
from urllib.parse import urlparse

BOT_TOKEN = os.getenv("BOT_TOKEN")

# ✅ تحسين دالة استخراج ID الفيديو
def extract_id(url):
    try:
        # تحقق من أن الرابط من TikTok أولاً
        parsed = urlparse(url)
        if "tiktok.com" not in parsed.netloc:
            return None
            
        # حل أي روابط مختصرة
        final_url = resolve_redirect(url)
        
        # نمط regex لاكتشاف معرف الفيديو في مختلف تنسيقات الروابط
        patterns = [
            r"/video/(\d+)",  # الروابط العادية
            r"@[\w.]+/video/(\d+)",  # روابط مع اسم مستخدم
            r"/(\d+)(?:\.html|\?|$)",  # روابط رقمية فقط
            r"item_id=(\d+)"  # روابط معلمة
        ]
        
        for pattern in patterns:
            match = re.search(pattern, final_url)
            if match:
                return match.group(1)
                
        return None
    except:
        return None

# ✅ حل الروابط المختصرة
def resolve_redirect(url):
    try:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
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
            await update.message.reply_text("❌ لم أتمكن من استخراج الفيديو. الرابط غير صحيح أو غير مدعوم.")
            return

        # ✅ استخدام API مختلف أكثر موثوقية
        api_url = f"https://api.tiklydown.eu.org/api/info?url={final_url}"
        headers = {
            'User-Agent': 'Mozilla/5.0'
        }
        response = requests.get(api_url, headers=headers).json()

        if not response.get('success') or not response.get('video'):
            await update.message.reply_text("❌ تعذر الحصول على الفيديو من الخدمة.")
            return

        download_url = response['video']['download_url']
        video_data = requests.get(download_url, headers=headers).content

        with open("video.mp4", "wb") as f:
            f.write(video_data)

        await update.message.reply_video(
            video=open("video.mp4", "rb"),
            caption="✅ تم التنزيل بدون علامة مائية!",
            supports_streaming=True
        )
        os.remove("video.mp4")

    except Exception as e:
        await update.message.reply_text(f"⚠️ حدث خطأ أثناء التنزيل: {str(e)}")

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
