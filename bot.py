import os
import asyncio
import random
from flask import Flask
from threading import Thread
from telegram import Update, ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# Flask വെബ് സെർവർ സെറ്റപ്പ് (Render ഹോസ്റ്റിംഗ് എപ്പോഴും ലൈവ് ആയിരിക്കാൻ)
app = Flask('')

@app.route('/')
def home():
    return "Bot is running perfectly!"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# ബോട്ട് വിവരങ്ങൾ
BOT_TOKEN = "8397424887:AAEyNXWcGS6e9NoJ_JrUw_TB6ulRlcm-vL4"
GROUP_LINK = "https://t.me/+imWG8JPfw6cyMTQ1"

# 🛑 നിങ്ങളുടെ ശരിയായ Owner ID-യും Group ID-യും ഇവിടെ നൽകുക
OWNER_ID = 123456789  
ALLOWED_GROUP_ID = -1002482312345  

user_warnings = {}
custom_notes = {
    "rules": "📜 ഗ്രൂപ്പ് നിയമങ്ങൾ അനുസരിക്കുക. പരസ്പരം ബഹുമാനിക്കുക.",
}

# ബോട്ട് അനുവദിക്കപ്പെട്ട ഗ്രൂപ്പിലാണോ എന്ന് പരിശോധിക്കാൻ
def is_allowed_chat(update: Update) -> bool:
    if update.effective_chat.type == "private":
        return True
    return update.effective_chat.id == ALLOWED_GROUP_ID

# അഡ്മിൻ/ഓണർ പരിശോധന (എറർ വരാതിരിക്കാൻ ലളിതമാക്കിയത്)
async def is_owner_or_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id
    if user_id == OWNER_ID:
        return True
    if update.effective_chat.type == "private":
        return True
    try:
        member = await context.bot.get_chat_member(update.effective_chat.id, user_id)
        return member.status in ["administrator", "creator"]
    except Exception:
        return False

# 🌟 റാൻഡം റിയാക്ഷൻ
async def random_reaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed_chat(update) or update.effective_chat.type == "private":
        return
    if update.message.text and update.message.text.startswith('/'):
        return

    reactions = ["👍", "❤️", "🔥", "😂", "😮", "🎉", "👏", "⚡"]
    chosen_reaction = random.choice(reactions)
    try:
        await context.bot.set_message_reaction(
            chat_id=update.effective_chat.id,
            message_id=update.message.message_id,
            reaction=[{"type": "emoji", "emoji": chosen_reaction}]
        )
    except Exception:
        pass

# കമാൻഡുകൾ
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed_chat(update): return
    keyboard = [
        [InlineKeyboardButton("Help & Commands 📜", callback_data="help_menu")],
        [InlineKeyboardButton("Join Our Group 🔗", url=GROUP_LINK)]
    ]
    await update.message.reply_text(
        "ഹലോ! ഞാൻ നിങ്ങളുടെ ഗ്രൂപ്പ് മാനേജ്മെന്റ് ബോട്ട് ആണ്.\n\nകമാൻഡുകൾ മനസ്സിലാക്കാൻ താഴെയുള്ള ബട്ടൺ ക്ലിക്ക് ചെയ്യുക.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed_chat(update): return
    help_text = (
        "🛠 **ഗ്രൂപ്പ് മാനേജ്മെന്റ് കമാൻഡുകൾ:**\n\n"
        "🛑 **Ban:** `/ban` (മെസ്സേജിന് റിപ്ലൈ ചെയ്യുക)\n"
        "👋 **Kick:** `/kick`\n"
        "🤫 **Mute:** `/mute` | `/unmute`\n"
        "⚠️ **Warning:** `/warn` (3 വാണിംഗ് ആയാൽ ഓട്ടോ ബാൻ)\n"
        "📝 **Notes:** `/save <name> <content>` | `/get <name>`"
    )
    await update.message.reply_text(help_text)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "help_menu":
        await query.edit_message_text(text="• `/ban` - Ban ചെയ്യാൻ\n• `/kick` - പുറത്താക്കാൻ\n• `/mute` - മ്യൂട്ട് ചെയ്യാൻ\n• `/warn` - വാണിംഗ് നൽകാൻ")

# 🛑 മെസ്സേജുകൾ ശരിയായി വർക്ക് ആകാൻ Text റെസ്‌പോൺസ് ലളിതമാക്കി
async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed_chat(update) or update.effective_chat.type == "private": return
    if not await is_owner_or_admin(update, context): return
    if not update.message.reply_to_message:
        return await update.message.reply_text("❌ ആർക്കാണോ ബാൻ നൽകേണ്ടത് ആ മെസ്സേജിന് റിപ്ലൈ ആയി /ban എന്ന് ടൈപ്പ് ചെയ്യുക.")

    target_user = update.message.reply_to_message.from_user
    await context.bot.ban_chat_member(update.effective_chat.id, target_user.id)
    await update.message.reply_text(f"🛑 {target_user.first_name} ഗ്രൂപ്പിൽ നിന്നും Ban ചെയ്യപ്പെട്ടു.")

async def kick_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed_chat(update) or update.effective_chat.type == "private": return
    if not await is_owner_or_admin(update, context): return
    if not update.message.reply_to_message: return

    target_user = update.message.reply_to_message.from_user
    await context.bot.ban_chat_member(update.effective_chat.id, target_user.id)
    await context.bot.unban_chat_member(update.effective_chat.id, target_user.id)
    await update.message.reply_text(f"👋 {target_user.first_name} ഗ്രൂപ്പിൽ നിന്നും പുറത്താക്കപ്പെട്ടു.")

async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed_chat(update) or update.effective_chat.type == "private": return
    if not await is_owner_or_admin(update, context): return
    if not update.message.reply_to_message: return

    target_user = update.message.reply_to_message.from_user
    await context.bot.restrict_chat_member(update.effective_chat.id, target_user.id, ChatPermissions(can_send_messages=False))
    await update.message.reply_text(f"🤫 {target_user.first_name} Mute ചെയ്യപ്പെട്ടു.")

async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed_chat(update) or update.effective_chat.type == "private": return
    if not await is_owner_or_admin(update, context): return
    if not update.message.reply_to_message: return

    target_user = update.message.reply_to_message.from_user
    await context.bot.restrict_chat_member(update.effective_chat.id, target_user.id, ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True))
    await update.message.reply_text(f"🔊 {target_user.first_name} അൺമ്യൂട്ട് ചെയ്യപ്പെട്ടു.")

async def warn_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed_chat(update) or update.effective_chat.type == "private": return
    if not await is_owner_or_admin(update, context): return
    if not update.message.reply_to_message: return

    target_user = update.message.reply_to_message.from_user
    user_id = target_user.id
    chat_id = update.effective_chat.id
    
    if chat_id not in user_warnings: user_warnings[chat_id] = {}
    if user_id not in user_warnings[chat_id]: user_warnings[chat_id][user_id] = 0
    
    user_warnings[chat_id][user_id] += 1
    count = user_warnings[chat_id][user_id]
    
    if count >= 3:
        await context.bot.ban_chat_member(chat_id, user_id)
        user_warnings[chat_id][user_id] = 0
        await update.message.reply_text(f"🛑 {target_user.first_name} 3 വാണിംഗുകൾ ലഭിച്ചതിനാൽ Ban ചെയ്യപ്പെട്ടു.")
    else:
        await update.message.reply_text(f"⚠️ {target_user.first_name} നിങ്ങൾക്ക് ഒരു വാണിംഗ് ലഭിച്ചു! ({count}/3)")

async def save_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed_chat(update): return
    if not await is_owner_or_admin(update, context): return
    if len(context.args) < 2: return
    
    note_name = context.args[0].lower()
    note_content = " ".join(context.args[1:])
    custom_notes[note_name] = note_content
    await update.message.reply_text(f"✅ നോട്ട് '{note_name}' വിജയകരമായി സേവ് ചെയ്തു.")

async def get_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed_chat(update): return
    if len(context.args) < 1: return
    
    note_name = context.args[0].lower()
    if note_name in custom_notes:
        await update.message.reply_text(custom_notes[note_name])

async def welcome_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed_chat(update): return
    for member in update.message.new_chat_members:
        if not member.is_bot:
            await update.message.reply_text(f"ഹലോ {member.first_name} 👋!\nഞങ്ങളുടെ ഗ്രൂപ്പിലേക്ക് സ്വാഗതം! ✨")

def main():
    # Flask വെബ് സെർവർ ഒരു സെപ്പറേറ്റ് ത്രെഡിൽ സ്റ്റാർട്ട് ചെയ്യുന്നു
    Thread(target=run_flask).start()

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("ban", ban_user))
    application.add_handler(CommandHandler("kick", kick_user))
    application.add_handler(CommandHandler("mute", mute_user))
    application.add_handler(CommandHandler("unmute", unmute_user))
    application.add_handler(CommandHandler("warn", warn_user))
    application.add_handler(CommandHandler("save", save_note))
    application.add_handler(CommandHandler("get", get_note))
    
    application.add_handler(CallbackQueryHandler(button_click))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_member))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), random_reaction))

    print("Bot is running with Flask...")
    application.run_polling()

if __name__ == "__main__":
    main()