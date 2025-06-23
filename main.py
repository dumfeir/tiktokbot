import os
import re
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")

class AdvancedInstaDownloader:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.instagram.com/'
        }
        self.APIS = [
            self._try_ddinstagram,
            self._try_savefrom,
            self._try_snapinsta
        ]

    def _fix_url(self, text):
        """إصلاح جميع مشاكل الروابط"""
        # إزالة المسافات والأخطاء الإملائية
        text = re.sub(r'(https?://[^\s]+)\s+([^\s]+)', r'\1\2', text)
        # تصحيح reel/feel/reeI إلى reel
        text = re.sub(r'/(f[eE]{2}l|ree[iI]|ree[lL])', '/reel', text, flags=re.IGNORECASE)
        # استخراج الرابط النهائي
        match = re.search(r'(https?://(?:www\.)?instagram\.com/reel/[a-zA-Z0-9_-]+(?:/\?[^\s]*)?)', text)
        return match.group(0) if match else None

    def _try_ddinstagram(self, url):
        """أفضل طريقة تعمل حالياً"""
        try:
            dd_url = url.replace('instagram.com', 'ddinstagram.com')
            response = self.session.head(dd_url, allow_redirects=True, timeout=10)
            return response.url if 'video' in response.url else None
        except:
            return None

    def _try_savefrom(self, url):
        """الخيار الثاني"""
        try:
            api_url = "https://api.savefrom.net/api/convert"
            params = {'url': url, 'format': 'mp4'}
            response = self.session.get(api_url, params=params, timeout=15).json()
            return response.get('url')
        except:
            return None

    def _try_snapinsta(self, url):
        """الخيار الثالث"""
        try:
            api_url = "https://snapinsta.app/api/ajaxSearch"
            data = {'q': url}
            response = self.session.post(api_url, data=data, timeout=15).json()
            return response.get('links', [{}])[0].get('url')
        except:
            return None

    def download(self, text):
        """المحاولة مع جميع الواجهات"""
        url = self._fix_url(text)
        if not url:
            return None, "⚠️ لم أتمكن من تحديد رابط الريل الصحيح"

        for api in self.APIS:
            video_url = api(url)
            if video_url:
                return video_url, None
        
        return None, "❌ جميع الخوادم مشغولة، حاول لاحقاً أو أرسل رابطاً مختلفاً"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    downloader = AdvancedInstaDownloader()
    
    video_url, error_msg = downloader.download(update.message.text)
    
    if error_msg:
        await update.message.reply_text(error_msg)
        return

    await update.message.chat.send_action("upload_video")

    try:
        response = downloader.session.get(video_url, stream=True, timeout=30)
        if response.status_code != 200:
            await update.message.reply_text("❌ فشل تحميل الفيديو من الخادم")
            return

        await update.message.reply_video(
            video=response.raw,
            caption="🎉 تم التحميل بنجاح!",
            supports_streaming=True,
            filename="instagram_reel.mp4"
        )
    except Exception as e:
        print(f"Error: {e}")
        await update.message.reply_text("⛔ حدث خطأ غير متوقع")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🚀 البوت يعمل بكل كفاءة...")
    app.run_polling()
