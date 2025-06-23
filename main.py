import os
import re
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")

class InstagramDownloader:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.instagram.com/'
        }
        self.api_providers = [
            self._try_savefrom,
            self._try_igram,
            self._try_snapinsta
        ]

    def _extract_reel_url(self, text):
        """استخراج رابط الريل من النص مع تصحيح الأخطاء"""
        # تصحيح الأخطاء الشائعة (feel → reel)
        text = re.sub(r'/f[eE]{2}l/', '/reel/', text, flags=re.IGNORECASE)
        # إزالة المسافات بين أجزاء الرابط
        text = re.sub(r'(\S+)\s+(\S+)', r'\1\2', text)
        # استخراج الرابط
        url_match = re.search(
            r'(https?://(?:www\.)?instagram\.com/reel/[a-zA-Z0-9_-]+/?\??[^\s]*)',
            text
        )
        return url_match.group(0) if url_match else None

    def _try_savefrom(self, url):
        """استخدام savefrom.net API"""
        try:
            api_url = "https://api.savefrom.net/api/convert"
            params = {'url': url, 'format': 'mp4'}
            response = self.session.get(api_url, params=params, timeout=15).json()
            return response.get('url')
        except:
            return None

    def _try_igram(self, url):
        """استخدام igram.world API"""
        try:
            api_url = "https://igram.world/api/dl"
            data = {'url': url}
            response = self.session.post(api_url, data=data, timeout=15).json()
            return response.get('url')
        except:
            return None

    def _try_snapinsta(self, url):
        """استخدام snapinsta.app API"""
        try:
            api_url = "https://snapinsta.app/api/ajaxSearch"
            data = {'q': url}
            response = self.session.post(api_url, data=data, timeout=15).json()
            return response.get('links', [{}])[0].get('url')
        except:
            return None

    def download_reel(self, text):
        """التحميل باستخدام أفضل API متاح"""
        url = self._extract_reel_url(text)
        if not url:
            return None, "⚠️ لم يتم التعرف على رابط الريل الصحيح"

        for api in self.api_providers:
            video_url = api(url)
            if video_url:
                return video_url, None
        
        return None, "❌ جميع الخوادم مشغولة حالياً، حاول لاحقاً"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    downloader = InstagramDownloader()
    
    video_url, error_msg = downloader.download_reel(update.message.text)
    
    if error_msg:
        await update.message.reply_text(error_msg)
        return

    await update.message.chat.send_action("upload_video")

    try:
        response = downloader.session.get(video_url, stream=True, timeout=30)
        if response.status_code != 200:
            await update.message.reply_text("❌ فشل تحميل الفيديو")
            return

        await update.message.reply_video(
            video=response.raw,
            caption="✅ تم التحميل بنجاح من Instagram",
            supports_streaming=True,
            filename="instagram_reel.mp4"
        )
    except Exception as e:
        print(f"Error: {e}")
        await update.message.reply_text("⛔ حدث خطأ أثناء التحميل")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ البوت يعمل (متخصص في Instagram Reels)...")
    app.run_polling()
