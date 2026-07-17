import asyncio
import re
from threading import Thread
from flask import Flask
from telegram import Update, ChatPermissions
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# Flask വെബ് സെർവർ സെറ്റപ്പ് (Render ഹോസ്റ്റിംഗിനായി)
app = Flask(__name__)


@app.route("/")
def home():
    return "Bot is alive!"


def run_flask():
    app.run(host="0.0.0.0", port=8080)


# ബോട്ട് ടോക്കൺ
BOT_TOKEN = "8673412670:AAFW2QTdkHH_LxecEzJNE-SkflJZe1X8Y0g"
LINK_REGEX = re.compile(r"https?://\S+|www\.\S+")


# യൂസർ അഡ്മിൻ ആണോ എന്ന് പരിശോധിക്കാനുള്ള ഫംഗ്ഷൻ
async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    chat = update.effective_chat
    user = update.effective_user

    # പ്രൈവറ്റ് ചാറ്റിൽ അഡ്മിൻ ചെക്കിങ് ആവശ്യമില്ല
    if chat.type == "private":
        return True

    member = await context.bot.get_chat_member(
        chat_id=chat.id, user_id=user.id
    )
    return member.status in ["creator", "administrator"]


# സ്റ്റാർട്ട് കമാൻഡ്
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 ഹലോ! ഞാൻ ആക്ടീവ് ആണ്.\nഗ്രൂപ്പുകളിൽ ലിങ്കുകൾ അല്ലാത്ത മെസ്സേജുകൾ ഒഴിവാക്കാനും അഡ്മിൻ കമാൻഡുകൾ ചെയ്യാനും എന്നെ ഉപയോഗിക്കാം."
    )


# വാണിംഗ് മെസ്സേജ് ഡിലീറ്റ് ചെയ്യാനുള്ള ഫംഗ്ഷൻ
async def delete_warning(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    try:
        await context.bot.delete_message(
            chat_id=job.chat_id, message_id=job.data
        )
    except Exception as e:
        print(f"Error deleting warning message: {e}")


# ലിങ്കുകൾ ഫിൽട്ടർ ചെയ്യാനുള്ള ഫംഗ്ഷൻ
async def filter_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    chat = update.effective_chat
    user = update.effective_user

    if chat.type not in ["group", "supergroup"]:
        return

    # ബോട്ട് അയക്കുന്ന മെസ്സേജുകൾ ഒഴിവാക്കുക
    if user.is_bot:
        return

    # അഡ്മിൻമാർ അയക്കുന്ന മെസ്സേജുകൾ ഫിൽട്ടർ ചെയ്യരുത്
    if await is_admin(update, context):
        return

    # ലിങ്ക് ഉണ്ടെങ്കിൽ ഡിലീറ്റ് ചെയ്യരുത്
    if message.text and LINK_REGEX.search(message.text):
        return

    try:
        # 1. ലിങ്ക് അല്ലാത്ത മെസ്സേജ് ഡിലീറ്റ് ചെയ്യുന്നു
        await message.delete()

        # 2. യൂസറെ മ്യൂട്ട് ചെയ്യുന്നു
        mute_permissions = ChatPermissions(can_send_messages=False)
        await chat.restrict_member(
            user_id=user.id, permissions=mute_permissions
        )

        # 3. വാണിംഗ് മെസ്സേജ് അയക്കുന്നു
        warning_msg = await context.bot.send_message(
            chat_id=chat.id,
            text=f"⚠️ {user.mention_html()}, ഈ ഗ്രൂപ്പിൽ ലിങ്കുകൾ മാത്രമേ അനുവദിക്കൂ! നിങ്ങളുടെ മെസ്സേജ് ഡിലീറ്റ് ചെയ്ത് നിങ്ങളെ മ്യൂട്ട് ചെയ്തിരിക്കുന്നു.",
            parse_mode="HTML",
        )

        # 4. 1 മിനിറ്റിന് (60 സെക്കൻഡ്) ശേഷം വാണിംഗ് മെസ്സേജ് ഡിലീറ്റ് ചെയ്യുന്നു
        context.job_queue.run_once(
            delete_warning,
            when=60,
            chat_id=chat.id,
            data=warning_msg.message_id,
        )
    except Exception as e:
        print(f"Error in filter: {e}")


# --- ഗ്രൂപ്പ് മാനേജ്മെന്റ് കമാൻഡുകൾ ---


# 1. Ban (ബാൻ ചെയ്യാൻ - മറുപടി നൽകുന്ന മെസ്സേജിന് നേരെ /ban എന്ന് അടിക്കുക)
async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text(
            "❌ ഈ കമാൻഡ് ഉപയോഗിക്കാൻ നിങ്ങൾക്ക് അഡ്മിൻ അനുമതിയില്ല."
        )
        return

    if not update.message.reply_to_message:
        await update.message.reply_text(
            "❌ ആരെയാണ് ബാൻ ചെയ്യേണ്ടത് എന്ന് കാണിക്കാൻ ആ വ്യക്തിയുടെ മെസ്സേജിന് റിപ്ലൈ ആയി ഈ കമാൻഡ് അടിക്കുക."
        )
        return

    target_user = update.message.reply_to_message.from_user
    try:
        await update.effective_chat.ban_member(user_id=target_user.id)
        await update.message.reply_text(
            f"🚫 {target_user.mention_html()} എന്ന യൂസറെ ഗ്രൂപ്പിൽ നിന്നും ബാൻ ചെയ്തിരിക്കുന്നു.",
            parse_mode="HTML",
        )
    except Exception as e:
        await update.message.reply_text(f"❌ ബാൻ ചെയ്യാൻ സാധിച്ചില്ല: {e}")


# 2. Unban (അൺബാൻ ചെയ്യാൻ - /unban USER_ID)
async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text(
            "❌ ഈ കമാൻഡ് ഉപയോഗിക്കാൻ നിങ്ങൾക്ക് അഡ്മിൻ അനുമതിയില്ല."
        )
        return

    if not context.args:
        await update.message.reply_text(
            "❌ അൺബാൻ ചെയ്യേണ്ട യൂസറുടെ ID നൽകുക. ഉദാഹരണം: `/unban 12345678`"
        )
        return

    try:
        user_id = int(context.args[0])
        await update.effective_chat.unban_member(user_id=user_id)
        await update.message.reply_text(
            f"✅ യൂസർ ID: {user_id} അൺബാൻ ചെയ്തിരിക്കുന്നു."
        )
    except Exception as e:
        await update.message.reply_text(f"❌ അൺബാൻ ചെയ്യാൻ സാധിച്ചില്ല: {e}")


# 3. Kick (ഗ്രൂപ്പിൽ നിന്നും പുറത്താക്കാൻ - റിപ്ലൈ ആയി /kick)
async def kick_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text(
            "❌ ഈ കമാൻഡ് ഉപയോഗിക്കാൻ നിങ്ങൾക്ക് അഡ്മിൻ അനുമതിയില്ല."
        )
        return

    if not update.message.reply_to_message:
        await update.message.reply_text(
            "❌ പുറത്താക്കേണ്ട വ്യക്തിയുടെ മെസ്സേജിന് റിപ്ലൈ ആയി ഈ കമാൻഡ് അടിക്കുക."
        )
        return

    target_user = update.message.reply_to_message.from_user
    try:
        # ban ചെയ്ത് ഉടനെ unban ചെയ്താൽ മെമ്പർ ഗ്രൂപ്പിൽ നിന്നും ഒഴിവാക്കപ്പെടും (Kick)
        await update.effective_chat.ban_member(user_id=target_user.id)
        await update.effective_chat.unban_member(user_id=target_user.id)
        await update.message.reply_text(
            f"👞 {target_user.mention_html()} എന്ന യൂസറെ ഗ്രൂപ്പിൽ നിന്നും കിക്ക് ചെയ്തിരിക്കുന്നു.",
            parse_mode="HTML",
        )
    except Exception as e:
        await update.message.reply_text(f"❌ കിക്ക് ചെയ്യാൻ സാധിച്ചില്ല: {e}")


# 4. Mute (മ്യൂട്ട് ചെയ്യാൻ - റിപ്ലൈ ആയി /mute)
async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text(
            "❌ ഈ കമാൻഡ് ഉപയോഗിക്കാൻ നിങ്ങൾക്ക് അഡ്മിൻ അനുമതിയില്ല."
        )
        return

    if not update.message.reply_to_message:
        await update.message.reply_text(
            "❌ മ്യൂട്ട് ചെയ്യേണ്ട വ്യക്തിയുടെ മെസ്സേജിന് റിപ്ലൈ ആയി ഈ കമാൻഡ് അടിക്കുക."
        )
        return

    target_user = update.message.reply_to_message.from_user
    try:
        mute_permissions = ChatPermissions(can_send_messages=False)
        await update.effective_chat.restrict_member(
            user_id=target_user.id, permissions=mute_permissions
        )
        await update.message.reply_text(
            f"🔇 {target_user.mention_html()} എന്ന യൂസറെ മ്യൂട്ട് ചെയ്തിരിക്കുന്നു (മെസ്സേജ് അയക്കാൻ സാധിക്കില്ല).",
            parse_mode="HTML",
        )
    except Exception as e:
        await update.message.reply_text(f"❌ മ്യൂട്ട് ചെയ്യാൻ സാധിച്ചില്ല: {e}")


# 5. Unmute (അൺമ്യൂട്ട് ചെയ്യാൻ - റിപ്ലൈ ആയി /unmute)
async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text(
            "❌ ഈ കമാൻഡ് ഉപയോഗിക്കാൻ നിങ്ങൾക്ക് അഡ്മിൻ അനുമതിയില്ല."
        )
        return

    if not update.message.reply_to_message:
        await update.message.reply_text(
            "❌ അൺമ്യൂട്ട് ചെയ്യേണ്ട വ്യക്തിയുടെ മെസ്സേജിന് റിപ്ലൈ ആയി ഈ കമാൻഡ് അടിക്കുക."
        )
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
            can_add_web_page_previews=True,
        )
        await update.effective_chat.restrict_member(
            user_id=target_user.id, permissions=unmute_permissions
        )
        await update.message.reply_text(
            f"🔊 {target_user.mention_html()} അൺമ്യൂട്ട് ചെയ്യപ്പെട്ടിരിക്കുന്നു. ഇനി മെസ്സേജുകൾ അയക്കാം.",
            parse_mode="HTML",
        )
    except Exception as e:
        await update.message.reply_text(f"❌ അൺമ്യൂട്ട് ചെയ്യാൻ സാധിച്ചില്ല: {e}")


def main():
    # വെബ് സെർവർ സ്റ്റാർട്ട് ചെയ്യുന്നു
    Thread(target=run_flask).start()

    # ബോട്ട് സ്റ്റാർട്ട് ചെയ്യുന്നു
    application = Application.builder().token(BOT_TOKEN).build()

    # ഹാൻഡ്‌ലറുകൾ ചേർക്കുന്നു
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ban", ban_user))
    application.add_handler(CommandHandler("unban", unban_user))
    application.add_handler(CommandHandler("kick", kick_user))
    application.add_handler(CommandHandler("mute", mute_user))
    application.add_handler(CommandHandler("unmute", unmute_user))

    # ലിങ്കുകൾ അല്ലാത്തവ ഫിൽട്ടർ ചെയ്യാൻ
    application.add_handler(
        MessageHandler(filters.ALL & ~filters.COMMAND, filter_messages)
    )

    print("Bot is running...")
    application.run_polling()


if __name__ == "__main__":
    main()