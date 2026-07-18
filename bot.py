import os
import asyncio
import random  # റാൻഡം റിയാക്ഷൻ തിരഞ്ഞെടുക്കാൻ
from telegram import Update, ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# നിങ്ങളുടെ ടെലിഗ്രാം ബോട്ട് കീ
BOT_TOKEN = "8397424887:AAEyNXWcGS6e9NoJ_JrUw_TB6ulRlcm-vL4"
GROUP_LINK = "https://t.me/+imWG8JPfw6cyMTQ1"

# 🛑 ഇവിടെ നിങ്ങളുടെ സ്വന്തം ടെലിഗ്രാം യൂസർ ഐഡി (Owner ID) നൽകുക
OWNER_ID = 123456789  

# 🛑 ഇവിടെ ബോട്ട് വർക്ക് ചെയ്യേണ്ട നിങ്ങളുടെ ഗ്രൂപ്പിന്റെ ഐഡി നൽകുക
ALLOWED_GROUP_ID = -1002482312345  

user_warnings = {}
custom_notes = {
    "rules": "📜 ഗ്രൂപ്പ് നിയമങ്ങൾ അനുസരിക്കുക. പരസ്പരം ബഹുമാനിക്കുക.",
}

# ബോട്ട് അനുവദിക്കപ്പെട്ട ഗ്രൂപ്പിലാണോ എന്ന് പരിശോധിക്കുന്ന ഫങ്ഷൻ
def is_allowed_chat(update: Update) -> bool:
    if update.effective_chat.type == "private":
        return True 
    return update.effective_chat.id == ALLOWED_GROUP_ID

# 🌟 മെസ്സേജുകൾക്ക് റാൻഡം റിയാക്ഷൻ നൽകുന്ന പുതിയ ഫങ്ഷൻ
async def random_reaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed_chat(update) or update.effective_chat.type == "private":
        return
        
    # ബോട്ട് സ്വന്തം മെസ്സേജുകൾക്കോ കമാൻഡുകൾക്കോ റിയാക്ഷൻ ഇടാതിരിക്കാൻ
    if update.message.text and update.message.text.startswith('/'):
        return

    # ബോട്ട് നൽകാൻ ഉദ്ദേശിക്കുന്ന റിയാക്ഷനുകളുടെ ലിസ്റ്റ്
    reactions = ["👍", "❤️", "🔥", "😂", "😮", "🎉", "👏", "⚡"]
    chosen_reaction = random.choice(reactions)
    
    try:
        # ടെലിഗ്രാം റിയാക്ഷൻ API വഴി മെസ്സേജിന് റിയാക്ഷൻ സെറ്റ് ചെയ്യുന്നു
        await context.bot.set_message_reaction(
            chat_id=update.effective_chat.id,
            message_id=update.message.message_id,
            reaction=[{"type": "emoji", "emoji": chosen_reaction}],
            is_big=False
        )
    except Exception as e:
        # ഗ്രൂപ്പിൽ റിയാക്ഷൻ ഓഫ് ആണെങ്കിലോ എറർ വന്നാലോ ബോട്ട് ക്രാഷ് ആകാതിരിക്കാൻ
        print(f"Reaction Error: {e}")

# /start കമാൻഡ്
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed_chat(update): return
    keyboard = [
        [InlineKeyboardButton("Help & Commands 📜", callback_data="help_menu")],
        [InlineKeyboardButton("Join Our Group 🔗", url=GROUP_LINK)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"ഹലോ! ഞാൻ നിങ്ങളുടെ ഗ്രൂപ്പ് മാനേജ്മെന്റ് ബോട്ട് ആണ്.\n\n"
        f"കമാൻഡുകൾ മനസ്സിലാക്കാൻ താഴെയുള്ള ബട്ടൺ ക്ലിക്ക് ചെയ്യുക അല്ലെങ്കിൽ /help എന്ന് ടൈപ്പ് ചെയ്യുക.",
        reply_markup=reply_markup
    )

# /help കമാൻഡ്
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
    await update.message.reply_text(help_text, parse_mode="Markdown")

# ബട്ടൺ ക്ലിക്ക് ഹാൻഡ്‌ലർ
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "help_menu":
        help_text = "• `/ban` - Ban ചെയ്യാൻ\n• `/kick` - പുറത്താക്കാൻ\n• `/mute` - ബോൾ ബ്ലോക്ക് ചെയ്യാൻ\n• `/warn` - വാണിംഗ് നൽകാൻ"
        await query.edit_message_text(text=help_text)

# 1. സ്വാഗതം ചെയ്യൽ (Welcome Message)
async def welcome_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed_chat(update): return
    for member in update.message.new_chat_members:
        if not member.is_bot:
            await update.message.reply_text(
                f"ഹലോ {member.mention_markdown_v2()} 👋!\n"
                f"ഞങ്ങളുടെ ഗ്രൂപ്പിലേക്ക് സ്വാഗതം\\! ✨"
            )

# അഡ്മിൻ/ഓണർ പരിശോധന
async def is_owner_or_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id
    if user_id == OWNER_ID:
        return True
    if update.effective_chat.type == "private":
        return True
    member = await context.bot.get_chat_member(update.effective_chat.id, user_id)
    return member.status in ["administrator", "creator"]

# 2. Ban ചെയ്യാൻ (/ban)
async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed_chat(update) or update.effective_chat.type == "private": return
    if not await is_owner_or_admin(update, context): return
    if not update.message.reply_to_message: return

    target_user = update.message.reply_to_message.from_user
    await context.bot.ban_chat_member(update.effective_chat.id, target_user.id)
    await update.message.reply_text(f"🛑 {target_user.mention_markdown_v2()} ഗ്രൂപ്പിൽ നിന്നും Ban ചെയ്യപ്പെട്ടു\\.")

# 3. Kick ചെയ്യാൻ (/kick)
async def kick_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed_chat(update) or update.effective_chat.type == "private": return
    if not await is_owner_or_admin(update, context): return
    if not update.message.reply_to_message: return

    target_user = update.message.reply_to_message.from_user
    await context.bot.ban_chat_member(update.effective_chat.id, target_user.id)
    await context.bot.unban_chat_member(update.effective_chat.id, target_user.id)
    await update.message.reply_text(f"👋 {target_user.mention_markdown_v2()} ഗ്രൂപ്പിൽ നിന്നും പുറത്താക്കപ്പെട്ടു\\.")

# 4. Mute ചെയ്യാൻ (/mute)
async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed_chat(update) or update.effective_chat.type == "private": return
    if not await is_owner_or_admin(update, context): return
    if not update.message.reply_to_message: return

    target_user = update.message.reply_to_message.from_user
    await context.bot.restrict_chat_member(update.effective_chat.id, target_user.id, ChatPermissions(can_send_messages=False))
    await update.message.reply_text(f"🤫 {target_user.mention_markdown_v2()} Mute ചെയ്യപ്പെട്ടു\\.")

# 5. Unmute ചെയ്യാൻ (/unmute)
async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed_chat(update) or update.effective_chat.type == "private": return
    if not await is_owner_or_admin(update, context): return
    if not update.message.reply_to_message: return

    target_user = update.message.reply_to_message.from_user
    await context.bot.restrict_chat_member(update.effective_chat.id, target_user.id, ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True, can_add_web_page_previews=True))
    await update.message.reply_text(f"🔊 {target_user.mention_markdown_v2()} അൺമ്യൂട്ട് ചെയ്യപ്പെട്ടു\\.")

# 6. Warning നൽകാൻ (/warn)
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
        await update.message.reply_text(f"🛑 {target_user.mention_markdown_v2()} 3 വാണിംഗുകൾ ലഭിച്ചതിനാൽ ഗ്രൂപ്പിൽ നിന്നും Ban ചെയ്യപ്പെട്ടു\\.")
    else:
        await update.message.reply_text(f"⚠️ {target_user.mention_markdown_v2()} നിങ്ങൾക്ക് ഒരു വാണിംഗ് ലഭിച്ചു\\! ({count}/3)")

# 7. Note സേവ് ചെയ്യാൻ (/save)
async def save_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed_chat(update): return
    if not await is_owner_or_admin(update, context): return
    if len(context.args) < 2: return
    
    note_name = context.args[0].lower()
    note_content = " ".join(context.args[1:])
    custom_notes[note_name] = note_content
    await update.message.reply_text(f"✅ നോട്ട് *'{note_name}'* വിജയകരമായി സേവ് ചെയ്തു\\.", parse_mode="MarkdownV2")

# 8. Note വിളിച്ചുവരുത്താൻ (/get)
async def get_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed_chat(update): return
    if len(context.args) < 1: return
    
    note_name = context.args[0].lower()
    if note_name in custom_notes:
        await update.message.reply_text(custom_notes[note_name])

def main():
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
    
    # 🌟 എല്ലാ ടെക്സ്റ്റ്/മീഡിയ മെസ്സേജുകൾക്കും റിയാക്ഷൻ നൽകാൻ ഈ ഹാൻഡ്‌ലർ സഹായിക്കുന്നു
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), random_reaction))

    print("Bot with Random Reactions is running...")
    application.run_polling()

if __name__ == "__main__":
    main()