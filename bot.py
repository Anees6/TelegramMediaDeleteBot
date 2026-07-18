import os
import asyncio
from telegram import Update, ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# നിങ്ങളുടെ ടെലിഗ്രാം ബോട്ട് കീ (Token)
BOT_TOKEN = "8397424887:AAEyNXWcGS6e9NoJ_JrUw_TB6ulRlcm-vL4"
GROUP_LINK = "https://t.me/+imWG8JPfw6cyMTQ1"

# വാണിംഗുകളും നോട്ടുകളും താൽക്കാലികമായി സൂക്ഷിക്കാൻ (Memory Storage)
user_warnings = {}
custom_notes = {
    "rules": "📜 ഗ്രൂപ്പ് നിയമങ്ങൾ അനുസരിക്കക്കുക. പരസ്പരം ബഹുമാനിക്കുക.",
}

# /start കമാൻഡ് (ഇതിൽ ഹെൽപ്പ് ബട്ടണും ഗ്രൂപ്പ് ലിങ്കും ഉണ്ടാകും)
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Help & Commands 📜", callback_data="help_menu")],
        [InlineKeyboardButton("Join Our Group 🔗", url=GROUP_LINK)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"ഹലോ! ഞാൻ നിങ്ങളുടെ ഗ്രൂപ്പ് മാനേജ്മെന്റ് ബോട്ട് ആണ്. റോസ് ബോട്ട് പോലുള്ള ഫീച്ചറുകൾ എന്നിൽ ലഭ്യമാണ്.\n\n"
        f"കമാൻഡുകൾ മനസ്സിലാക്കാൻ താഴെയുള്ള ബട്ടൺ ക്ലിക്ക് ചെയ്യുക അല്ലെങ്കിൽ /help എന്ന് ടൈപ്പ് ചെയ്യുക.",
        reply_markup=reply_markup
    )

# /help കമാൻഡ് (എല്ലാ ഫങ്ഷനുകളും കാണിക്കും)
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🛠 **ഗ്രൂപ്പ് മാനേജ്മെന്റ് കമാൻഡുകൾ (Miss Rose പോലെ):**\n\n"
        "🛑 **Ban ഫീച്ചറുകൾ:**\n"
        "• `/ban` - ഒരു യൂസറെ ഗ്രൂപ്പിൽ നിന്ന് സ്ഥിരമായി പുറത്താക്കാൻ (മെസ്സേജിന് റിപ്ലൈ ചെയ്യുക)\n\n"
        "👋 **Kick ഫീച്ചറുകൾ:**\n"
        "• `/kick` - യൂസറെ ഗ്രൂപ്പിൽ നിന്ന് പുറത്താക്കാൻ (വീണ്ടും ജോയിൻ ചെയ്യാം)\n\n"
        "🤫 **Mute ഫീച്ചറുകൾ:**\n"
        "• `/mute` - യൂസറുടെ മെസ്സേജ് അയക്കാനുള്ള അനുവാദം തടയാൻ\n"
        "• `/unmute` - തിരികെ സംസാരിക്കാൻ അനുവാദം നൽകാൻ\n\n"
        "⚠️ **Warning ഫീച്ചറുകൾ:**\n"
        "• `/warn` - യൂസറിന് ഒരു വാണിംഗ് നൽകാൻ (3 വാണിംഗ് ആയാൽ ബോട്ട് സ്വയം BAN ചെയ്യും)\n\n"
        "📝 **Notes ഫീച്ചറുകൾ:**\n"
        "• `/save <note_name> <content>` - പുതിയ നോട്ട് സേവ് ചെയ്യാൻ (ഉദാഹരണം: `/save rules പരസ്പരം ബഹുമാനിക്കുക`)\n"
        "• `/get <note_name>` - സേവ് ചെയ്ത നോട്ട് കാണാൻ (ഉദാഹരണം: `/get rules`)\n\n"
        "✨ **Welcome:** പുതിയ ആളുകൾ ഗ്രൂപ്പിൽ വരുമ്പോൾ ബോട്ട് സ്വയം സ്വാഗതം ചെയ്യും."
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

# സ്റ്റാർട്ടിലെ ബട്ടൺ ക്ലിക്ക് ചെയ്യുമ്പോൾ ഉള്ള റെസ്‌പോൺസ്
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "help_menu":
        help_text = (
            "🛠 **ലഭ്യമായ പ്രധാന കമാൻഡുകൾ:**\n\n"
            "• `/ban` - ഗ്രൂപ്പിൽ നിന്ന് പുറത്താക്കാൻ\n"
            "• `/kick` - റിമൂവ് ചെയ്യാൻ\n"
            "• `/mute` - മെസ്സേജ് ബ്ലോക്ക് ചെയ്യാൻ\n"
            "• `/warn` - വാണിംഗ് നൽകാൻ (3/3 ആയാൽ Ban)\n"
            "• `/save <പേര്> <വിവരം>` - നോട്ട് സൂക്ഷിക്കാൻ\n"
            "• `/get <പേര്>` - നോട്ട് കാണാൻ\n\n"
            "കൂടുതൽ വിവരങ്ങൾക്ക് ഗ്രൂപ്പിലോ ചാറ്റിലോ നേരിട്ട് `/help` എന്ന് ടൈപ്പ് ചെയ്യുക."
        )
        await query.edit_message_text(text=help_text)

# 1. സ്വാഗതം ചെയ്യൽ (Welcome Message)
async def welcome_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        if not member.is_bot:
            await update.message.reply_text(
                f"ഹലോ {member.mention_markdown_v2()} 👋!\n"
                f"ഞങ്ങളുടെ ഗ്രൂപ്പിലേക്ക് സ്വാഗതം\\! ✨"
            )

# അഡ്മിൻ ആണോ എന്ന് പരിശോധിക്കുന്ന ഫങ്ഷൻ
async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if update.effective_chat.type == "private":
        return True
    member = await context.bot.get_chat_member(update.effective_chat.id, update.effective_user.id)
    return member.status in ["administrator", "creator"]

# 2. Ban ചെയ്യാൻ (/ban)
async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private": return
    if not await is_admin(update, context): return
    if not update.message.reply_to_message:
        return await update.message.reply_text("❌ ആരെയാണ് ban ചെയ്യേണ്ടത്? ആ മെസ്സേജിന് റിപ്ലൈ ആയി /ban എന്ന് ടൈപ്പ് ചെയ്യുക.")

    target_user = update.message.reply_to_message.from_user
    await context.bot.ban_chat_member(update.effective_chat.id, target_user.id)
    await update.message.reply_text(f"🛑 {target_user.mention_markdown_v2()} ഗ്രൂപ്പിൽ നിന്നും Ban ചെയ്യപ്പെട്ടു\\.")

# 3. Kick ചെയ്യാൻ (/kick)
async def kick_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private": return
    if not await is_admin(update, context): return
    if not update.message.reply_to_message:
        return await update.message.reply_text("❌ ആരുടെ മെസ്സേജിനാണോ റിപ്ലൈ നൽകേണ്ടത് അതിൽ നൽകുക.")

    target_user = update.message.reply_to_message.from_user
    await context.bot.ban_chat_member(update.effective_chat.id, target_user.id)
    await context.bot.unban_chat_member(update.effective_chat.id, target_user.id)
    await update.message.reply_text(f"👋 {target_user.mention_markdown_v2()} ഗ്രൂപ്പിൽ നിന്നും പുറത്താക്കപ്പെട്ടു\\.")

# 4. Mute ചെയ്യാൻ (/mute)
async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private": return
    if not await is_admin(update, context): return
    if not update.message.reply_to_message: return

    target_user = update.message.reply_to_message.from_user
    await context.bot.restrict_chat_member(update.effective_chat.id, target_user.id, ChatPermissions(can_send_messages=False))
    await update.message.reply_text(f"🤫 {target_user.mention_markdown_v2()} Mute ചെയ്യപ്പെട്ടു\\. ഇനി മെസ്സേജ് അയക്കാൻ കഴിയില്ല\\.")

# 5. Unmute ചെയ്യാൻ (/unmute)
async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private": return
    if not await is_admin(update, context): return
    if not update.message.reply_to_message: return

    target_user = update.message.reply_to_message.from_user
    await context.bot.restrict_chat_member(update.effective_chat.id, target_user.id, ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True, can_add_web_page_previews=True))
    await update.message.reply_text(f"🔊 {target_user.mention_markdown_v2()} അൺമ్యూട്ട് ചെയ്യപ്പെട്ടു\\.")

# 6. Warning നൽകാൻ (/warn)
async def warn_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private": return
    if not await is_admin(update, context): return
    if not update.message.reply_to_message:
        return await update.message.reply_text("❌ ആർക്കാണോ വാണിംഗ് നൽകേണ്ടത് ആ മെസ്സേജിന് റിപ്ലൈ ആയി /warn എന്ന് ടൈപ്പ് ചെയ്യുക.")

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
    if not await is_admin(update, context): return
    if len(context.args) < 2:
        return await update.message.reply_text("❌ ഉപയോഗിക്കേണ്ട വിധം: `/save <note_name> <content>`")
    
    note_name = context.args[0].lower()
    note_content = " ".join(context.args[1:])
    custom_notes[note_name] = note_content
    await update.message.reply_text(f"✅ നോട്ട് *'{note_name}'* വിജയകരമായി സേവ് ചെയ്തു\\.", parse_mode="MarkdownV2")

# 8. Note വിളിച്ചുവരുത്താൻ (/get)
async def get_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        return await update.message.reply_text("❌ ഉപയോഗിക്കേണ്ട വിധം: `/get <note_name>`")
    
    note_name = context.args[0].lower()
    if note_name in custom_notes:
        await update.message.reply_text(custom_notes[note_name])
    else:
        await update.message.reply_text("❌ അങ്ങനെയൊരു നോട്ട് കണ്ടെത്തിയില്ല\\.")

def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # കമാൻഡുകൾ രജിസ്റ്റർ ചെയ്യുന്നു
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("ban", ban_user))
    application.add_handler(CommandHandler("kick", kick_user))
    application.add_handler(CommandHandler("mute", mute_user))
    application.add_handler(CommandHandler("unmute", unmute_user))
    application.add_handler(CommandHandler("warn", warn_user))
    application.add_handler(CommandHandler("save", save_note))
    application.add_handler(CommandHandler("get", get_note))
    
    # ഇൻലൈൻ ബട്ടൺ ക്ലിക്ക് ഹാൻഡ്‌ലർ
    application.add_handler(CallbackQueryHandler(button_click))
    
    # വെൽക്കം മെസ്സേജ് ഹാൻഡ്‌ലർ
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_member))

    print("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()