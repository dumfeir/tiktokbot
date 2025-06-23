import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from keep_alive import keep_alive
from urllib.parse import urlparse

BOT_TOKEN = os.getenv("BOT_TOKEN")

class TikTokDownloader:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.tiktok.com/'
        })

    def resolve_short_url(self, url):
        """حل الروابط المختصرة مثل vt.tiktok.com"""
        try:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
                
            response = self.session.head(url, allow_redirects=True, timeout=15)
            return response.url
        except Exception as e:
            print(f"Error resolving URL: {e}")
            return url

    def get_video_url(self, original_url):
        """الحصول على رابط الفيديو باستخدام عدة مصادر"""
        # قائمة بواجهات برمجة التطبيقات البديلة
        apis = [
            self._try_tikmate_api,
            self._try_tiklydown_api,
            self._try_tikwm_api
        ]
        
        for api in apis:
            try:
                video_url = api(original_url)
                if video_url:
                    return video_url
            except Exception as e:
                print(f"API Error: {e}")
                continue
                
        return None

    def _try_tikmate_api(self, url):
        """محاولة استخدام واجهة tikmate.online"""
        api_url = "https://tikmate.online/api/lookup"
        data = {'url': url}
        response = self.session.post(api_url, data=data, timeout=15).json()
        if response.get('token'):
            return f"https://tikmate.online/download/{response['token']}/video.mp4"
        return None

    def _try_tiklydown_api(self, url):
        """محاولة استخدام واجهة tiklydown.eu.org"""
        api_url = "https://api.tiklydown.eu.org/api/download"
        payload = {'url': url}
        response = self.session.post(api_url, json=payload, timeout=15).json()
        if response.get('success') and response.get('video', {}).get('url'):
            return response['video']['url']
        return None

    def _try_tikwm_api(self, url):
        """محاولة استخدام واجهة tikwm.com"""
        api_url = "https://www.tikwm.com/api/"
        data = {'url': url}
        response = self.session.post(api_url, data=data, timeout=15).json()
        if response.get('data', {}).get('play'):
            return response['data']['play']
        return None

async def download_tiktok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    downloader = TikTokDownloader()

    # التحقق من أن الرابط من تيك توك
    if not any(domain in url for domain in ['tiktok.com', 'vm.tiktok.com', 'vt.tiktok.com']):
        await update.message.reply_text("❌ الرابط غير صحيح. يرجى إرسال رابط TikTok فقط.")
        return

    await update.message.chat.send_action("upload_video")

    try:
        # حل الرابط المختصر أولاً
        final_url = downloader.resolve_short_url(url)
        print(f"Processing URL: {final_url}")

        # الحصول على رابط الفيديو
        video_url = downloader.get_video_url(final_url)
        
        if not video_url:
            await update.message.reply_text("❌ تعذر العثور على الفيديو. قد يكون الرابط غير صحيح أو الخدمة غير متوفرة.")
            return

        # تنزيل وإرسال الفيديو مباشرة
        with downloader.session.get(video_url, stream=True, timeout=30) as video_response:
            if video_response.status_code != 200:
                await update.message.reply_text("❌ تعذر تنزيل الفيديو")
                return

            await update.message.reply_video(
                video=video_response.raw,
                caption="✅ تم التنزيل بنجاح!",
                supports_streaming=True,
                filename="tiktok_video.mp4"
            )

    except Exception as e:
        print(f"Error: {str(e)}")
        await update.message.reply_text("❌ حدث خطأ غير متوقع. يرجى المحاولة لاحقاً أو إرسال رابط مختلف.")

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
