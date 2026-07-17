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
    app.run(host='0.0.0.0', port=8080)

# നിങ്ങളുടെ ബോട്ട് ടോക്കൺ
BOT_TOKEN = "8673412670:AAFW2QTdkHH_LxecEzJNE-SkflJZe1X8Y0g"
LINK_REGEX = re.compile(r'https?://\S+|www\.\S+')

# ഫീച്ചറുകൾ സേവ് ചെയ്യാനുള്ള ഗ്ലോബൽ വേരിയബിളുകൾ
welcome_enabled = {}  # ഓരോ ഗ്രൂപ്പിലെയും സ്റ്റാറ്റസ് അറിയാൻ (True/False)
last_welcome_messages = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ബോട്ട് ആക്ടീവ് ആണ്!")

async def is_admin(update: Update) -> bool:
    """മെസ്സേജ് അയച്ചത് അഡ്മിൻ ആണോ എന്ന് പരിശോധിക്കുന്നു"""
    chat = update.effective_chat
    user = update.effective_user
    if chat.type in ["group", "supergroup"]:
        member = await chat.get_member(user.id)
        return member.status in ["administrator", "creator"]
    return False

async def toggle_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/new on അല്ലെങ്കിൽ /new off കമാൻഡുകൾ കൈകാര്യം ചെയ്യുന്നു"""
    chat_id = update.effective_chat.id
    
    # അഡ്മിൻ ആണോ എന്ന് നോക്കുന്നു
    if not await is_admin(update):
        await update.message.reply_text("❌ ഈ കമാൻഡ് ഉപയോഗിക്കാൻ നിങ്ങൾക്ക് അഡ്മിൻ പവർ വേണം.")
        return

    command_args = context.args
    if not command_args:
        await update.message.reply_text("ഉപയോഗിക്കേണ്ട വിധം: `/new on` അല്ലെങ്കിൽ `/new off`")
        return

    action = command_args[0].lower()
    if action == "on":
        welcome_enabled[chat_id] = True
        await update.message.reply_text("✅ പുതിയ യൂസർമാർ വരുമ്പോൾ നിയമങ്ങൾ ഓർമ്മിപ്പിക്കുന്ന ഫീച്ചർ ഓണാക്കി! (2 മിനിറ്റിൽ ഡിലീറ്റ് ആകും)")
    elif action == "off":
        welcome_enabled[chat_id] = False
        await update.message.reply_text("❌ വെൽക്കം ഫീച്ചർ ഓഫാക്കി.")
    else:
        await update.message.reply_text("തെറ്റായ കമാൻഡ്! `/new on` അല്ലെങ്കിൽ `/new off` എന്ന് ഉപയോഗിക്കുക.")

async def delete_warning(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    try:
        await context.bot.delete_message(chat_id=job.chat_id, message_id=job.data)
    except Exception as e:
        print(f"Error deleting message: {e}")

async def handle_everything(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message:
        return

    chat = update.effective_chat
    user = update.effective_user

    if chat.type not in ["group", "supergroup"]:
        return
    if user.is_bot:
        return

    # --- 1. പുതിയ മെമ്പർമാർ ഗ്രൂപ്പിൽ ജോയിൻ ചെയ്യുമ്പോൾ ---
    if message.new_chat_members:
        # വെൽക്കം ഫീച്ചർ ഓൺ ആണെങ്കിൽ മാത്രം പ്രവർത്തിക്കും (ഡിഫോൾട്ട് ആയി ഓൺ ആയിരിക്കില്ല, /new on അടിക്കണം)
        if welcome_enabled.get(chat.id, False):
            for new_member in message.new_chat_members:
                if new_member.is_bot:
                    continue

                # പഴയ വെൽക്കം മെസ്സേജ് ഉണ്ടെങ്കിൽ കളയുന്നു
                if chat.id in last_welcome_messages:
                    try:
                        await context.bot.delete_message(chat_id=chat.id, message_id=last_welcome_messages[chat.id])
                    except Exception as e:
                        print(f"Error deleting previous welcome message: {e}")

                welcome_text = (
                    f"👋 ഹലോ {new_member.mention_html()},\n\n"
                    f"ഈ ഗ്രൂപ്പിലേക്ക് സ്വാഗതം! <b>ഗ്രൂപ്പിൽ ലിങ്കുകൾ (Links) മാത്രമേ അനുവദിക്കൂ.</b>\n"
                    f"ലിങ്ക് അല്ലാത്ത മെസ്സേജുകൾ അയച്ചാൽ ബോട്ട് അത് ഓട്ടോമാറ്റിക് ആയി ഡിലീറ്റ് ചെയ്യുകയും നിങ്ങളെ മ്യൂട്ട് ചെയ്യുകയും ചെയ്യും."
                )
                
                try:
                    welcome_msg = await context.bot.send_message(
                        chat_id=chat.id,
                        text=welcome_text,
                        parse_mode="HTML"
                    )
                    last_welcome_messages[chat.id] = welcome_msg.message_id

                    # കൃത്യം 2 മിനിറ്റിന് ശേഷം (2 * 60 = 120 സെക്കൻഡ്) ഡിലീറ്റ് ചെയ്യാൻ ഷെഡ്യൂൾ ചെയ്യുന്നു
                    context.job_queue.run_once(
                        delete_warning,
                        when=120,
                        chat_id=chat.id,
                        data=welcome_msg.message_id
                    )
                except Exception as e:
                    print(f"Error sending welcome message: {e}")
        return

    # അഡ്മിൻമാർ അയക്കുന്ന സാധാരണ മെസ്സേജുകൾ ബോട്ട് ഫിൽട്ടർ ചെയ്യില്ല
    if await is_admin(update):
        return

    # --- 2. ലിങ്ക് ഫിൽട്ടറിംഗ് ലോജിക് (സാധാരണ മെമ്പർമാർക്ക്) ---
    has_link = message.text and LINK_REGEX.search(message.text)

    try:
        if has_link:
            # ലിങ്ക് 15 മിനിറ്റ് (900 സെക്കൻഡ്) കഴിഞ്ഞാൽ ഡിലീറ്റ് ചെയ്യും
            context.job_queue.run_once(
                delete_warning, 
                when=900, 
                chat_id=chat.id, 
                data=message.message_id
            )
            return

        # ലിങ്ക് അല്ലാത്തത് അപ്പോൾത്തന്നെ ഡിലീറ്റ് ചെയ്യുന്നു
        await message.delete()

        # യൂസറെ മ്യൂട്ട് ചെയ്യുന്നു
        mute_permissions = ChatPermissions(can_send_messages=False)
        await chat.restrict_member(user_id=user.id, permissions=mute_permissions)

        # വാണിംഗ് മെസ്സേജ് നൽകുന്നു
        warning_msg = await context.bot.send_message(
            chat_id=chat.id,
            text=f"⚠️ {user.mention_html()}, ഈ ഗ്രൂപ്പിൽ ലിങ്കുകൾ മാത്രമേ അനുവദിക്കൂ! നിങ്ങളുടെ മെസ്സേജ് ഡിലീറ്റ് ചെയ്ത് നിങ്ങളെ മ്യൂട്ട് ചെയ്തിരിക്കുന്നു.",
            parse_mode="HTML"
        )

        # 1 മിനിറ്റിന് ശേഷം വാണിംഗ് ഡിലീറ്റ് ചെയ്യുന്നു
        context.job_queue.run_once(
            delete_warning, 
            when=60, 
            chat_id=chat.id, 
            data=warning_msg.message_id
        )
    except Exception as e:
        print(f"Error in filter_messages: {e}")

def main():
    Thread(target=run_flask).start()

    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    
    # /new കമാൻഡിനുള്ള ഹാൻഡ്‌ലർ
    application.add_handler(CommandHandler("new", toggle_welcome))
    
    # മറ്റെല്ലാ ആക്റ്റിവിറ്റികളും ഫിൽട്ടർ ചെയ്യാൻ
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_everything))

    print("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()