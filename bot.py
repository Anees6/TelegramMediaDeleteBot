import logging
from telegram import Update, ChatPermissions
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    filters
)

# ----------------- കോൺഫിഗറേഷൻ -----------------
TOKEN = "8397424887:AAEyNXWcGS6e9NoJ_JrUw_TB6ulRlcm-vL4"

# ലോഗിങ് സെറ്റപ്പ്
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ----------------- ഹെൽപ്പർ ഫങ്ഷനുകൾ -----------------

# കമാൻഡ് അടിക്കുന്നത് അഡ്മിൻ ആണോ എന്ന് പരിശോധിക്കാൻ
async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    chat = update.effective_chat
    user = update.effective_user
    
    if chat.type == "private":
        return False
        
    member = await chat.get_member(user.id)
    return member.status in ["administrator", "creator"]

# 10 സെക്കൻഡ് കഴിഞ്ഞാൽ മെസ്സേജ് ഡിലീറ്റ് ചെയ്യാനുള്ള ഫങ്ക്ഷൻ
async def delete_message_job(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    try:
        await context.bot.delete_message(chat_id=job.chat_id, message_id=job.data)
    except Exception:
        pass

# ----------------- ബോട്ട് കമാൻഡുകൾ -----------------

# 1. Ban (ബാൻ ചെയ്യാൻ - റിപ്ലൈ ആയി /ban)
async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        response = await update.message.reply_text("❌ ഈ കമാൻഡ് ഉപയോഗിക്കാൻ നിങ്ങൾക്ക് അഡ്മിൻ അനുമതിയില്ല.")
        context.job_queue.run_once(delete_message_job, 10, chat_id=update.effective_chat.id, data=response.message_id)
        return

    if not update.message.reply_to_message:
        response = await update.message.reply_text("❌ ബാൻ ചെയ്യേണ്ട വ്യക്തിയുടെ മെസ്സേജിന് റിപ്ലൈ ആയി ഈ കമാൻഡ് അടിക്കുക.")
        context.job_queue.run_once(delete_message_job, 10, chat_id=update.effective_chat.id, data=response.message_id)
        return

    target_user = update.message.reply_to_message.from_user
    try:
        await update.effective_chat.ban_member(user_id=target_user.id)
        response = await update.message.reply_text(
            f"🚫 {target_user.mention_html()} എന്ന യൂസറെ ഗ്രൂപ്പിൽ നിന്നും ബാൻ ചെയ്തിരിക്കുന്നു.",
            parse_mode="HTML",
        )
        context.job_queue.run_once(delete_message_job, 10, chat_id=update.effective_chat.id, data=response.message_id)
    except Exception as e:
        response = await update.message.reply_text(f"❌ ബാൻ ചെയ്യാൻ സാധിച്ചില്ല: {e}")
        context.job_queue.run_once(delete_message_job, 10, chat_id=update.effective_chat.id, data=response.message_id)


# 2. Unban (അൺബാൻ ചെയ്യാൻ - /unban USER_ID)
async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        response = await update.message.reply_text("❌ ഈ കമാൻഡ് ഉപയോഗിക്കാൻ നിങ്ങൾക്ക് അഡ്മിൻ അനുമതിയില്ല.")
        context.job_queue.run_once(delete_message_job, 10, chat_id=update.effective_chat.id, data=response.message_id)
        return

    if not context.args:
        response = await update.message.reply_text("❌ അൺബാൻ ചെയ്യേണ്ട യൂസറുടെ ID നൽകുക. ഉദാഹരണം: /unban 12345678")
        context.job_queue.run_once(delete_message_job, 10, chat_id=update.effective_chat.id, data=response.message_id)
        return

    try:
        user_id = int(context.args[0])
        await update.effective_chat.unban_member(user_id=user_id)
        response = await update.message.reply_text(f"✅ യൂസർ ID: {user_id} അൺബാൻ ചെയ്തിരിക്കുന്നു.")
        context.job_queue.run_once(delete_message_job, 10, chat_id=update.effective_chat.id, data=response.message_id)
    except Exception as e:
        response = await update.message.reply_text(f"❌ അൺബാൻ ചെയ്യാൻ സാധിച്ചില്ല: {e}")
        context.job_queue.run_once(delete_message_job, 10, chat_id=update.effective_chat.id, data=response.message_id)


# 3. Kick (ഗ്രൂപ്പിൽ നിന്നും പുറത്താക്കാൻ - റിപ്ലൈ ആയി /kick)
async def kick_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        response = await update.message.reply_text("❌ ഈ കമാൻഡ് ഉപയോഗിക്കാൻ നിങ്ങൾക്ക് അഡ്മിൻ അനുമതിയില്ല.")
        context.job_queue.run_once(delete_message_job, 10, chat_id=update.effective_chat.id, data=response.message_id)
        return

    if not update.message.reply_to_message:
        response = await update.message.reply_text("❌ പുറത്താക്കേണ്ട വ്യക്തിയുടെ മെസ്സേജിന് റിപ്ലൈ ആയി ഈ കമാൻഡ് അടിക്കുക.")
        context.job_queue.run_once(delete_message_job, 10, chat_id=update.effective_chat.id, data=response.message_id)
        return

    target_user = update.message.reply_to_message.from_user
    try:
        await update.effective_chat.ban_member(user_id=target_user.id)
        await update.effective_chat.unban_member(user_id=target_user.id)
        response = await update.message.reply_text(
            f"👞 {target_user.mention_html()} എന്ന യൂസറെ ഗ്രൂപ്പിൽ നിന്നും കിക്ക് ചെയ്തിരിക്കുന്നു.",
            parse_mode="HTML",
        )
        context.job_queue.run_once(delete_message_job, 10, chat_id=update.effective_chat.id, data=response.message_id)
    except Exception as e:
        response = await update.message.reply_text(f"❌ കിക്ക് ചെയ്യാൻ സാധിച്ചില്ല: {e}")
        context.job_queue.run_once(delete_message_job, 10, chat_id=update.effective_chat.id, data=response.message_id)


# 4. Mute (മ്യൂട്ട് ചെയ്യാൻ - റിപ്ലൈ ആയി /mute)
async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        response = await update.message.reply_text("❌ ഈ കമാൻഡ് ഉപയോഗിക്കാൻ നിങ്ങൾക്ക് അഡ്മിൻ അനുമതിയില്ല.")
        context.job_queue.run_once(delete_message_job, 10, chat_id=update.effective_chat.id, data=response.message_id)
        return

    if not update.message.reply_to_message:
        response = await update.message.reply_text("❌ മ്യൂട്ട് ചെയ്യേണ്ട വ്യക്തിയുടെ മെസ്സേജിന് റിപ്ലൈ ആയി ഈ കമാൻഡ് അടിക്കുക.")
        context.job_queue.run_once(delete_message_job, 10, chat_id=update.effective_chat.id, data=response.message_id)
        return

    target_user = update.message.reply_to_message.from_user
    try:
        mute_permissions = ChatPermissions(can_send_messages=False)
        await update.effective_chat.restrict_member(user_id=target_user.id, permissions=mute_permissions)
        response = await update.message.reply_text(
            f"🔇 {target_user.mention_html()} എന്ന യൂസറെ മ്യൂട്ട് ചെയ്തിരിക്കുന്നു (മെസ്സേജ് അയക്കാൻ സാധിക്കില്ല).",
            parse_mode="HTML",
        )
        context.job_queue.run_once(delete_message_job, 10, chat_id=update.effective_chat.id, data=response.message_id)
    except Exception as e:
        response = await update.message.reply_text(f"❌ മ്യൂട്ട് ചെയ്യാൻ സാധിച്ചില്ല: {e}")
        context.job_queue.run_once(delete_message_job, 10, chat_id=update.effective_chat.id, data=response.message_id)


# 5. Unmute (അൺമ്യൂട്ട് ചെയ്യാൻ - റിപ്ലൈ ആയി /unmute)
async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        response = await update.message.reply_text("❌ ഈ കമാൻഡ് ഉപയോഗിക്കാൻ നിങ്ങൾക്ക് അഡ്മിൻ അനുമതിയില്ല.")
        context.job_queue.run_once(delete_message_job, 10, chat_id=update.effective_chat.id, data=response.message_id)
        return

    if not update.message.reply_to_message:
        response = await update.message.reply_text("❌ അൺമ്യൂട്ട് ചെയ്യേണ്ട വ്യക്തിയുടെ മെസ്സേജിന് റിപ്ലൈ ആയി ഈ കമാൻഡ് അടിക്കുക.")
        context.job_queue.run_once(delete_message_job, 10, chat_id=update.effective_chat.id, data=response.message_id)
        return

    target_user = update.message.reply_to_message.from_user
    try:
        unmute_permissions = ChatPermissions(
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
        await update.effective_chat.restrict_member(user_id=target_user.id, permissions=unmute_permissions)
        response = await update.message.reply_text(
            f"🔊 {target_user.mention_html()} എന്ന യൂസറെ അൺമ്യൂട്ട് ചെയ്തിരിക്കുന്നു.",
            parse_mode="HTML",
        )
        context.job_queue.run_once(delete_message_job, 10, chat_id=update.effective_chat.id, data=response.message_id)
    except Exception as e:
        response = await update.message.reply_text(f"❌ അൺമ്യൂട്ട് ചെയ്യാൻ സാധിച്ചില്ല: {e}")
        context.job_queue.run_once(delete_message_job, 10, chat_id=update.effective_chat.id, data=response.message_id)

# ----------------- മെയിൻ ഫങ്ക്ഷൻ -----------------
def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("ban", ban_user))
    application.add_handler(CommandHandler("unban", unban_user))
    application.add_handler(CommandHandler("kick", kick_user))
    application.add_handler(CommandHandler("mute", mute_user))
    application.add_handler(CommandHandler("unmute", unmute_user))

    application.run_polling()

if __name__ == "__main__":
    main()