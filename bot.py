import json
import random
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# তোমার টোকেন ও অ্যাডমিন ইউজারনেম
BOT_TOKEN = "123456789:AAE4wMQuGnx-Z39NGHkii46JNVE-phAxgVo"
ADMIN_USERNAME = "jihad54041"

# ফাইল
USERS_FILE = "users.json"
UK_FILE = "uk_ips.txt"
USA_FILE = "usa_ips.txt"

# ইউজার ডাটা লোড/সেভ
def load_users():
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

# IP লোড
def get_ip(country):
    file_name = UK_FILE if country == "uk" else USA_FILE
    try:
        with open(file_name, "r") as f:
            lines = f.read().splitlines()
        if not lines:
            return None
        ip = lines[0]
        with open(file_name, "w") as f:
            f.write("\n".join(lines[1:]))  # Remove used IP
        return ip
    except:
        return None

# ✅ /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.effective_user.username
    users = load_users()

    if username not in users:
        await update.message.reply_text("❌ আপনি অনুমোদিত ইউজার নন। অনুগ্রহ করে অ্যাডমিনের সাথে যোগাযোগ করুন।")
        return

    # মেয়াদ শেষ চেক
    expires_on = datetime.strptime(users[username]['expires_on'], "%Y-%m-%d")
    if datetime.now() > expires_on:
        await update.message.reply_text("⏳ আপনার মেয়াদ শেষ হয়ে গেছে।")
        return

    # তারিখ বদলেছে কিনা চেক করে daily_limit রিসেট করো
    if users[username]['last_used'] != datetime.now().strftime("%Y-%m-%d"):
        users[username]['daily_limit'] = 0
        users[username]['last_used'] = datetime.now().strftime("%Y-%m-%d")
        save_users(users)

    # বাটন
    keyboard = [
        [InlineKeyboardButton("🇬🇧 UK IP", callback_data="get_uk")],
        [InlineKeyboardButton("🇺🇸 USA IP", callback_data="get_usa")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📡 কোন দেশের IP নিতে চান?", reply_markup=reply_markup)

# ✅ /adduser
async def add_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender = update.effective_user.username
    if sender != ADMIN_USERNAME:
        await update.message.reply_text("❌ আপনি অ্যাডমিন নন।")
        return

    if len(context.args) != 1:
        await update.message.reply_text("⚠️ সঠিক ব্যবহার: /adduser username")
        return

    new_user = context.args[0].replace("@", "")
    users = load_users()

    if new_user in users:
        await update.message.reply_text(f"✅ @{new_user} আগে থেকেই যুক্ত আছে।")
        return

    users[new_user] = {
        "added_on": datetime.now().strftime("%Y-%m-%d"),
        "expires_on": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
        "daily_limit": 0,
        "last_used": "",
        "used_ips": []
    }
    save_users(users)
    await update.message.reply_text(f"🎉 @{new_user} কে সফলভাবে অ্যাড করা হয়েছে!")

# ✅ /myinfo
async def myinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.effective_user.username
    users = load_users()

    if username not in users:
        await update.message.reply_text("❌ আপনি অনুমোদিত নন।")
        return

    user = users[username]
    await update.message.reply_text(
        f"👤 ইউজার: @{username}\n"
        f"📅 মেয়াদ শেষ: {user['expires_on']}\n"
        f"📈 আজকের ব্যবহার: {user['daily_limit']} / 10"
    )

# ✅ বাটন হ্যান্ডলার (IP দেওয়া)
async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    username = query.from_user.username
    users = load_users()

    if username not in users:
        await query.edit_message_text("❌ আপনি অনুমোদিত নন।")
        return

    user = users[username]

    # মেয়াদ চেক
    if datetime.now() > datetime.strptime(user['expires_on'], "%Y-%m-%d"):
        await query.edit_message_text("⏳ আপনার সার্ভিস মেয়াদ শেষ হয়েছে।")
        return

    # লিমিট চেক
    if user['last_used'] != datetime.now().strftime("%Y-%m-%d"):
        user['daily_limit'] = 0
        user['last_used'] = datetime.now().strftime("%Y-%m-%d")

    if user['daily_limit'] >= 10:
        await query.edit_message_text("🚫 আজকের লিমিট শেষ। কাল আবার চেষ্টা করুন।")
        return

    country = "uk" if query.data == "get_uk" else "usa"
    ip = get_ip(country)

    if not ip:
        await query.edit_message_text("❌ কোনো IP আর বাকি নেই।")
        return

    user['daily_limit'] += 1
    user['used_ips'].append(ip)
    save_users(users)

    await query.edit_message_text(f"✅ আপনার {country.upper()} IP:\n`{ip}`", parse_mode="Markdown")

# ✅ Bot Run
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("adduser", add_user))
    app.add_handler(CommandHandler("myinfo", myinfo))
    app.add_handler(CallbackQueryHandler(handle_button))

    print("🚀 Bot is running...")
    app.run_polling()

