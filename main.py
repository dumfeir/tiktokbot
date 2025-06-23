import os
import re
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from keep_alive import keep_alive
from urllib.parse import urlparse, parse_qs

BOT_TOKEN = os.getenv("BOT_TOKEN")

# دالة محسنة لاستخراج ID الفيديو
def extract_video_id(url):
    try:
        # حل أي روابط مختصرة أولاً
        final_url = resolve_redirect(url)
        
        # التحقق من أن الرابط من تيك توك
        if "tiktok.com" not in final_url:
            return None
            
        # الأنماط الشائعة لروابط تيك توك
        patterns = [
            r"/video/(\d+)",  # الروابط العادية
            r"@[\w.]+/video/(\d+)",  # روابط مع @username
            r"/(\d+)(?:\?|$)",  # الروابط الرقمية فقط
            r"item_id=(\d+)"  # روابط معلمة
        ]
        
        for pattern in patterns:
            match = re.search(pattern, final_url)
            if match:
                return match.group(1)
                
        # إذا لم ينجح أي من الأنماط السابقة، جرب استخراج من query parameters
        parsed = urlparse(final_url)
        params = parse_qs(parsed.query)
        if 'item_id' in params:
            return params['item_id'][0]
            
        return None
    except Exception as e:
        print(f"Error extracting video ID: {e}")
        return None

# دالة محسنة لحل الروابط المختصرة
def resolve_redirect(url):
    try:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response = session.head(url, allow_redirects=True, timeout=10)
        return response.url
    except Exception as e:
        print(f"Error resolving URL: {e}")
        return url

async def download_tiktok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if not any(domain in url for domain in ['tiktok.com', 'vm.tiktok.com', 'vt.tiktok.com']):
        await update.message.reply_text("❌ الرابط غير صحيح. يرجى إرسال رابط TikTok فقط.")
        return

    await update.message.chat.send_action("upload_video")

    try:
        # حل الرابط المختصر
        final_url = resolve_redirect(url)
        print(f"Final URL: {final_url}")  # لأغراض debugging

        # استخدام API موثوق
        api_url = "https://api.tiklydown.eu.org/api/download"
        payload = {
            "url": final_url
        }
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/json"
        }

        response = requests.post(api_url, json=payload, headers=headers)
        
        # تحقق من أن الرد يحتوي على JSON صالح
        try:
            data = response.json()
        except ValueError:
            await update.message.reply_text("❌ حصلت على رد غير متوقع من الخادم. يرجى المحاولة لاحقاً.")
            return

        if not data.get("success"):
            error_msg = data.get("message", "تعذر الحصول على الفيديو")
            await update.message.reply_text(f"❌ {error_msg}")
            return

        video_url = data["video"]["url"]
        video_response = requests.get(video_url, stream=True, headers=headers)
        
        if video_response.status_code != 200:
            await update.message.reply_text("❌ تعذر تنزيل الفيديو")
            return

        # حفظ الفيديو مؤقتاً
        temp_file = "temp_video.mp4"
        with open(temp_file, "wb") as f:
            for chunk in video_response.iter_content(chunk_size=8192):
                f.write(chunk)

        # إرسال الفيديو
        await update.message.reply_video(
            video=open(temp_file, "rb"),
            caption="✅ تم التنزيل بنجاح!",
            supports_streaming=True
        )

        # حذف الملف المؤقت
        os.remove(temp_file)

    except Exception as e:
        error_msg = f"⚠️ حدث خطأ: {str(e)}"
        print(error_msg)  # لأغراض debugging
        await update.message.reply_text("❌ حدث خطأ أثناء معالجة طلبك. يرجى المحاولة لاحقاً.")

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
