import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from urllib.parse import urlparse

BOT_TOKEN = os.getenv("BOT_TOKEN")

class TikTokAPI:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.tiktok.com/'
        }
        self.active_apis = [
            self._try_tikmate,
            self._try_tikdown,
            self._try_ddinstagram,
            self._try_savetk
        ]

    def _try_tikmate(self, url):
        """API 1: tikmate.online"""
        try:
            response = self.session.post(
                "https://tikmate.online/api/lookup",
                data={'url': url},
                timeout=10
            ).json()
            return f"https://tikmate.online/download/{response['token']}/video.mp4"
        except:
            return None

    def _try_tikdown(self, url):
        """API 2: tikdown.org"""
        try:
            response = self.session.get(
                f"https://tikdown.org/getAjax?url={url}",
                timeout=10
            ).json()
            return response.get('video')
        except:
            return None

    def _try_ddinstagram(self, url):
        """API 3: ddinstagram.com"""
        try:
            resolved = self.session.head(url, allow_redirects=True).url
            if 'vm.tiktok.com' in resolved:
                return resolved.replace('vm.tiktok.com', 'ddinstagram.com')
            return None
        except:
            return None

    def _try_savetk(self, url):
        """API 4: savetk.app"""
        try:
            response = self.session.post(
                "https://savetk.app/api/v1/download",
                json={'url': url},
                timeout=10
            ).json()
            return response.get('url')
        except:
            return None

    def get_video(self, url):
        """تجربة جميع الواجهات بالترتيب"""
        for api in self.active_apis:
            video_url = api(url)
            if video_url:
                return video_url
        return None

async def handle_tiktok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    tiktok = TikTokAPI()

    if not any(x in url for x in ['tiktok.com', 'vm.tiktok', 'vt.tiktok']):
        await update.message.reply_text("⚠️ الرابط غير صالح، يرجى إرسال رابط TikTok فقط")
        return

    await update.message.chat.send_action("upload_video")

    try:
        video_url = tiktok.get_video(url)
        
        if not video_url:
            await update.message.reply_text("❌ تعذر تحميل الفيديو، جرب رابطًا آخر")
            return

        with self.session.get(video_url, stream=True, timeout=30) as resp:
            if resp.status_code != 200:
                await update.message.reply_text("❌ فشل تحميل الفيديو من الخادم")
                return

            await update.message.reply_video(
                video=resp.raw,
                caption="✅ تم التحميل بدون علامة مائية",
                supports_streaming=True
            )

    except Exception as e:
        print(f"Error: {e}")
        await update.message.reply_text("⛔ حدث خطأ غير متوقع، يرجى المحاولة لاحقًا")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_tiktok))
    app.run_polling()
