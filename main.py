import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from keep_alive import keep_alive

BOT_TOKEN = os.getenv("BOT_TOKEN")

class TikTokDownloader:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.tiktok.com/'
        }

    def try_apis(self, url):
        """تجربة عدة واجهات برمجة تطبيقات لإزالة العلامة المائية"""
        apis = [
            self._try_tikmate_api,
            self._try_tiklydown_api,
            self._try_ttdownloader_api,
            self._try_snaptik_api,
            self._try_tikwm_api
        ]
        
        for api in apis:
            try:
                result = api(url)
                if result:
                    return result
            except Exception as e:
                print(f"Error with API: {e}")
        return None

    def _try_tikmate_api(self, url):
        api_url = "https://api.tikmate.app/api/download"
        params = {'url': url}
        response = self.session.get(api_url, params=params, timeout=10).json()
        return response.get('video_no_watermark')

    def _try_tiklydown_api(self, url):
        api_url = "https://api.tiklydown.eu.org/api/download"
        payload = {'url': url}
        response = self.session.post(api_url, json=payload, timeout=10).json()
        return response.get('video', {}).get('url')

    def _try_ttdownloader_api(self, url):
        api_url = "https://ttdownloader.com/req/"
        data = {'url': url}
        response = self.session.post(api_url, data=data, timeout=10).json()
        return response.get('video_no_watermark')

    def _try_snaptik_api(self, url):
        api_url = "https://snaptik.app/api/v1/get-video"
        data = {'url': url}
        response = self.session.post(api_url, data=data, timeout=10).json()
        return response.get('data', {}).get('play')

    def _try_tikwm_api(self, url):
        api_url = "https://www.tikwm.com/api/"
        data = {'url': url}
        response = self.session.post(api_url, data=data, timeout=10).json()
        return response.get('data', {}).get('play')

async def download_tiktok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    downloader = TikTokDownloader()

    if not any(x in url for x in ['tiktok.com', 'vt.tiktok', 'vm.tiktok']):
        await update.message.reply_text("❌ يرجى إرسال رابط TikTok صحيح")
        return

    await update.message.chat.send_action("upload_video")

    try:
        video_url = downloader.try_apis(url)
        
        if not video_url:
            await update.message.reply_text("❌ تعذر إزالة العلامة المائية. جرب رابطًا آخر أو حاول لاحقًا.")
            return

        response = downloader.session.get(video_url, stream=True, timeout=30)
        
        if response.status_code != 200:
            await update.message.reply_text("❌ فشل تنزيل الفيديو")
            return

        await update.message.reply_video(
            video=response.raw,
            caption="✅ تم التنزيل بدون علامة مائية",
            supports_streaming=True,
            filename="tiktok_video.mp4"
        )

    except Exception as e:
        print(f"Error: {e}")
        await update.message.reply_text("⚠️ حدث خطأ غير متوقع. يرجى المحاولة لاحقًا.")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    keep_alive()

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_tiktok))
    print("✅ البوت يعمل...")
    app.run_polling()
