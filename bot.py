import asyncio
import re
from threading import Thread
from flask import Flask
from telegram import Update, ChatPermissions
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Flask വെബ് സെർവർ സെറ്റപ്പ്
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive!"

def run_flask():
    # Render നൽകുന്ന പോർട്ടിൽ സെർവർ റൺ ചെയ്യുന്നു
    app.run(host='0.0.0.0', port=8080)

# നിങ്ങളുടെ ബോട്ട് ടോക്കൺ ഇവിടെ നൽകുക
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
LINK_REGEX = re.compile(r'https?://\S+|www\.\S+')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ബോട്ട് ആക്ടീവ് ആണ്!")

async def delete_warning(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    try:
        await context.bot.delete_message(chat_id=job.chat_id, message_id=job.data)
    except Exception as e:
        print(f"Error deleting message: {e}")

async def filter_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    chat = update.effective_chat
    user = update.effective_user

    if chat.type not in ["group", "supergroup"]:
        return
    if user.is_bot or (message.text and LINK_REGEX.search(message.text)):
        return

    try:
        await message.delete()
        mute_permissions = ChatPermissions(can_send_messages=False)
        await chat.restrict_member(user_id=user.id, permissions=mute_permissions)

        warning_msg = await context.bot.send_message(
            chat_id=chat.id,
            text=f"⚠️ {user.mention_html()}, ഈ ഗ്രൂപ്പിൽ ലിങ്കുകൾ മാത്രമേ അനുവദിക്കൂ!",
            parse_mode="HTML"
        )

        context.job_queue.run_once(
            delete_warning, 
            when=60, 
            chat_id=chat.id, 
            data=warning_msg.message_id
        )
    except Exception as e:
        print(f"Error: {e}")

def main():
    # വെബ് സെർവർ ഒരു പ്രത്യേക ത്രെഡിൽ സ്റ്റാർട്ട് ചെയ്യുന്നു
    Thread(target=run_flask).start()

    # ബോട്ട് സ്റ്റാർട്ട് ചെയ്യുന്നു
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, filter_messages))
    
    print("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()