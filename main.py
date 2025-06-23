import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from keep_alive import keep_alive

BOT_TOKEN = os.getenv("BOT_TOKEN")

class TikTokHandler:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.tiktok.com/'
        }

    def get_no_watermark(self, url):
        """الحصول على رابط بدون علامة مائية باستخدام api.tikmate.cc"""
        try:
            # أولاً: حل الرابط المختصر
            resolved_url = self.session.head(url, allow_redirects=True, timeout=10).url
            
            # ثانياً: استخدام API موثوق
            api_url = "https://api.tikmate.cc/api/download"
            params = {
                'url': resolved_url,
                'token': 'null'  # بعض الخوادم تتطلب هذا
            }
            
            response = self.session.get(api_url, params=params, timeout=15).json()
            
            if response.get('video_no_watermark'):
                return response['video_no_watermark']
            return None
            
        except Exception as e:
            print(f"API Error: {e}")
            return None

async def download_tiktok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    handler = TikTokHandler()

    if "tiktok.com" not in url:
        await update.message.reply_text("❌ يرجى إرسال رابط TikTok صحيح")
        return

    await update.message.chat.send_action("upload_video")

    try:
        video_url = handler.get_no_watermark(url)
        
        if not video_url:
            await update.message.reply_text("❌ تعذر إزالة العلامة المائية. جرب رابطًا آخر أو حاول لاحقًا.")
            return

        # تنزيل الفيديو مباشرة
        response = handler.session.get(video_url, stream=True, timeout=30)
        
        if response.status_code != 200:
            await update.message.reply_text("❌ فشل تنزيل الفيديو")
            return

        await update.message.reply_video(
            video=response.raw,
            caption="✅ تم التنزيل بدون علامة مائية",
            supports_streaming=True
        )

    except Exception as e:
        print(f"Error: {e}")
        await update.message.reply_text("⚠️ حدث خطأ. جرب مرة أخرى أو أرسل رابطًا مختلفًا.")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    keep_alive()

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_tiktok))
    print("✅ البوت يعمل...")
    app.run_polling()
