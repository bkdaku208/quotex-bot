import telebot
from flask import Flask
import threading
from attached_assets.key_utils import generate_key, check_key_valid
from attached_assets.valid_pairs import VALID_OTC_PAIRS
import random
from datetime import datetime, timedelta

# Flask Web Server
app = Flask(__name__)

@app.route('/')
def home():
    return "The bot is running!"

def run_server():
    app.run(host='0.0.0.0', port=5000)

# Configuration
TELEGRAM_BOT_TOKEN = "7905942542:AAGpsq3m-nhRSYVSUjoLBYf7PBPco-r17vU"
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Admin Users
ADMIN_USER_IDS = [2053912772, 5052012233]

# User Access Control
user_access = {}
user_last_request = {}

# --- Bot Commands ---

@bot.message_handler(commands=['start', 'intro'])
def send_welcome(message):
    intro_text = (
        "👋 Welcome to the Quotex OTC Signal Bot!\n\n"
        "Start trading on Quotex with my referral link:\n"
        "https://broker-qx.pro/sign-up/?lid=1296187\n\n"
        "Type /help to see available commands."
    )
    bot.reply_to(message, intro_text)

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = (
        "/start - Introduction\n"
        "/genkey 7 or /genkey 30 (admin only) - Generate access key\n"
        "/usekey <yourkey> - Activate your access key\n"
        "/nextsignal - Get your next signal (if you have access)\n"
    )
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['genkey'])
def admin_generate_key(message):
    if message.from_user.id not in ADMIN_USER_IDS:
        bot.reply_to(message, "You are not authorized to generate keys.")
        return
    try:
        duration = int(message.text.split()[1])
        if duration not in [7, 30]:
            bot.reply_to(message, "Duration must be 7 or 30 days.")
            return
        key = generate_key(duration)
        bot.reply_to(message, f"Key generated for {duration} days: `{key}`", parse_mode='Markdown')
    except Exception:
        bot.reply_to(message, "Usage: /genkey 7 or /genkey 30")

@bot.message_handler(commands=['usekey'])
def user_use_key(message):
    try:
        key = message.text.split()[1]
        valid, msg = check_key_valid(key, message.from_user.id)
        if valid:
            user_access[message.from_user.id] = True
            bot.reply_to(message, f"✅ Access granted! {msg}")
        else:
            bot.reply_to(message, f"❌ {msg}")
    except Exception:
        bot.reply_to(message, "Usage: /usekey <yourkey>")

# --- Signal Logic ---

def get_otc_signal():
    pair = random.choice(VALID_OTC_PAIRS)
    direction = random.choice(["CALL", "PUT"])
    confidence = random.randint(70, 95)
    return pair, direction, confidence

def safe_entry_signal(chat_id, pair):
    msg = "🟢 Trade win! You can send feedback on my DM <a href='https://t.me/Zoya_Qt'>@Zoya_Qt</a>"
    try:
        bot.send_message(chat_id, msg, parse_mode='HTML')
    except telebot.apihelper.ApiTelegramException as e:
        print(f"Error sending message: {e}")

@bot.message_handler(commands=['nextsignal'])
def next_signal(message):
    current_time = datetime.now()
    last_request = user_last_request.get(message.from_user.id, None)

    if last_request and (current_time - last_request).seconds < 60:
        bot.reply_to(message, "⏳ Please wait before requesting another signal.")
        return

    if not user_access.get(message.from_user.id):
        bot.reply_to(message, "You do not have access. Please activate your access key using /usekey <yourkey>.")
        return

    user_last_request[message.from_user.id] = current_time

    pair, direction, confidence = get_otc_signal()
    start_time = datetime.now()
    end_time = start_time + timedelta(minutes=1)
    msg = (
        f"📡 *Quotex OTC Signal*\n"
        f"🔸 Pair: *{pair}*\n"
        f"🔸 Direction: *{direction}*\n"
        f"🔸 Confidence: *{confidence}%*\n"
        f"⏱ Trade Start: *{start_time.strftime('%H:%M:%S')}*\n"
        f"⏱ Trade End: *{end_time.strftime('%H:%M:%S')}*"
    )
    bot.send_message(message.chat.id, msg, parse_mode='Markdown')

    threading.Timer(60, safe_entry_signal, args=[message.chat.id, pair]).start()

# --- Main ---
if __name__ == "__main__":
    print("Bot is running...")
    threading.Thread(target=bot.polling, daemon=True).start()
    run_server()
    
