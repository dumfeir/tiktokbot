import os
import re
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")

class SocialDownloader:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.instagram.com/'
        }

    def fix_broken_url(self, text):
        """إصلاح الروابط المقطوعة وتصحيح الأخطاء الإملائية"""
        # تصحيح reei → reel
        text = re.sub(r'/ree[iI]', '/reel', text, flags=re.IGNORECASE)
        # جمع الروابط المقطوعة
        text = re.sub(r'(\S+)\s+(\S+)', r'\1\2', text)
        return text.strip()

    def is_instagram(self, url):
        """كشف روابط انستغرام مع تحمل الأخطاء الإملائية"""
        return bool(re.search(r'instagram\.com/ree[lL]', url, re.IGNORECASE))

    def download_instagram(self, url):
        """تحميل من انستغرام باستخدام api.savefrom.net"""
        try:
            api_url = "https://api.savefrom.net/api/convert"
            params = {
                'url': url,
                'format': 'mp4'
            }
            response = self.session.get(api_url, params=params, timeout=15).json()
            return response.get('url')
        except Exception as e:
            print(f"Instagram Error: {e}")
            return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw_text = update.message.text
    downloader = SocialDownloader()
    
    # إصلاح الرابط
    fixed_url = downloader.fix_broken_url(raw_text)
    
    if not downloader.is_instagram(fixed_url):
        await update.message.reply_text("⚠️ يرجى إرسال رابط Instagram Reel صحيح")
        return

    await update.message.chat.send_action("upload_video")

    video_url = downloader.download_instagram(fixed_url)
    
    if not video_url:
        await update.message.reply_text("❌ تعذر تحميل الريل. جرب رابطًا آخر أو حاول لاحقًا.")
        return

    try:
        response = downloader.session.get(video_url, stream=True, timeout=30)
        if response.status_code != 200:
            await update.message.reply_text("❌ فشل تحميل الفيديو")
            return

        await update.message.reply_video(
            video=response.raw,
            caption="✅ تم التحميل من Instagram",
            supports_streaming=True
        )
    except Exception as e:
        print(f"Error: {e}")
        await update.message.reply_text("⛔ حدث خطأ غير متوقع")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ البوت يعمل...")
    app.run_polling()
