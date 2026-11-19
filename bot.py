import os
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import telebot
from google import genai
from playwright.sync_api import sync_playwright

# 1. امسح الكلام العربي اللي بين علامات التنصيص وحط مفاتيحك الجديدة هنا
TELEGRAM_TOKEN = "9258513622:AAHXSvW8ZsQ2bPiOGiIZcxNlMGBNrKWUWR8"
GEMINI_API_KEY = "AQ.Ab8RN6LUbBabqKdUajYuYFhdbQkJ-IWD30tnbzUyd0MCQX3wng"

bot = telebot.TeleBot(TELEGRAM_TOKEN)
ai_client = genai.Client(api_key=GEMINI_API_KEY)

class KeepAliveHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), KeepAliveHandler)
    server.serve_forever()

def ask_ai(image_path):
    uploaded = ai_client.files.upload(file=image_path)
    prompt = "هذه صورة سؤال برمجة من منصة Qureo. اكتب الإجابة الصحيحة أو الكود المطلوب فقط بدون شرح."
    res = ai_client.models.generate_content(model='gemini-2.5-flash', contents=[uploaded, prompt])
    return res.text.strip()

@bot.message_handler(commands=['start'])
def welcome(msg):
    bot.reply_to(msg, "أهلاً بك! البوت شغال 24 ساعة.\nأرسل بياناتك لحل السؤال الحالي هكذا:\n/solve اليوزر الباسورد")

@bot.message_handler(commands=['solve'])
def solve_task(msg):
    try:
        _, user, pwd = msg.text.split()
        bot.reply_to(msg, "⏳ جاري فتح منصة كيريو وقراءة السؤال...")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("https://qureo.education")
            
            page.locator('input').first.fill(user)
            page.locator('input').nth(1).fill(pwd)
            page.locator('button').first.click()
            
            time.sleep(5)
            page.screenshot(path="q.png")
            answer = ask_ai("q.png")
            browser.close()
            
        bot.reply_to(msg, f"✅ تم الدخول! إجابة السؤال الحالي هي:\n\n{answer}")
    except Exception as e:
        bot.reply_to(msg, f"❌ حدث خطأ: {e}")

if __name__ == "__main__":
    threading.Thread(target=run_web_server, daemon=True).start()
    print("البوت يعمل الآن...")
    bot.infinity_polling()
