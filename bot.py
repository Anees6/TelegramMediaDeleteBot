import logging
import os
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# --- FLASK WEB SERVER SETUP (ഫോർ 24/7 ഹോസ്റ്റിംഗ്) ---
flask_app = Flask('')

@flask_app.route('/')
def home():
    return "ബോട്ട് വിജയകരമായി പ്രവർത്തിക്കുന്നു!"

def run_flask():
    # ഹോസ്റ്റിംഗ് സൈറ്റുകൾ തരുന്ന പോർട്ട് എടുക്കും, ഇല്ലെങ്കിൽ 8080 ഉപയോഗിക്കും
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host='0.0.0.0', port=port)

def keep_alive():
    # Flask ബാക്ക്ഗ്രൗണ്ടിൽ റൺ ചെയ്യാനുള്ള ത്രെഡ്
    t = Thread(target=run_flask)
    t.start()


# --- TELEGRAM BOT SETUP ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

TOKEN = "8673412670:AAFW2QTdkHH_LxecEzJNE-SkflJZe1X8Y0g"

# കമാൻഡ് അടിക്കുന്നയാൾ ഗ്രൂപ്പ് അഡ്മിൻ ആണോ എന്ന് പരിശോധിക്കാനുള്ള ഫങ്ഷൻ
async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ['creator', 'administrator']
    except Exception:
        return False

# /start കമാൻഡ്
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ഹലോ! ഞാൻ നിങ്ങളുടെ ഗ്രൂപ്പ് മാനേജ്‌മെന്റ് ബോട്ട് ആണ്.\n\n"
        "കമാൻഡുകൾ:\n"
        "/ban - മെസ്സേജിന് റിപ്ലൈ ആയി അടിച്ചാൽ യൂസറെ ബാൻ ചെയ്യാം\n"
        "/kick - മെസ്സേജിന് റിപ്ലൈ ആയി അടിച്ചാൽ യൂസറെ പുറത്താക്കാം\n"
        "/unban [user_id] - ഐഡി വെച്ച് അൺബാൻ ചെയ്യാം"
    )

# /ban കമാൻഡ് (മെസ്സേജിന് റിപ്ലൈ ആയി ഉപയോഗിക്കണം)
async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text("❌ നിങ്ങൾക്ക് ഈ കമാൻഡ് ഉപയോഗിക്കാൻ അധികാരമില്ല!")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ ഏത് യൂസറെയാണ് ബാൻ ചെയ്യേണ്ടത് അവരുടെ മെസ്സേജിന് റിപ്ലൈ ആയി ഈ കമാൻഡ് അടിക്കുക.")
        return

    user_to_ban = update.message.reply_to_message.from_user
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, user_to_ban.id)
        await update.message.reply_text(f"❌ {user_to_ban.first_name} എന്ന യൂസറെ ഗ്രൂപ്പിൽ നിന്നും ബാൻ ചെയ്തു.")
    except Exception as e:
        await update.message.reply_text(f"ಬാൻ ചെയ്യാൻ പറ്റിയില്ല: {e}")

# /unban കമാൻഡ് (ഉദാഹരണത്തിന്: /unban 12345678)
async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text("❌ നിങ്ങൾക്ക് ഈ കമാൻഡ് ഉപയോഗിക്കാൻ അധികാരമില്ല!")
        return

    if not context.args:
        await update.message.reply_text("⚠️ ഉപയോഗിക്കേണ്ട രീതി: `/unban [user_id]`")
        return

    try:
        user_id = int(context.args[0])
        await context.bot.unban_chat_member(update.effective_chat.id, user_id)
        await update.message.reply_text(f"✓ യൂസർ (ID: {user_id}) അൺബാൻ ചെയ്യപ്പെട്ടു.")
    except Exception as e:
        await update.message.reply_text(f"അൺബാൻ ചെയ്യാൻ പറ്റിയില്ല: {e}")

# /kick കമാൻഡ് (മെസ്സേജിന് റിപ്ലൈ ആയി ഉപയോഗിക്കണം)
async def kick_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text("❌ നിങ്ങൾക്ക് ഈ കമാൻഡ് ഉപയോഗിക്കാൻ അധികാരമില്ല!")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ ആരെയാണ് കിക്ക് ചെയ്യേണ്ടത് അവരുടെ മെസ്സേജിന് റിപ്ലൈ ആയി ചെയ്യുക.")
        return

    user_to_kick = update.message.reply_to_message.from_user
    try:
        # ബാൻ ചെയ്ത് തൊട്ടുപിന്നാലെ അൺബാൻ ചെയ്യുമ്പോൾ അയാൾ ഗ്രൂപ്പിൽ നിന്ന് കിക്ക് ആകും (വീണ്ടും ഗ്രൂപ്പിൽ കയറാം)
        await context.bot.ban_chat_member(update.effective_chat.id, user_to_kick.id)
        await context.bot.unban_chat_member(update.effective_chat.id, user_to_kick.id)
        await update.message.reply_text(f"🏃 {user_to_kick.first_name} ഗ്രൂപ്പിൽ നിന്നും പുറത്താക്കപ്പെട്ടു.")
    except Exception as e:
        await update.message.reply_text(f"കിക്ക് ചെയ്യാൻ പറ്റിയില്ല: {e}")

def main():
    # ബോട്ട് റൺ ചെയ്യുന്നതിന് തൊട്ടുമുമ്പ് ഫ്ലാസ്ക് വെബ് സെർവർ ബാക്ക്ഗ്രൗണ്ടിൽ സ്റ്റാർട്ട് ചെയ്യുന്നു
    keep_alive()

    # ബോട്ട് ആപ്ലിക്കേഷൻ തുടങ്ങുന്നു
    app = Application.builder().token(TOKEN).build()

    # കമാൻഡുകൾ ലിങ്ക് ചെയ്യുന്നു
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ban", ban_user))
    app.add_handler(CommandHandler("unban", unban_user))
    app.add_handler(CommandHandler("kick", kick_user))

    print("ബോട്ട് വിജയകരമായി സ്റ്റാർട്ട് ആയിട്ടുണ്ട്...")
    app.run_polling()

if __name__ == '__main__':
    main()