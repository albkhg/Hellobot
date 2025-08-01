import telebot
from telebot import types

API_TOKEN = '8181945500:AAHVOMstYLfh_quo2VQwgfn4TtXpfnqMbTI'
GROUP_LINK = 'https://t.me/+ZJXacWU8fX8wMGJk'
ADMIN_ID = 7775019590  # ID e adminit

bot = telebot.TeleBot(API_TOKEN)
solved_users = set()
all_users = set()

challenges = [
    {
        "question": "🔐 Fix the following BruteForce Python snippet:\n\n```python\nfor i in range(1000):\n    if password == str(i):\n        print(\"Access Denied\")\n```",
        "options": ["Change 'Denied' to 'Granted'", "Use while instead of for", "Add hash(password)"],
        "correct": 0
    },
    {
        "question": "🌐 DDoS protection bypass simulation. What's the fix?\n\n```python\nimport socket\nwhile True:\n    socket.create_connection(('target.com', 80))\n```",
        "options": ["Add sleep", "Use threading", "Limit requests"],
        "correct": 2
    },
    {
        "question": "🛡️ What's the fix for this XSS?\n\n```html\n<input value='{{ user_input }}'>\n```",
        "options": ["Use innerHTML", "Escape input", "Add alert()"],
        "correct": 1
    }
]

@bot.message_handler(commands=['start'])
def send_welcome(message):
    all_users.add(message.chat.id)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🧠 Solve CAPTCHA", callback_data="start_captcha"))
    bot.send_message(message.chat.id, "Welcome! Click below to solve a hacker-level CAPTCHA to join the group.", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "start_captcha")
def send_challenge(call):
    if call.message.chat.id in solved_users:
        bot.send_message(call.message.chat.id, "✅ You already solved the CAPTCHA!")
        return

    challenge = challenges[call.message.chat.id % len(challenges)]  # Pick based on user ID for consistency
    markup = types.InlineKeyboardMarkup()
    for i, opt in enumerate(challenge["options"]):
        markup.add(types.InlineKeyboardButton(opt, callback_data=f"answer_{i}_{challenges.index(challenge)}"))
    bot.send_message(call.message.chat.id, challenge["question"], reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("answer_"))
def handle_answer(call):
    _, selected, ch_index = call.data.split("_")
    selected = int(selected)
    ch_index = int(ch_index)
    challenge = challenges[ch_index]

    if selected == challenge["correct"]:
        if call.message.chat.id not in solved_users:
            solved_users.add(call.message.chat.id)
        bot.send_message(call.message.chat.id, f"🎉 Correct! Here's the group link:\n{GROUP_LINK}")
    else:
        bot.send_message(call.message.chat.id, "❌ Wrong answer. Try again with /start")

@bot.message_handler(commands=['stats'])
def stats(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, f"📊 Stats:\n- Total Users: {len(all_users)}\n- Solved CAPTCHA: {len(solved_users)}")
    else:
        bot.send_message(message.chat.id, "⛔ You are not authorized.")

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "🚫 You are not authorized to use this command.")
        return
    if message.reply_to_message:
        for uid in all_users:
            try:
                bot.copy_message(uid, message.chat.id, message.reply_to_message.message_id)
            except:
                continue
        bot.send_message(message.chat.id, "📢 Broadcast sent.")
    else:
        bot.send_message(message.chat.id, "📌 Reply to a message with /broadcast to send it to all users.")

print("[+] Bot is running...")
bot.infinity_polling()
                         
