import logging
import os
from datetime import datetime, timedelta, timezone
from threading import Thread
from flask import Flask
from telegram import Update, ChatPermissions
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# --- FLASK WEB SERVER SETUP ---
# ബോട്ട് ഹോസ്റ്റിംഗ് പ്ലാറ്റ്‌ഫോമുകളിൽ ഓഫാകാതെ എപ്പോഴും റൺ ചെയ്യാൻ വേണ്ടി ഒരു ഫ്ലാസ്ക് സെർവർ ഉണ്ടാക്കുന്നു
flask_app = Flask('')

@flask_app.route('/')
def home():
    return "ബോട്ട് വിജയകരമായി പ്രവർത്തിക്കുന്നു!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()


# --- TELEGRAM BOT SETUP ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

TOKEN = "8673412670:AAFW2QTdkHH_LxecEzJNE-SkflJZe1X8Y0g"

# പഴയ മെസ്സേജുകളുടെ ഐഡി സൂക്ഷിക്കാനും ആന്റി-ലിങ്ക് സ്റ്റാറ്റസ് അറിയാനുമുള്ള ഗ്ലോബൽ വേരിയബിളുകൾ
last_warning_message_id = None
last_welcome_message_id = None
antilink_status = True  # തുടക്കത്തിൽ ഈ ഫീച്ചർ ഓൺ ആയിരിക്കും (True)

# കമാൻഡ് അടിക്കുന്ന ആൾ ഗ്രൂപ്പിലെ അഡ്മിൻ ആണോ എന്ന് പരിശോധിക്കാനുള്ള ഫങ്ഷൻ
async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ['creator', 'administrator']
    except Exception:
        return False

# /start കമാൻഡ് വരുമ്പോൾ കാണിക്കേണ്ട മെസ്സേജ്
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ഹലോ! ഞാൻ നിങ്ങളുടെ ഗ്രൂപ്പ് മാനേജ്‌മെന്റ് ബോട്ട് ആണ്.\n\n"
        "**കമാൻഡുകൾ (മെസ്സേജിന് റിപ്ലൈ ആയി അടിക്കുക):**\n"
        "/ban - ബാൻ ചെയ്യാൻ\n"
        "/kick - പുറത്താക്കാൻ\n"
        "/mute - എപ്പോഴും മ్యూട്ട് ചെയ്യാൻ\n"
        "/tmute [മിനിറ്റ്] - പറഞ്ഞ സമയത്തേക്ക് മ്യൂട്ട് ചെയ്യാൻ (ഉദാ: /tmute 10)\n"
        "/unmute - മ్యూട്ട് മാറ്റാൻ\n\n"
        "**അഡ്മിൻ കമാൻഡുകൾ:**\n"
        "/antilink on - ആന്റി-ലിങ്ക് ഫീച്ചർ ഓൺ ചെയ്യാൻ\n"
        "/antilink off - ആന്റി-ലിങ്ക് ഫീച്ചർ ഓഫ് ചെയ്യാൻ\n"
        "/unban [user_id] - അൺബാൻ ചെയ്യാൻ"
    )

# --- ഓൺ / ഓഫ് ചെയ്യാനുള്ള കമാൻഡ് ഫങ്ഷൻ ---
async def toggle_antilink(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global antilink_status
    
    # കമാൻഡ് അടിക്കുന്നത് അഡ്മിൻ ആണെന്ന് ഉറപ്പുവരുത്തുന്നു
    if not await is_admin(update, context):
        await update.message.reply_text("❌ നിങ്ങൾക്ക് ഈ കമാൻഡ് ഉപയോഗിക്കാൻ അധികാരമില്ല!")
        return

    if not context.args:
        await update.message.reply_text("⚠️ ഉപയോഗിക്കേണ്ട രീതി: `/antilink on` അല്ലെങ്കിൽ `/antilink off`")
        return

    command = context.args[0].lower()
    if command == "on":
        antilink_status = True
        await update.message.reply_text("✅ ലിങ്ക് ഒഴികെയുള്ള മറ്റ് മെസ്സേജുകൾ ഡിലീറ്റ് ചെയ്യുന്ന സിസ്റ്റം ഓൺ ആക്കി!")
    elif command == "off":
        antilink_status = False
        await update.message.reply_text("🛑 ലിങ്ക് ഒഴികെയുള്ള മറ്റ് മെസ്സേജുകൾ ഡിലീറ്റ് ചെയ്യുന്ന സിസ്റ്റം ഓഫ് ആക്കി!")
    else:
        await update.message.reply_text("⚠️ ദയവായി `on` അല്ലെങ്കിൽ `off` എന്ന് മാത്രം ചേർക്കുക.")

# /ban കമാൻഡ്
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
        await update.message.reply_text(f"❌ {user_to_ban.first_name} എന്ന യൂസറെ ബാൻ ചെയ്തു.")
    except Exception as e:
        await update.message.reply_text(f"ബാൻ ചെയ്യാൻ പറ്റിയില്ല: {e}")

# /unban കമാൻഡ്
async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
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

# /kick കമാൻഡ്
async def kick_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ ആരെയാണ് കിക്ക് ചെയ്യേണ്ടത് അവരുടെ മെസ്സേജിന് റിപ്ലൈ ആയി ചെയ്യുക.")
        return
    user_to_kick = update.message.reply_to_message.from_user
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, user_to_kick.id)
        await context.bot.unban_chat_member(update.effective_chat.id, user_to_kick.id)
        await update.message.reply_text(f"🏃 {user_to_kick.first_name} ഗ്രൂപ്പിൽ നിന്നും പുറത്താക്കപ്പെട്ടു.")
    except Exception as e:
        await update.message.reply_text(f"കിക്ക് ചെയ്യാൻ പറ്റിയില്ല: {e}")

# /mute കമാൻഡ്
async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ ആരെയാണ് മ్యూട്ട് ചെയ്യേണ്ടത് അവരുടെ മെസ്സേജിന് റിപ്ലൈ ആയി ചെയ്യുക.")
        return
    user_to_mute = update.message.reply_to_message.from_user
    no_send_permissions = ChatPermissions(can_send_messages=False)
    try:
        await context.bot.restrict_chat_member(update.effective_chat.id, user_to_mute.id, permissions=no_send_permissions)
        await update.message.reply_text(f"🔇 {user_to_mute.first_name} മ్యూട്ട് ചെയ്യപ്പെട്ടു.")
    except Exception as e:
        await update.message.reply_text(f"മ్యూട്ട് ചെയ്യാൻ പറ്റിയില്ല: {e}")

# /tmute കമാൻഡ്
async def timed_mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ ആരെയാണ് മ్యూട്ട് ചെയ്യേണ്ടത് അവരുടെ മെസ്സേജിന് റിപ്ലൈ ആയി ചെയ്യുക.")
        return
    if not context.args:
        await update.message.reply_text("⚠️ എത്ര മിനിറ്റാണ് മ്യൂട്ട് ചെയ്യേണ്ടത് എന്ന് കൂടി പറയുക. ഉദാഹരണത്തിന്: `/tmute 10`")
        return

    try:
        minutes = int(context.args[0])
        user_to_mute = update.message.reply_to_message.from_user
        until_time = datetime.now(timezone.utc) + timedelta(minutes=minutes)
        no_send_permissions = ChatPermissions(can_send_messages=False)
        
        await context.bot.restrict_chat_member(
            update.effective_chat.id, 
            user_to_mute.id, 
            permissions=no_send_permissions, 
            until_date=until_time
        )
        await update.message.reply_text(f"⏳ {user_to_mute.first_name} {minutes} മിനിറ്റത്തേക്ക് മ్యూട്ട് ചെയ്യപ്പെട്ടു.")
    except ValueError:
        await update.message.reply_text("⚠️ സമയം നമ്പറായി തന്നെ നൽകുക (ഉദാഹരണത്തിന്: 10).")
    except Exception as e:
        await update.message.reply_text(f"മ്യൂട്ട് ചെയ്യാൻ പറ്റിയില്ല: {e}")

# /unmute കമാൻഡ്
async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ ആരുടെ മ్యూട്ടാണ് മാറ്റേണ്ടത് അവരുടെ മെസ്സേജിന് റിപ്ലൈ ആയി ചെയ്യുക.")
        return
    user_to_unmute = update.message.reply_to_message.from_user
    full_permissions = ChatPermissions(
        can_send_messages=True,
        can_send_audios=True,
        can_send_documents=True,
        can_send_photos=True,
        can_send_videos=True,
        can_send_video_notes=True,
        can_send_voice_notes=True,
        can_send_polls=True,
        can_send_other_messages=True,
        can_add_web_page_previews=True
    )
    try:
        await context.bot.restrict_chat_member(update.effective_chat.id, user_to_unmute.id, permissions=full_permissions)
        await update.message.reply_text(f"🔊 {user_to_unmute.first_name} അൺമ്യൂട്ട് ചെയ്യപ്പെട്ടു. ഇനി മെസ്സേജ് അയക്കാം.")
    except Exception as e:
        await update.message.reply_text(f"അൺമ്യൂട്ട് ചെയ്യാൻ പറ്റിയില്ല: {e}")

# --- ലിങ്ക് ഒഴികെയുള്ള മറ്റ് ടെക്സ്റ്റ് മെസ്സേജുകൾ ഡിലീറ്റ് ചെയ്യാനും വാണിംഗ് നൽകാനുമുള്ള ഫങ്ഷൻ ---
async def handle_normal_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global last_warning_message_id, antilink_status
    
    # സിസ്റ്റം അഡ്മിൻ ഓഫ് ആക്കിയിട്ടുണ്ടെങ്കിൽ ഈ ഫങ്ഷൻ വർക്ക് ആകില്ല
    if not antilink_status:
        return

    # അഡ്മിൻമാർ അയക്കുന്ന മെസ്സേജുകൾ ഡിലീറ്റ് ചെയ്യരുത്
    if await is_admin(update, context):
        return

    # മെസ്സേജിൽ ലിങ്കുകൾ (URLs) അടങ്ങിയിട്ടുണ്ടെങ്കിൽ അത് ഡിലീറ്റ് ചെയ്യാതെ ഒഴിവാക്കുന്നു
    if update.message.entities and any(entity.type in ["url", "text_link"] for entity in update.message.entities):
        return

    chat_id = update.effective_chat.id
    user = update.effective_user

    try:
        # 1. ഗ്രൂപ്പിൽ വന്ന ലിങ്ക് അല്ലാത്ത ടെക്സ്റ്റ് മെസ്സേജ് ഡിലീറ്റ് ചെയ്യുന്നു
        await context.bot.delete_message(chat_id=chat_id, message_id=update.message.message_id)

        # 2. ബോട്ട് മുൻപ് അയച്ചിട്ടുള്ള വാണിംഗ് മെസ്സേജ് ഗ്രൂപ്പിൽ ഉണ്ടെങ്കിൽ അത് ഡിലീറ്റ് ചെയ്യുന്നു
        if last_warning_message_id is not None:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=last_warning_message_id)
            except Exception:
                pass

        # 3. മെസ്സേജ് അയച്ച യൂസറെ മെൻഷൻ ചെയ്തുകൊണ്ട് പുതിയ വാണിംഗ് മെസ്സേജ് അയക്കുന്നു
        warning_text = f"⚠️ {user.mention_html()} ഗ്രൂപ്പിൽ ലിങ്ക് മാത്രം ഇടുക!"
        sent_message = await context.bot.send_message(chat_id=chat_id, text=warning_text, parse_mode="HTML")
        
        # 4. അടുത്ത തവണ ഡിലീറ്റ് ചെയ്യാൻ വേണ്ടി പുതിയ മെസ്സേജ് ഐഡി സൂക്ഷിച്ചുവെക്കുന്നു
        last_warning_message_id = sent_message.message_id

    except Exception as e:
        print(f"മെസ്സേജ് കൈകാര്യം ചെയ്യുന്നതിൽ എറർ: {e}")

# --- പുതിയ മെമ്പർമാർ വരുമ്പോൾ സ്വാഗതം ചെയ്യാനുള്ള ഫങ്ഷൻ ---
async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global last_welcome_message_id
    chat_id = update.effective_chat.id
    
    for new_member in update.message.new_chat_members:
        if new_member.id == context.bot.id:
            continue
            
        try:
            # പുതിയ ആളുകൾ വരുമ്പോൾ പഴയ വെൽക്കം മെസ്സേജ് ഡിലീറ്റ് ചെയ്യുന്നു
            if last_welcome_message_id is not None:
                try:
                    await context.bot.delete_message(chat_id=chat_id, message_id=last_welcome_message_id)
                except Exception:
                    pass

            # ഗ്രൂപ്പിലേക്ക് പുതിയ ആളുകളെ സ്വാഗതം ചെയ്യുന്നു
            welcome_text = f"👋 ഹലോ {new_member.mention_html()}, നമ്മുടെ ഗ്രൂപ്പിലേക്ക് സ്വാഗതം!"
            sent_message = await context.bot.send_message(chat_id=chat_id, text=welcome_text, parse_mode="HTML")
            last_welcome_message_id = sent_message.message_id
            
        except Exception as e:
            print(f"വെൽക്കം പറയുന്നതിൽ എറർ: {e}")


def main():
    # വെബ് സെർവർ റൺ ചെയ്യിക്കുന്നു
    keep_alive()

    # ബോട്ട് ടോക്കൺ വെച്ച് ആപ്ലിക്കേഷൻ ബിൽഡ് ചെയ്യുന്നു
    app = Application.builder().token(TOKEN).build()

    # കമാൻഡ് ഹാൻഡ്‌ലറുകൾ രജിസ്റ്റർ ചെയ്യുന്നു
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("antilink", toggle_antilink)) # ഓൺ/ഓഫ് ചെയ്യാനുള്ള പുതിയ കമാൻഡ്
    app.add_handler(CommandHandler("ban", ban_user))
    app.add_handler(CommandHandler("unban", unban_user))
    app.add_handler(CommandHandler("kick", kick_user))
    app.add_handler(CommandHandler("mute", mute_user))
    app.add_handler(CommandHandler("tmute", timed_mute_user))
    app.add_handler(CommandHandler("unmute", unmute_user))

    # ഗ്രൂപ്പിലേക്ക് പുതിയ ആളുകൾ കയറുന്നത് നിരീക്ഷിക്കാൻ
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))

    # ഗ്രൂപ്പിൽ വരുന്ന മെസ്സേജുകൾ പരിശോധിക്കാനും ലിങ്ക് അല്ലാത്തവ ഡിലീറ്റ് ചെയ്യാനുമുള്ള ഹാൻഡ്‌ലർ
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_normal_messages))

    print("ബോട്ട് പൂർണ്ണ സജ്ജമാണ്...")
    app.run_polling()

if __name__ == '__main__':
    main()