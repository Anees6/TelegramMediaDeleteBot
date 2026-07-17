import asyncio
import re
from threading import Thread
from flask import Flask
from telegram import Update, ChatPermissions
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Flask വെബ് സെർവർ സെറ്റപ്പ് (Render-ൽ ലിങ്ക് കിട്ടാൻ വേണ്ടി)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# നിങ്ങളുടെ ബോട്ട് ടോക്കൺ ഇവിടെ ചേർത്തിട്ടുണ്ട്
BOT_TOKEN = "8673412670:AAFW2QTdkHH_LxecEzJNE-SkflJZe1X8Y0g"
LINK_REGEX = re.compile(r'https?://\S+|www\.\S+')

# അവസാനമായി അയച്ച വെൽക്കം മെസ്സേജിന്റെ ID സൂക്ഷിക്കാൻ ഒരു ഡിക്ഷണറി
last_welcome_messages = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ബോട്ട് ആക്ടീവ് ആണ്!")

async def delete_warning(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    try:
        await context.bot.delete_message(chat_id=job.chat_id, message_id=job.data)
    except Exception as e:
        print(f"Error deleting message: {e}")

async def handle_everything(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """എല്ലാ മെസ്സേജുകളും പുതിയ ആളുകൾ വരുന്നതും കൈകാര്യം ചെയ്യുന്ന മെയിൻ ഫങ്ഷൻ"""
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
        for new_member in message.new_chat_members:
            if new_member.is_bot:
                continue

            # മുമ്പൊരു പുതിയ യൂസർ വന്നപ്പോൾ അയച്ച വെൽക്കം മെസ്സേജ് ഉണ്ടെങ്കിൽ അത് ഡിലീറ്റ് ചെയ്യുന്നു
            if chat.id in last_welcome_messages:
                try:
                    await context.bot.delete_message(chat_id=chat.id, message_id=last_welcome_messages[chat.id])
                except Exception as e:
                    print(f"Error deleting previous welcome message: {e}")

            # വെൽക്കം മെസ്സേജ് ടെക്സ്റ്റ്
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

                # ഇപ്പോഴത്തെ വെൽക്കം മെസ്സേജിന്റെ ID സേവ് ചെയ്യുന്നു
                last_welcome_messages[chat.id] = welcome_msg.message_id

                # കൃത്യം 5 മിനിറ്റിന് ശേഷം (300 സെക്കൻഡ്) ഡിലീറ്റ് ചെയ്യാൻ ഷെഡ്യൂൾ ചെയ്യുന്നു
                context.job_queue.run_once(
                    delete_warning,
                    when=300,
                    chat_id=chat.id,
                    data=welcome_msg.message_id
                )
            except Exception as e:
                print(f"Error sending welcome message: {e}")
        return

    # --- 2. ലിങ്ക് ഫിൽട്ടറിംഗ് ലോജിക് (സാധാരണ മെസ്സേജുകൾക്ക്) ---
    has_link = message.text and LINK_REGEX.search(message.text)

    try:
        if has_link:
            # ലിങ്ക് ഉള്ള മെസ്സേജ് ആണെങ്കിൽ 15 മിനിറ്റിന് (900 സെക്കൻഡ്) ശേഷം ഡിലീറ്റ് ചെയ്യും
            context.job_queue.run_once(
                delete_warning, 
                when=900, 
                chat_id=chat.id, 
                data=message.message_id
            )
            return

        # ലിങ്ക് അല്ലാത്ത മെസ്സേജ് ഡിലീറ്റ് ചെയ്യുന്നു
        await message.delete()

        # യൂസറെ മ്യൂട്ട് ചെയ്യുന്നു
        mute_permissions = ChatPermissions(can_send_messages=False)
        await chat.restrict_member(user_id=user.id, permissions=mute_permissions)

        # വാണിംഗ് മെസ്സേജ് അയക്കുന്നു
        warning_msg = await context.bot.send_message(
            chat_id=chat.id,
            text=f"⚠️ {user.mention_html()}, ഈ ഗ്രൂപ്പിൽ ലിങ്കുകൾ മാത്രമേ അനുവദിക്കൂ! നിങ്ങളുടെ മെസ്സേജ് ഡിലീറ്റ് ചെയ്ത് നിങ്ങളെ മ്യൂട്ട് ചെയ്തിരിക്കുന്നു.",
            parse_mode="HTML"
        )

        # 1 മിനിറ്റിന് (60 സെക്കൻഡ്) ശേഷം വാണിംഗ് മെസ്സേജ് ഡിലീറ്റ് ചെയ്യുന്നു
        context.job_queue.run_once(
            delete_warning, 
            when=60, 
            chat_id=chat.id, 
            data=warning_msg.message_id
        )
    except Exception as e:
        print(f"Error in filter_messages: {e}")

def main():
    # വെബ് സെർവർ സ്റ്റാർട്ട് ചെയ്യുന്നു
    Thread(target=run_flask).start()

    # ബോട്ട് സ്റ്റാർട്ട് ചെയ്യുന്നു
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    
    # എല്ലാ മെസ്സേജുകളും സ്റ്റാറ്റസ് അപ്ഡേറ്റുകളും ഒരൊറ്റ ഹാൻഡ്‌ലറിലേക്ക് വിടുന്നു
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_everything))

    print("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()