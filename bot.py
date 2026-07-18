import logging
import os
from datetime import datetime, timedelta, timezone
from threading import Thread
from flask import Flask
from telegram import Update, ChatPermissions
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# --- FLASK WEB SERVER SETUP ---
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

# പഴയ വാണിംഗ് മെസ്സേജും വെൽക്കം മെസ്സേജും സൂക്ഷിക്കാൻ
last_warning_message_id = None
last_welcome_message_id = None

# ഗ്രൂപ്പ് അഡ്മിൻ പരിശോധന
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
        "**കമാൻഡുകൾ (മെസ്സേജിന് റിപ്ലൈ ആയി അടിക്കുക):**\n"
        "/ban - ബാൻ ചെയ്യാൻ\n"
        "/kick - പുറത്താക്കാൻ\n"
        "/mute - എപ്പോഴും മ്യൂട്ട് ചെയ്യാൻ\n"
        "/tmute [മിനിറ്റ്] - പറഞ്ഞ സമയത്തേക്ക് മ്യൂട്ട് ചെയ്യാൻ (ഉദാ: /tmute 10)\n"
        "/unmute - മ്യൂട്ട് മാറ്റാൻ\n\n"
        "**ഐഡി വെച്ച് ഉപയോഗിക്കാൻ:**\n"
        "/unban [user_id] - അൺബാൻ ചെയ്യാൻ"
    )

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
        await update.message.reply_text("⚠️ ആരെയാണ് മ്യൂട്ട് ചെയ്യേണ്ടത് അവരുടെ മെസ്സേജിന് റിപ്ലൈ ആയി ചെയ്യുക.")
        return
    user_to_mute = update.message.reply_to_message.from_user
    no_send_permissions = ChatPermissions(can_send_messages=False)
    try:
        await context.bot.restrict_chat_member(update.effective_chat.id, user_to_mute.id, permissions=no_send_permissions)
        await update.message.reply_text(f"🔇 {user_to_mute.first_name} മ്യൂട്ട് ചെയ്യപ്പെട്ടു.")
    except Exception as e:
        await update.message.reply_text(f"മ്യൂട്ട് ചെയ്യാൻ പറ്റിയില്ല: {e}")

# /tmute കമാൻഡ്
async def timed_mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ ആരെയാണ് മ്യൂട്ട് ചെയ്യേണ്ടത് അവരുടെ മെസ്സേജിന് റിപ്ലൈ ആയി ചെയ്യുക.")
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
        await update.message.reply_text(f"⏳ {user_to_mute.first_name} {minutes} മിനിറ്റത്തേക്ക് മ്യൂട്ട് ചെയ്യപ്പെട്ടു.")
    except ValueError:
        await update.message.reply_text("⚠️ സമയം നമ്പറായി തന്നെ നൽകുക (ഉദാഹരണത്തിന്: 10).")
    except Exception as e:
        await update.message.reply_text(f"മ്യൂട്ട് ചെയ്യാൻ പറ്റിയില്ല: {e}")

# /unmute കമാൻഡ്
async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ ആരുടെ മ്യൂട്ടാണ് മാറ്റേണ്ടത് അവരുടെ മെസ്സേജിന് റിപ്ലൈ ആയി ചെയ്യുക.")
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

# --- ലിങ്ക് ഒഴികെയുള്ള മറ്റ് മെസ്സേജുകൾ ഡിലീറ്റ് ചെയ്യാനുള്ള ഫങ്ഷൻ ---
async def handle_normal_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global last_warning_message_id
    
    if await is_admin(update, context):
        return

    if update.message.entities and any(entity.type in ["url", "text_link"] for entity in update.message.entities):
        return

    chat_id = update.effective_chat.id
    user = update.effective_user

    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=update.message.message_id)

        if last_warning_message_id is not None:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=last_warning_message_id)
            except Exception:
                pass

        warning_text = f"⚠️ {user.mention_html()} ഗ്രൂപ്പിൽ ലിങ്ക് മാത്രം ഇടുക!"
        sent_message = await context.bot.send_message(chat_id=chat_id, text=warning_text, parse_mode="HTML")
        last_warning_message_id = sent_message.message_id

    except Exception as e:
        print(f"എറർ: {e}")

# --- പുതിയ ഫീച്ചർ: ഗ്രൂപ്പിലേക്ക് പുതിയ ആളുകൾ വരുമ്പോൾ സ്വാഗതം ചെയ്യാൻ ---
async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global last_welcome_message_id
    chat_id = update.effective_chat.id
    
    # പുതിയതായി വന്ന എല്ലാ മെമ്പർമാരെയും സ്വാഗതം ചെയ്യുന്നു
    for new_member in update.message.new_chat_members:
        # ബോട്ട് തന്നെയാണ് ഗ്രൂപ്പിൽ കയറിയതെങ്കിൽ വെൽക്കം പറയേണ്ടതില്ല
        if new_member.id == context.bot.id:
            continue
            
        try:
            # പഴയ വെൽക്കം മെസ്സേജ് ഉണ്ടെങ്കിൽ അത് ഡിലീറ്റ് ചെയ്യുന്നു
            if last_welcome_message_id is not None:
                try:
                    await context.bot.delete_message(chat_id=chat_id, message_id=last_welcome_message_id)
                except Exception:
                    pass

            # പുതിയ യൂസറെ സ്വാഗതം ചെയ്തുകൊണ്ട് മെസ്സേജ് അയക്കുന്നു
            welcome_text = f"👋 ഹലോ {new_member.mention_html()}, നമ്മുടെ ഗ്രൂപ്പിലേക്ക് സ്വാഗതം!"
            sent_message = await context.bot.send_message(chat_id=chat_id, text=welcome_text, parse_mode="HTML")
            
            # പുതിയ വെൽക്കം മെസ്സേജ് ഐഡി സേവ് ചെയ്യുന്നു
            last_welcome_message_id = sent_message.message_id
            
        except Exception as e:
            print(f"വെൽക്കം ഫങ്ഷനിൽ എറർ: {e}")


def main():
    keep_alive()

    app = Application.builder().token(TOKEN).build()

    # കമാൻഡുകൾ
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ban", ban_user))
    app.add_handler(CommandHandler("unban", unban_user))
    app.add_handler(CommandHandler("kick", kick_user))
    app.add_handler(CommandHandler("mute", mute_user))
    app.add_handler(CommandHandler("tmute", timed_mute_user))
    app.add_handler(CommandHandler("unmute", unmute_user))

    # ഗ്രൂപ്പിലേക്ക് പുതിയ ആളുകൾ കയറുന്നത് ശ്രദ്ധിക്കാൻ (Status Update Handler)
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))

    # ഗ്രൂപ്പിൽ വരുന്ന മറ്റ് മെസ്സേജുകൾ നിയന്ത്രിക്കാൻ
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_normal_messages))

    print("ബോട്ട് പൂർണ്ണ സജ്ജമാണ്...")
    app.run_polling()

if __name__ == '__main__':
    main()