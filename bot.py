import os
import asyncio
from telegram import Update, ChatPermissions
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# നിങ്ങളുടെ ടെലിഗ്രാം ബോട്ട് കീ (Token)
BOT_TOKEN = "8397424887:AAEyNXWcGS6e9NoJ_JrUw_TB6ulRlcm-vL4"

# /start കമാൻഡ് മെസ്സേജ് ഫങ്ഷൻ (ഗ്രൂപ്പിലും പേഴ്‌സണൽ ചാറ്റിലും വർക്ക് ആകും)
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_link = "https://t.me/+imWG8JPfw6cyMTQ1"
    await update.message.reply_text(
        f"ഹലോ! ഞങ്ങളുടെ ഗ്രൂപ്പിൽ ജോയിൻ ചെയ്യാൻ താഴെയുള്ള ലിങ്ക് ഉപയോഗിക്കുക:\n\n🔗 {group_link}"
    )

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
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    # പേഴ്‌സണൽ ചാറ്റിൽ അഡ്മിൻ ചെക്കിങ് ആവശ്യമില്ല
    if update.effective_chat.type == "private":
        return True
        
    member = await context.bot.get_chat_member(chat_id, user_id)
    return member.status in ["administrator", "creator"]

# 2. Ban ചെയ്യാൻ (/ban)
async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        return await update.message.reply_text("❌ ഈ കമാൻഡ് ഗ്രൂപ്പിൽ മാത്രമേ ഉപയോഗിക്കാൻ കഴിയൂ.")
        
    if not await is_admin(update, context):
        await update.message.reply_text("❌ ഈ കമാൻഡ് ഉപയോഗിക്കാൻ നിങ്ങൾക്ക് അനുവാദമില്ല.")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("❌ നിങ്ങൾ ആരെയാണ് ban ചെയ്യേണ്ടത്? ആ മെസ്സേജിന് റിപ്ലൈ ആയി /ban എന്ന് ടൈപ്പ് ചെയ്യുക.")
        return

    target_user = update.message.reply_to_message.from_user
    await context.bot.ban_chat_member(update.effective_chat.id, target_user.id)
    await update.message.reply_text(f"🛑 {target_user.mention_markdown_v2()} ഗ്രൂപ്പിൽ നിന്നും Ban ചെയ്യപ്പെട്ടു\\.")

# 3. Kick ചെയ്യാൻ (/kick)
async def kick_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        return await update.message.reply_text("❌ ഈ കമാൻഡ് ഗ്രൂപ്പിൽ മാത്രമേ ഉപയോഗിക്കാൻ കഴിയൂ.")
        
    if not await is_admin(update, context):
        await update.message.reply_text("❌ നിങ്ങൾക്ക് ഇതിനുള്ള അനുവാദമില്ല.")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("❌ ആരുടെ മെസ്സേജിനാണോ റിപ്ലൈ നൽകേണ്ടത് അതിൽ നൽകുക.")
        return

    target_user = update.message.reply_to_message.from_user
    await context.bot.ban_chat_member(update.effective_chat.id, target_user.id)
    await context.bot.unban_chat_member(update.effective_chat.id, target_user.id)
    await update.message.reply_text(f"👋 {target_user.mention_markdown_v2()} ഗ്രൂപ്പിൽ നിന്നും പുറത്താക്കപ്പെട്ടു\\.")

# 4. Mute ചെയ്യാൻ (/mute)
async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        return await update.message.reply_text("❌ ഈ കമാൻഡ് ഗ്രൂപ്പിൽ മാത്രമേ ഉപയോഗിക്കാൻ കഴിയൂ.")
        
    if not await is_admin(update, context):
        await update.message.reply_text("❌ നിങ്ങൾക്ക് ഇതിനുള്ള അനുവാദമില്ല.")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("❌ ആരുടെ മെസ്സേജിനാണോ റിപ്ലൈ നൽകേണ്ടത് അതിൽ നൽകുക.")
        return

    target_user = update.message.reply_to_message.from_user
    permissions = ChatPermissions(can_send_messages=False)
    await context.bot.restrict_chat_member(update.effective_chat.id, target_user.id, permissions)
    await update.message.reply_text(f"🤫 {target_user.mention_markdown_v2()} Mute ചെയ്യപ്പെട്ടു\\. ഇനി മെസ്സേജ് അയക്കാൻ കഴിയില്ല\\.")

# 5. Unmute ചെയ്യാൻ (/unmute)
async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        return await update.message.reply_text("❌ ഈ കമാൻഡ് ഗ്രൂപ്പിൽ മാത്രമേ ഉപയോഗിക്കാൻ കഴിയൂ.")
        
    if not await is_admin(update, context):
        await update.message.reply_text("❌ നിങ്ങൾക്ക് ഇതിനുള്ള അനുവാദമില്ല.")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("❌ ആരുടെ മെസ്സേജിനാണോ റിപ്ലൈ നൽകേണ്ടത് അതിൽ നൽകുക.")
        return

    target_user = update.message.reply_to_message.from_user
    permissions = ChatPermissions(
        can_send_messages=True,
        can_send_media_messages=True,
        can_send_other_messages=True,
        can_add_web_page_previews=True
    )
    await context.bot.restrict_chat_member(update.effective_chat.id, target_user.id, permissions)
    await update.message.reply_text(f"🔊 {target_user.mention_markdown_v2()} അൺമ്യൂട്ട് ചെയ്യപ്പെട്ടു\\.")

def main():
    # ബോട്ട് ആപ്ലിക്കേഷൻ സ്റ്റാർട്ട് ചെയ്യുന്നു (ഹോസ്റ്റിംഗിൽ എറർ വരാതിരിക്കാൻ ഡിഫോൾട്ട് കോൺഫിഗറേഷൻ)
    application = Application.builder().token(BOT_TOKEN).build()

    # കമാൻഡുകൾ ലിങ്ക് ചെയ്യുന്നു
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_member))
    application.add_handler(CommandHandler("ban", ban_user))
    application.add_handler(CommandHandler("kick", kick_user))
    application.add_handler(CommandHandler("mute", mute_user))
    application.add_handler(CommandHandler("unmute", unmute_user))

    print("Bot is starting...")
    application.run_polling()

if __name__ == "__main__":
    main()