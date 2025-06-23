import os
import re
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from keep_alive import keep_alive
from urllib.parse import urlparse, parse_qs

BOT_TOKEN = os.getenv("BOT_TOKEN")

# دالة محسنة لحل الروابط المختصرة
def resolve_tiktok_url(url):
    try:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'en-US,en;q=0.9'
        })
        response = session.head(url, allow_redirects=True, timeout=15)
        return response.url
    except Exception as e:
        print(f"Error resolving URL: {e}")
        return url

# دالة لاستخراج معلومات الفيديو باستخدام API متعدد المصادر
def get_tiktok_video_info(url):
    APIs = [
        {
            'url': 'https://api.tiklydown.eu.org/api/download',
            'method': 'POST',
            'payload': {'url': url},
            'video_field': 'video.url'
        },
        {
            'url': 'https://tikwm.com/api/info',
            'method': 'GET',
            'params': {'url': url},
            'video_field': 'data.play'
        },
        {
            'url': 'https://www.tikwm.com/api/',
            'method': 'POST',
            'data': {'url': url},
            'video_field': 'data.wmplay'
        }
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/json'
    }
    
    for api in APIs:
        try:
            if api['method'] == 'POST':
                response = requests.post(
                    api['url'],
                    json=api.get('payload', {}),
                    data=api.get('data', {}),
                    headers=headers,
                    timeout=15
                )
            else:
                response = requests.get(
                    api['url'],
                    params=api.get('params', {}),
                    headers=headers,
                    timeout=15
                )
            
            # التحقق من أن الرد يحتوي على JSON صالح
            data = response.json()
            
            # استخراج رابط الفيديو باستخدام المسار المحدد
            keys = api['video_field'].split('.')
            video_url = data
            for key in keys:
                video_url = video_url.get(key)
                if video_url is None:
                    break
            
            if video_url and video_url.startswith('http'):
                return video_url
                
        except Exception as e:
            print(f"Error with API {api['url']}: {e}")
            continue
    
    return None

async def download_tiktok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    # التحقق من أن الرابط من تيك توك
    if not any(domain in url for domain in ['tiktok.com', 'vm.tiktok.com', 'vt.tiktok.com']):
        await update.message.reply_text("❌ الرابط غير صحيح. يرجى إرسال رابط TikTok فقط.")
        return

    await update.message.chat.send_action("upload_video")

    try:
        # حل الرابط المختصر أولاً
        final_url = resolve_tiktok_url(url)
        print(f"Processing URL: {final_url}")

        # الحصول على رابط الفيديو من أحد APIs
        video_url = get_tiktok_video_info(final_url)
        
        if not video_url:
            await update.message.reply_text("❌ تعذر العثور على الفيديو. قد يكون الرابط غير صحيح أو الخدمة غير متوفرة.")
            return

        # تنزيل الفيديو مباشرة بدون حفظ في ملف
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Referer': 'https://www.tiktok.com/'
        }
        
        with requests.get(video_url, headers=headers, stream=True, timeout=30) as video_response:
            if video_response.status_code != 200:
                await update.message.reply_text("❌ تعذر تنزيل الفيديو")
                return

            # إرسال الفيديو مباشرة من الذاكرة بدون حفظ في ملف
            await update.message.reply_video(
                video=video_response.raw,
                caption="✅ تم التنزيل بنجاح!",
                supports_streaming=True,
                filename="tiktok_video.mp4"
            )

    except Exception as e:
        error_msg = f"⚠️ حدث خطأ: {str(e)}"
        print(error_msg)
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
