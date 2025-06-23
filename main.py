import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from urllib.parse import urlparse

BOT_TOKEN = os.getenv("BOT_TOKEN")

class TikTokDownloader:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.tiktok.com/',
            'Origin': 'https://www.tiktok.com'
        }
        self.active_apis = [
            self._try_tiklydown_api,
            self._try_tikmate_api,
            self._try_tikwm_api,
            self._try_ttdownloader_api
        ]

    def _try_tiklydown_api(self, url):
        """API 1: tiklydown.eu.org"""
        try:
            api_url = "https://api.tiklydown.eu.org/api/download"
            payload = {'url': url}
            response = self.session.post(api_url, json=payload, timeout=10).json()
            if response.get('success'):
                return response['video']['url']
        except:
            return None

    def _try_tikmate_api(self, url):
        """API 2: tikmate.cc"""
        try:
            api_url = "https://api.tikmate.cc/api/download"
            data = {'url': url}
            response = self.session.post(api_url, data=data, timeout=10).json()
            return response.get('video_no_watermark')
        except:
            return None

    def _try_tikwm_api(self, url):
        """API 3: tikwm.com"""
        try:
            api_url = "https://www.tikwm.com/api/"
            data = {'url': url}
            response = self.session.post(api_url, data=data, timeout=10).json()
            return response.get('data', {}).get('play')
        except:
            return None

    def _try_ttdownloader_api(self, url):
        """API 4: ttdownloader.com"""
        try:
            api_url = "https://ttdownloader.com/req/"
            data = {'url': url}
            response = self.session.post(api_url, data=data, timeout=10).json()
            return response.get('video_no_watermark')
        except:
            return None

    def get_video_url(self, url):
        """تجربة جميع الواجهات بالترتيب"""
        for api in self.active_apis:
            video_url = api(url)
            if video_url:
                return video_url
        return None

async def handle_tiktok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    downloader = TikTokDownloader()

    if not any(x in url for x in ['tiktok.com', 'vm.tiktok', 'vt.tiktok']):
        await update.message.reply_text("⚠️ يرجى إرسال رابط TikTok صحيح فقط")
        return

    await update.message.chat.send_action("upload_video")

    try:
        video_url = downloader.get_video_url(url)
        
        if not video_url:
            await update.message.reply_text("❌ تعذر تحميل الفيديو، جميع الخوادم مشغولة حالياً")
            return

        response = downloader.session.get(video_url, stream=True, timeout=30)
        if response.status_code != 200:
            await update.message.reply_text("❌ فشل تحميل الفيديو من الخادم")
            return

        await update.message.reply_video(
            video=response.raw,
            caption="✅ تم التحميل بدون علامة مائية",
            supports_streaming=True,
            filename="tiktok_video.mp4"
        )

    except Exception as e:
        print(f"Error: {e}")
        await update.message.reply_text("⛔ حدث خطأ غير متوقع، يرجى المحاولة لاحقاً")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_tiktok))
    print("✅ البوت يعمل بنجاح...")
    app.run_polling()
