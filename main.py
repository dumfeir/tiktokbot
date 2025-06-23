import os
import re
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from urllib.parse import urlparse, unquote

BOT_TOKEN = os.getenv("BOT_TOKEN")

class Downloader:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.tiktok.com/'
        }

    def clean_url(self, url):
        """تنظيف الروابط من الأحرف الزائدة"""
        url = unquote(url).strip()
        url = re.sub(r'\s+', '', url)  # إزالة المسافات
        return url.split('?')[0]  # إزالة query parameters

    def is_tiktok(self, url):
        """التأكد من أن الرابط من تيك توك"""
        domains = ['tiktok.com', 'vm.tiktok', 'vt.tiktok']
        return any(d in url for d in domains)

    def is_instagram(self, url):
        """التأكد من أن الرابط من انستغرام"""
        return 'instagram.com/reel' in url

    def get_tiktok(self, url):
        try:
            api_url = "https://api.tikmate.cc/api/download"
            response = self.session.post(api_url, data={'url': url}, timeout=10).json()
            return response.get('video_no_watermark')
        except:
            return None

    def get_instagram(self, url):
        try:
            api_url = "https://igram.world/api/dl"
            response = self.session.post(api_url, json={'url': url}, timeout=10).json()
            return response.get('url')
        except:
            return None

async def handle_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw_url = update.message.text.strip()
    downloader = Downloader()
    
    # تنظيف الرابط
    clean_url = downloader.clean_url(raw_url)
    
    # تحديد المنصة
    if downloader.is_tiktok(clean_url):
        platform = "TikTok"
        video_url = downloader.get_tiktok(clean_url)
    elif downloader.is_instagram(clean_url):
        platform = "Instagram Reels"
        video_url = downloader.get_instagram(clean_url)
    else:
        await update.message.reply_text("⚠️ الرابط غير مدعوم. يرجى إرسال رابط TikTok أو Instagram Reel صحيح.")
        return

    await update.message.chat.send_action("upload_video")

    if not video_url:
        await update.message.reply_text("❌ تعذر تحميل الفيديو. جرب رابطًا آخر.")
        return

    try:
        response = downloader.session.get(video_url, stream=True, timeout=30)
        if response.status_code != 200:
            await update.message.reply_text("❌ فشل الاتصال بالخادم")
            return

        await update.message.reply_video(
            video=response.raw,
            caption=f"✅ تم التحميل من {platform}",
            supports_streaming=True,
            filename="video.mp4"
        )
    except Exception as e:
        print(f"Error: {e}")
        await update.message.reply_text("⛔ حدث خطأ غير متوقع")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_download))
    print("✅ البوت يعمل (يدعم TikTok + Instagram Reels)...")
    app.run_polling()
