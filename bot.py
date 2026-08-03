import os
import logging
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# Logging Setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Flask Server (Koyeb/Render 24/7 Uptime)
app = Flask('')

@app.route('/')
def home():
    return "Bot is running fine!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

# Global Data Structure (Group-Aware Data Storage)
# Format: { chat_id: { user_id: { "name": str, "photos": int, "links": int } } }
group_data = {}

def get_group_db(chat_id):
    """ഓരോ ഗ്രൂപ്പിനും പ്രത്യേകമായി ഡാറ്റ സൂക്ഷിക്കാനുള്ള ഫങ്ഷൻ"""
    if chat_id not in group_data:
        group_data[chat_id] = {}
    return group_data[chat_id]

# 1. Message Tracker (Photos & Links Counting)
async def track_activity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat or update.effective_chat.type not in ['group', 'supergroup']:
        return

    chat_id = update.effective_chat.id
    user = update.effective_user
    if not user or user.is_bot:
        return

    db = get_group_db(chat_id)
    user_id = user.id

    if user_id not in db:
        db[user_id] = {
            "name": user.first_name,
            "photos": 0,
            "links": 0
        }
    
    # Update user's display name if changed
    db[user_id]["name"] = user.first_name

    # Check for Photo
    if update.message.photo:
        db[user_id]["photos"] += 1

    # Check for Link/URL
    if update.message.text or update.message.caption:
        text = update.message.text or update.message.caption
        entities = update.message.entities or update.message.caption_entities
        if entities:
            for entity in entities:
                if entity.type in ["url", "text_link"]:
                    db[user_id]["links"] += 1
                    break

# 2. Photo Leaderboard Command (/photolb)
async def photo_lb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    db = get_group_db(chat_id)

    sorted_users = sorted(
        db.items(),
        key=lambda x: x[1]["photos"],
        reverse=True
    )[:5]

    text = "📸 **Top Photo Shareers** 📸\n\n"
    has_data = False
    
    for rank, (u_id, data) in enumerate(sorted_users, 1):
        if data["photos"] > 0:
            text += f"{rank}. **{data['name']}**: {data['photos']} photos\n"
            has_data = True

    if not has_data:
        text += "ഇതുവരെ ആരും ഫോട്ടോകൾ അയച്ചിട്ടില്ല!"

    await update.message.reply_text(text, parse_mode="Markdown")

# 3. Link Leaderboard Command (/linklb)
async def link_lb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    db = get_group_db(chat_id)

    sorted_users = sorted(
        db.items(),
        key=lambda x: x[1]["links"],
        reverse=True
    )[:5]

    text = "🔗 **Top Link Shareers** 🔗\n\n"
    has_data = False

    for rank, (u_id, data) in enumerate(sorted_users, 1):
        if data["links"] > 0:
            text += f"{rank}. **{data['name']}**: {data['links']} links\n"
            has_data = True

    if not has_data:
        text += "ഇതുവരെ ആരും ലിങ്കുകൾ അയച്ചിട്ടില്ല!"

    await update.message.reply_text(text, parse_mode="Markdown")

# 4. Helper Function: Generate Full Leaderboard Text
def build_combined_leaderboard(chat_id):
    db = get_group_db(chat_id)

    # Top Photos
    photo_sorted = sorted(db.items(), key=lambda x: x[1]["photos"], reverse=True)[:5]
    photo_text = "📸 **Top Photo Shareers**\n"
    p_has = False
    for rank, (u_id, data) in enumerate(photo_sorted, 1):
        if data["photos"] > 0:
            photo_text += f"{rank}. {data['name']}: {data['photos']}\n"
            p_has = True
    if not p_has:
        photo_text += "വിവരങ്ങൾ ഒന്നും ലഭ്യമല്ല\n"

    # Top Links
    link_sorted = sorted(db.items(), key=lambda x: x[1]["links"], reverse=True)[:5]
    link_text = "\n🔗 **Top Link Shareers**\n"
    l_has = False
    for rank, (u_id, data) in enumerate(link_sorted, 1):
        if data["links"] > 0:
            link_text += f"{rank}. {data['name']}: {data['links']}\n"
            l_has = True
    if not l_has:
        link_text += "വിവരങ്ങൾ ഒന്നും ലഭ്യമല്ല\n"

    return f"📊 **ഓട്ടോമാറ്റിക് ലീഡർബോർഡ്** 📊\n\n{photo_text}{link_text}"

# 5. Delete Message Callback
async def delete_leaderboard_msg(context: ContextTypes.DEFAULT_TYPE):
    job_data = context.job.data
    chat_id = job_data["chat_id"]
    msg_id = job_data["message_id"]

    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
    except Exception as e:
        logging.warning(f"Message delete ചെയ്യാൻ പറ്റിയില്ല: {e}")

# 6. Auto Leaderboard Sender Task
async def auto_send_leaderboard(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    text = build_combined_leaderboard(chat_id)

    try:
        msg = await context.bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
        
        # 1 മിനിറ്റ് (60 സെക്കൻഡ്) കഴിഞ്ഞാൽ ഡിലീറ്റ് ആക്കാൻ ഷെഡ്യൂൾ ചെയ്യുന്നു
        context.job_queue.run_once(
            delete_leaderboard_msg,
            60,
            data={"chat_id": chat_id, "message_id": msg.message_id},
            name=f"delete_{chat_id}_{msg.message_id}"
        )
    except Exception as e:
        logging.error(f"Error sending auto leaderboard to {chat_id}: {e}")

# 7. Toggle Auto Leaderboard (/autolb on / off)
async def toggle_autolb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    # അഡ്മിൻ പെർമിഷൻ പരിശോധന
    user_status = (await context.bot.get_chat_member(chat_id, update.effective_user.id)).status
    if user_status not in ['administrator', 'creator']:
        await update.message.reply_text("⚠️ ഈ കമാൻഡ് ഉപയോഗിക്കാൻ അഡ്മിൻ പെർമിഷൻ വേണം!")
        return

    if not context.args:
        await update.message.reply_text("ഉപയോഗിക്കേണ്ട രീതി: `/autolb on` അല്ലെങ്കിൽ `/autolb off`", parse_mode="Markdown")
        return

    status = context.args[0].lower()
    # ഓരോ ഗ്രൂപ്പിനും വെവ്വേറെ Job Name കൊടുക്കുന്നു
    job_name = f"autolb_{chat_id}"
    current_jobs = context.job_queue.get_jobs_by_name(job_name)

    if status == "on":
        if current_jobs:
            await update.message.reply_text("✅ ഈ ഗ്രൂപ്പിൽ ഓട്ടോമാറ്റിക് ലീഡർബോർഡ് ഇതിനകം ON ആണ്.")
            return

        # 5 മിനിറ്റ് (300 സെക്കൻഡ്) ഇടവേളയിൽ ഈ ഗ്രൂപ്പിൽ മാത്രം റൺ ചെയ്യുന്നു
        context.job_queue.run_repeating(
            auto_send_leaderboard,
            interval=300,  # <-- 5 മിനിറ്റ് (300 സെക്കൻഡ്)
            first=10,
            chat_id=chat_id,
            name=job_name
        )
        await update.message.reply_text("🚀 ഓട്ടോ ലീഡർബോർഡ് ON ആക്കി! ഇനി മുതൽ **ഓരോ 5 മിനിറ്റിലും** ലീഡർബോർഡ് വരികയും 1 മിനിറ്റിനകം തനിയെ ഡിലീറ്റ് ആവുകയും ചെയ്യും.")

    elif status == "off":
        if not current_jobs:
            await update.message.reply_text("⚠️ ഈ ഗ്രൂപ്പിൽ ഓട്ടോ ലീഡർബോർഡ് ഇതിനകം OFF ആണ്.")
            return

        for job in current_jobs:
            job.schedule_removal()
        await update.message.reply_text("🛑 ഓട്ടോ ലീഡർബോർഡ് OFF ആക്കി.")
    else:
        await update.message.reply_text("തെറ്റായ ഓപ്ഷൻ! `/autolb on` അല്ലെങ്കിൽ `/autolb off` എന്ന് ഉപയോഗിക്കുക.")

# Main Bot Setup
def main():
    # Keep Alive Server Start
    keep_alive()

    # Bot Token Get from Environment
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        print("Error: BOT_TOKEN Environment Variable കണ്ടുപിടിക്കാൻ പറ്റിയില്ല!")
        return

    # Application Setup
    application = Application.builder().token(TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler("photolb", photo_lb))
    application.add_handler(CommandHandler("linklb", link_lb))
    application.add_handler(CommandHandler("autolb", toggle_autolb))
    
    # Track photo and link messages
    application.add_handler(
        MessageHandler(filters.PHOTO | filters.TEXT | filters.ENTITY, track_activity)
    )

    # Start the Bot
    print("Bot is starting...")
    application.run_polling()

if __name__ == "__main__":
    main()