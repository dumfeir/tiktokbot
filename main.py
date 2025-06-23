import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from urllib.parse import urlparse

BOT_TOKEN = os.getenv("BOT_TOKEN")

class SocialDownloader:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'en-US,en;q=0.9'
        }

    def download_tiktok(self, url):
        """تحميل من تيك توك بدون علامة مائية"""
        try:
            api_url = "https://api.tikmate.app/api/download"
            params = {'url': url}
            response = self.session.get(api_url, params=params, timeout=15).json()
            return response.get('video_no_watermark')
        except Exception as e:
            print(f"TikTok Error: {e}")
            return None

    def download_instagram(self, url):
        """تحميل ريلز من انستغرام"""
        try:
            # استخدم خدمة第三方 مثل savefrom.net
            api_url = "https://igram.world/api/dl"
            data = {'url': url}
            response = self.session.post(api_url, data=data, timeout=15).json()
            return response.get('url')  # قد يختلف حسب API المستخدم
        except Exception as e:
            print(f"Instagram Error: {e}")
            return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    downloader = SocialDownloader()
    
    # تحديد نوع الرابط
    if 'tiktok.com' in url:
        video_url = downloader.download_tiktok(url)
        platform = "TikTok"
    elif 'instagram.com/reel' in url:
        video_url = downloader.download_instagram(url)
        platform = "Instagram Reels"
    else:
        await update.message.reply_text("⚠️ الرابط غير مدعوم. يرجى إرسال رابط TikTok أو Instagram Reel فقط.")
        return

    await update.message.chat.send_action("upload_video")

    if not video_url:
        await update.message.reply_text("❌ تعذر تحميل الفيديو. يرجى المحاولة لاحقًا أو استخدام رابط آخر.")
        return

    try:
        with downloader.session.get(video_url, stream=True, timeout=30) as resp:
            if resp.status_code != 200:
                await update.message.reply_text("❌ فشل تحميل الفيديو من الخادم")
                return

            await update.message.reply_video(
                video=resp.raw,
                caption=f"✅ تم التحميل من {platform}",
                supports_streaming=True,
                filename="social_video.mp4"
            )
    except Exception as e:
        print(f"Download Error: {e}")
        await update.message.reply_text("⛔ حدث خطأ غير متوقع")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ البوت يعمل (يدعم TikTok + Instagram Reels)...")
    app.run_polling()
