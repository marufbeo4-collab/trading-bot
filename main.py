import telebot
import time
import threading
import requests
import random
import os
from flask import Flask

# --- CONFIGURATION ---
BOT_TOKEN = '8183778698:AAGiOJuiN4ZRT7iEvIQLM3JaHc_tu1EFSWY'  # <--- আপনার টোকেন বসান
CHANNEL_ID = -1002629495753        # <--- আপনার গ্রুপের আইডি (মাইনাস সহ)
API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"

# --- SETUP ---
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# --- GLOBAL VARIABLES ---
is_running = False
consecutive_wins = 0
last_processed_period = None

# --- WEB SERVER (Render-এর জন্য) ---
@app.route('/')
def home():
    return "Bot is running with HTML Logic!"

def run_web_server():
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

# --- 1. API DATA FETCH ---
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

# --- 2. HTML LOGIC TRANSLATED TO PYTHON ---

def get_color_from_num(n):
    # HTML Logic: 0,2,4,6,8 = RED | 1,3,5,7,9 = GREEN
    # (Note: Usually 0 is Red+Violet, 5 is Green+Violet, but keeping your logic)
    if n in [0, 2, 4, 6, 8]:
        return "🔴 RED"
    return "🟢 GREEN"

def generate_prediction_logic(history):
    # Trend Analysis from History
    if not history:
        target_size = "BIG"
    else:
        # Simple Logic: Follow trend (Zigzag check)
        n1 = int(history[0]['number'])
        n2 = int(history[1]['number'])
        s1 = "BIG" if n1 >= 5 else "SMALL"
        s2 = "BIG" if n2 >= 5 else "SMALL"
        
        if s1 != s2:
            target_size = s1 # Zigzag pattern
        else:
            target_size = "SMALL" if s1 == "BIG" else "BIG" # Cut trend

    # Generate 3 Random Numbers that match the Target Size (Like HTML Code)
    nums = []
    while len(nums) < 3:
        if len(nums) < 2:
            # Force numbers to match target
            if target_size == "BIG":
                nums.append(random.randint(5, 9))
            else:
                nums.append(random.randint(0, 4))
        else:
            # Last number random
            nums.append(random.randint(0, 9))
    
    # Shuffle for realism
    random.shuffle(nums)
    
    # Calculate Final Logic from the 3 numbers
    big_count = sum(1 for n in nums if n >= 5)
    final_size = "BIG" if big_count >= 2 else "SMALL"
    
    red_count = sum(1 for n in nums if n in [0, 2, 4, 6, 8])
    final_color = "🔴 RED" if red_count >= 2 else "🟢 GREEN"
    
    return final_size, final_color, nums

# --- 3. MAIN BOT LOOP ---
def bot_loop():
    global is_running, consecutive_wins, last_processed_period

    while is_running:
        try:
            history = get_latest_data()
            
            if history:
                latest_issue = history[0]
                current_period_num = int(latest_issue['issueNumber'])
                next_period_num = current_period_num + 1
                
                # Check if we need to predict for next round
                if last_processed_period != next_period_num:
                    
                    # Generate Prediction
                    pred_size, pred_color, pred_nums = generate_prediction_logic(history)
                    
                    # Format Message (Detailed info as requested)
                    msg = (
                        f"🔥 **PREMIUM SIGNAL** 🔥\n"
                        f"➖➖➖➖➖➖➖➖➖➖\n"
                        f"📅 **Period:** `{next_period_num}`\n"
                        f"🎰 **Prediction:** **{pred_size}**\n"
                        f"🎨 **Color:** {pred_color}\n"
                        f"🔢 **Lucky Nums:** `{pred_nums[0]}` - `{pred_nums[1]}` - `{pred_nums[2]}`\n"
                        f"➖➖➖➖➖➖➖➖➖➖\n"
                        f"⏳ **Waiting for result...**"
                    )
                    
                    try:
                        bot.send_message(CHANNEL_ID, msg, parse_mode='Markdown')
                        print(f"Sent signal for {next_period_num}")
                    except Exception as e:
                        print(f"Msg Error: {e}")

                    # Wait for Result (approx 55 seconds)
                    time.sleep(55) 
                    
                    # Check Win/Loss
                    new_history = get_latest_data()
                    if new_history:
                        result_issue = new_history[0]
                        if int(result_issue['issueNumber']) == next_period_num:
                            res_num = int(result_issue['number'])
                            real_size = "BIG" if res_num >= 5 else "SMALL"
                            real_color = get_color_from_num(res_num)
                            
                            if real_size == pred_size:
                                consecutive_wins += 1
                                win_msg = (
                                    f"✅ **WIN Successful!**\n"
                                    f"🏆 Result: **{real_size}** ({res_num})\n"
                                    f"🔥 Streak: {consecutive_wins} Wins"
                                )
                                bot.send_message(CHANNEL_ID, win_msg, parse_mode='Markdown')
                            else:
                                consecutive_wins = 0
                                loss_msg = (
                                    f"❌ **Loss...**\n"
                                    f"Result: {real_size} ({res_num})\n"
                                    f"Use 3X Plan for Next."
                                )
                                bot.send_message(CHANNEL_ID, loss_msg, parse_mode='Markdown')
                    
                    last_processed_period = next_period_num
                else:
                    time.sleep(5)
            else:
                print("API Error or Waiting...")
                time.sleep(5)
        except Exception as e:
            print(f"Loop Exception: {e}")
            time.sleep(5)

# --- COMMANDS ---

@bot.message_handler(commands=['start', 'on'])
def start_command(message):
    global is_running
    # Only allow admin in private chat to start
    if str(message.chat.id) == str(CHANNEL_ID): return 
    
    if is_running:
        bot.reply_to(message, "⚠️ Bot is already running!")
    else:
        is_running = True
        bot.reply_to(message, "✅ **Bot Started!**\nSending signals with HTML Logic...")
        threading.Thread(target=bot_loop).start()

@bot.message_handler(commands=['stop', 'off'])
def stop_command(message):
    global is_running, consecutive_wins
    if not is_running:
        bot.reply_to(message, "Bot is currently OFF.")
    else:
        is_running = False
        bot.reply_to(message, "🛑 **Bot Stopped.**")
        bot.send_message(CHANNEL_ID, "🛑 **SESSION ENDED** 🛑\nNext Session Coming Soon!")
        consecutive_wins = 0

# --- RUN ---
if __name__ == "__main__":
    threading.Thread(target=run_web_server).start()
    bot.infinity_polling()
