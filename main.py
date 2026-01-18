import telebot
import time
import threading
import requests
import os
from flask import Flask

# --- CONFIGURATION ---
BOT_TOKEN = '8183778698:AAGiOJuiN4ZRT7iEvIQLM3JaHc_tu1EFSWY'  # আপনার টোকেন বসান
CHANNEL_ID = '@big_maruf_official0' # আপনার গ্রুপের লিংক
API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"

# --- SETUP ---
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# --- GLOBAL VARIABLES ---
is_running = False
consecutive_wins = 0
last_processed_period = None

# --- WEB SERVER (RENDER FIX) ---
# এই অংশটি রেন্ডারকে বুঝাবে যে অ্যাপটি লাইভ আছে
@app.route('/')
def home():
    return "Bot is running successfully!"

def run_web_server():
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

# --- API & LOGIC ---
def get_latest_data():
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(API_URL, headers=headers, timeout=10)
        data = response.json()
        if 'data' in data and 'list' in data['data']:
            return data['data']['list']
        return None
    except Exception as e:
        print(f"API Error: {e}")
        return None

def calculate_prediction(history):
    if not history or len(history) < 3:
        return "BIG"

    n1 = int(history[0]['number'])
    n2 = int(history[1]['number'])
    n3 = int(history[2]['number'])

    size1 = "BIG" if n1 >= 5 else "SMALL"
    size2 = "BIG" if n2 >= 5 else "SMALL"
    size3 = "BIG" if n3 >= 5 else "SMALL"

    # Smart Pattern Logic
    if size1 == size2 and size2 == size3:
        return "SMALL" if size1 == "BIG" else "BIG"
    if size1 == size3 and size1 != size2:
        return size2
        
    return "SMALL" if size1 == "BIG" else "BIG"

# --- BOT LOOP ---
def bot_loop():
    global is_running, consecutive_wins, last_processed_period

    while is_running:
        try:
            history = get_latest_data()
            
            if history:
                latest_issue = history[0]
                current_period_num = int(latest_issue['issueNumber'])
                next_period_num = current_period_num + 1
                
                if last_processed_period != next_period_num:
                    prediction = calculate_prediction(history)
                    
                    # ১. প্রেডিকশন মেসেজ
                    msg = (
                        f"🎰 **PREDICTION ALERT** 🎰\n"
                        f"━━━━━━━━━━━━━━━━\n"
                        f"⏰ Period: `{next_period_num}`\n"
                        f"🎯 Bet On: **{prediction}**\n"
                        f"📊 Logic: Smart AI Pattern\n"
                        f"━━━━━━━━━━━━━━━━\n"
                        f"⏳ রেজাল্টের জন্য অপেক্ষা করুন..."
                    )
                    try:
                        bot.send_message(CHANNEL_ID, msg, parse_mode='Markdown')
                    except Exception as e:
                        print(f"Error sending msg: {e}")

                    # ২. অপেক্ষা (৫৫ সেকেন্ড)
                    time.sleep(55) 
                    
                    # ৩. রেজাল্ট চেক
                    new_history = get_latest_data()
                    if new_history:
                        result_issue = new_history[0]
                        if int(result_issue['issueNumber']) == next_period_num:
                            result_num = int(result_issue['number'])
                            real_size = "BIG" if result_num >= 5 else "SMALL"
                            
                            if real_size == prediction:
                                consecutive_wins += 1
                                win_msg = f"✅ **WIN! WIN! WIN!** ✅\nResult: {real_size} ({result_num})"
                                if consecutive_wins >= 3:
                                    win_msg += f"\n🔥 **SUPER WIN STREAK: {consecutive_wins}** 🔥"
                                bot.send_message(CHANNEL_ID, win_msg, parse_mode='Markdown')
                            else:
                                consecutive_wins = 0
                                bot.send_message(CHANNEL_ID, f"❌ **LOSS**\nResult: {real_size} ({result_num})\nNext time recover.", parse_mode='Markdown')
                    
                    last_processed_period = next_period_num
                else:
                    time.sleep(10)
            else:
                time.sleep(5)
        except Exception as e:
            print(f"Loop Error: {e}")
            time.sleep(5)

# --- COMMANDS ---
@bot.message_handler(commands=['start', 'on'])
def start_command(message):
    global is_running
    if str(message.chat.id) == str(CHANNEL_ID): return # গ্রুপে কমান্ড কাজ করবে না, শুধু প্রাইভেট চ্যাটে
    
    if is_running:
        bot.reply_to(message, "⚠️ Bot already running!")
    else:
        is_running = True
        bot.reply_to(message, f"✅ **Bot Started!**\nTarget: {CHANNEL_ID}")
        threading.Thread(target=bot_loop).start()

@bot.message_handler(commands=['stop', 'off'])
def stop_command(message):
    global is_running, consecutive_wins
    if not is_running:
        bot.reply_to(message, "Bot is currently OFF.")
    else:
        is_running = False
        bot.reply_to(message, "🛑 **Bot Stopped.**")
        bot.send_message(CHANNEL_ID, f"🛑 **SESSION CLOSED** 🛑\nThank you for playing!")
        consecutive_wins = 0

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    # ১. ওয়েব সার্ভার চালু করা (Render এর জন্য জরুরি)
    threading.Thread(target=run_web_server).start()
    
    # ২. বট চালু করা
    print("Bot is polling...")
    bot.infinity_polling()
