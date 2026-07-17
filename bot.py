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

app = Flask(__name__)


@app.route("/")
def home():
    return "Bot is alive!"


def run_flask():
    app.run(host="0.0.0.0", port=8080)


# ബോട്ട് ടോക്കൺ
BOT_TOKEN = "8673412670:AAFW2QTdkHH_LxecEzJNE-SkflJZe1X8Y0g"
LINK_REGEX = re.compile(r"https?://\S+|www\.\S+")

warning_timeouts = {}  # {chat_id: seconds}

# ഓരോ ഗ്രൂപ്പിലെയും മീഡിയ ഓട്ടോ ഡിലീറ്റ് സമയം മിനിറ്റിൽ സൂക്ഷിക്കാൻ
# 0 എന്നാൽ ഓഫ് ആണെന്ന് അർത്ഥം
auto_delete_minutes = {}  # {chat_id: minutes}

DEFAULT_TIMEOUT = 60  # ഡിഫോൾട്ട് സമയം


# അഡ്മിൻ ചെക്കിങ് ഫംഗ്ഷൻ
async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    chat = update.effective_chat
    user = update.effective_user
    if chat.type == "private":
        return True
    try:
        member = await context.bot.get_chat_member(
            chat_id=chat.id, user_id=user.id
        )
        return member.status in ["creator", "administrator"]
    except Exception:
        return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 ഹലോ! അഡ്വാൻസ്ഡ് ഗ്രൂപ്പ് മാനേജ്മെന്റ് ബോട്ട് റെഡിയാണ്.\nകമാൻഡുകൾ അറിയാൻ ഗ്രൂപ്പിൽ /help എന്ന് അടിക്കുക."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🛠 **ലഭ്യമായ അഡ്മിൻ കമാൻഡുകൾ (Admins Only):**\n\n"
        "⏱ **⏱ മീഡിയ / ലിങ്ക് ഓട്ടോ ഡിലീറ്റ് ടൈമിംഗ്:**\n"
        "🔹 `/autodel [മിനിറ്റ്]` - മീഡിയകൾ ഡിലീറ്റ് ആകേണ്ട സമയം സെറ്റ് ചെയ്യാൻ.\n"
        "👉 *ലഭ്യമായ സമയങ്ങൾ:* 1, 10, 15, 20, 30 മിനിറ്റുകൾ.\n"
        "ഉദാഹരണത്തിന്: `/autodel 10` (10 മിനിറ്റിനുള്ളിൽ ഡിലീറ്റ് ആകും)\n"
        "🔹 `/autodel off` - ഓട്ടോ ഡിലീറ്റ് ഫീച്ചർ ഓഫ് ചെയ്യാൻ.\n\n"
        "📌 **ഗ്രൂപ്പ് കൺട്രോൾ:**\n"
        "🔹 `/mute` - റിപ്ലൈ നൽകി യൂസറെ മ്യൂട്ട് ചെയ്യാൻ\n"
        "🔹 `/unmute` - റിപ്ലൈ നൽകി അൺമ്യൂട്ട് ചെയ്യാൻ\n"
        "🔹 `/kick` - റിപ്ലൈ നൽകി കിക്ക് ചെയ്യാൻ\n"
        "🔹 `/ban` - റിപ്ലൈ നൽകി ബാൻ ചെയ്യാൻ\n"
        "🔹 `/unban [User_ID]` - ബാൻ മാറ്റാൻ\n\n"
        "⏱ **ടെക്സ്റ്റ് മെസ്സേജ് ഫിൽട്ടർ ടൈമിംഗ്:**\n"
        "🔹 `/settimeout [സെക്കൻഡ്]` - വാണിംഗ് മെസ്സേജ് ഡിലീറ്റ് ആകേണ്ട സമയം മാറ്റാൻ\n"
        "🔹 `/gettimeout` - നിലവിലെ വാണിംഗ് ടൈം അറിയാൻ"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


# മെസ്സേജുകൾ തനിയെ ഡിലീറ്റ് ചെയ്യാനുള്ള ഫംഗ്ഷൻ
async def delete_msg_job(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    try:
        await context.bot.delete_message(
            chat_id=job.chat_id, message_id=job.data
        )
    except Exception as e:
        print(f"Error deleting message: {e}")


# --- സമയം സെറ്റ് ചെയ്യാനുള്ള പുതിയ കമാൻഡ് ഫംഗ്ഷൻ ---
async def set_auto_delete_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return

    if not context.args:
        await update.message.reply_text(
            "❌ കമാൻഡിനൊപ്പം മിനിറ്റ് നൽകുക.\nഉദാഹരണം: `/autodel 10` അല്ലെങ്കിൽ `/autodel off`"
        )
        return

    arg = context.args[0].lower()
    chat_id = update.effective_chat.id

    if arg == "off":
        auto_delete_minutes[chat_id] = 0
        await update.message.reply_text(
            "❌ **മീഡിയ ഓട്ടോ-ഡിലീറ്റ് ഓഫ് ചെയ്തു!** ഇനി മീഡിയകൾ തനിയെ ഡിലീറ്റ് ആകില്ല.",
            parse_mode="Markdown",
        )
        return

    # അനുവദനീയമായ മിനിറ്റുകൾ മാത്രം പരിശോധിക്കുന്നു
    allowed_minutes = [1, 10, 15, 20, 30]
    try:
        minutes = int(arg)
        if minutes in allowed_minutes:
            auto_delete_minutes[chat_id] = minutes
            await update.message.reply_text(
                f"✅ **മീഡിയ ഓട്ടോ-ഡിലീറ്റ് സെറ്റ് ചെയ്തു!** ഇനി ഗ്രൂപ്പിൽ വരുന്ന എല്ലാ മീഡിയകളും ലിങ്കുകളും **{minutes} മിനിറ്റിനുള്ളിൽ** തനിയെ ഡിലീറ്റ് ചെയ്യപ്പെടും.",
                parse_mode="Markdown",
            )
        else:
            await update.message.reply_text(
                "❌ തെറ്റായ സമയം! ദയവായി 1, 10, 15, 20, അല്ലെങ്കിൽ 30 ഇതിലൊന്ന് നൽകുക.\nഉദാഹരണം: `/autodel 15`"
            )
    except ValueError:
        await update.message.reply_text(
            "❌ ദയവായി ഒരു കൃത്യമായ നമ്പർ നൽകുക. ഉദാഹരണം: `/autodel 10`"
        )


# ഗ്രൂപ്പിലെ മെസ്സേജുകൾ പരിശോധിക്കുന്ന ഫംഗ്ഷൻ
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    chat = update.effective_chat
    user = update.effective_user

    if chat.type not in ["group", "supergroup"] or user.is_bot:
        return

    # അഡ്മിൻമാർ അയക്കുന്ന ഒന്നിനെയും ബോട്ട് ഡിലീറ്റ് ചെയ്യില്ല
    if await is_admin(update, context):
        return

    chat_id = chat.id
    is_link = message.text and LINK_REGEX.search(message.text)
    is_media = bool(
        message.photo
        or message.video
        or message.audio
        or message.document
        or message.voice
        or message.video_note
    )

    chosen_minutes = auto_delete_minutes.get(chat_id, 0)

    # --- 1. മീഡിയ & ലിങ്ക് നിശ്ചിത മിനിറ്റിൽ ഡിലീറ്റ് ചെയ്യുന്ന ഫീച്ചർ (ഓൺ ആണെങ്കിൽ) ---
    if chosen_minutes > 0 and (is_media or is_link):
        # മിനിറ്റിനെ സെക്കൻഡിലേക്ക് മാറ്റുന്നു (Minutes * 60)
        seconds_to_wait = chosen_minutes * 60
        context.job_queue.run_once(
            delete_msg_job, when=seconds_to_wait, chat_id=chat_id, data=message.message_id
        )
        return

    # --- 2. ടെക്സ്റ്റ് മെസ്സേജ് ഫിൽട്ടർ (ലിങ്ക് അല്ലാത്ത സാധാ ടെക്സ്റ്റ് മെസ്സേജ് അയച്ചാൽ മ്യൂട്ട് ചെയ്യുന്ന സിസ്റ്റം) ---
    if not is_link and not is_media:
        try:
            await message.delete()

            await chat.restrict_member(
                user_id=user.id,
                permissions=ChatPermissions(can_send_messages=False),
            )

            warning_msg = await context.bot.send_message(
                chat_id=chat_id,
                text=f"⚠️ {user.mention_html()}, ഈ ഗ്രൂപ്പിൽ ലിങ്കുകളും മീഡിയകളും മാത്രമേ അനുവദിക്കൂ! നിങ്ങളുടെ ടെക്സ്റ്റ് മെസ്സേജ് ഡിലീറ്റ് ചെയ്ത് നിങ്ങളെ മ്യൂട്ട് ചെയ്തിരിക്കുന്നു.",
                parse_mode="HTML",
            )

            timeout = warning_timeouts.get(chat_id, DEFAULT_TIMEOUT)
            context.job_queue.run_once(
                delete_msg_job, when=timeout, chat_id=chat_id, data=warning_msg.message_id
            )
        except Exception as e:
            print(f"Error in filter: {e}")


# --- മറ്റ് ബേസിക് മാനേജ്മെന്റ് കമാൻഡുകൾ ---


async def set_timeout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not context.args:
        await update.message.reply_text("❌ സമയം സെക്കൻഡിൽ നൽകുക. ഉദാ: `/settimeout 15`")
        return
    try:
        seconds = int(context.args[0])
        if seconds < 5:
            await update.message.reply_text("❌ സമയം കുറഞ്ഞത് 5 സെക്കൻഡ് വേണം.")
            return
        warning_timeouts[update.effective_chat.id] = seconds
        await update.message.reply_text(f"✅ വാണിംഗ് സമയം {seconds} സെക്കൻഡ് ആക്കി.")
    except ValueError:
        await update.message.reply_text("❌ കൃത്യമായ ഒരു സംഖ്യ നൽകുക.")


async def get_timeout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    current_time = warning_timeouts.get(update.effective_chat.id, DEFAULT_TIMEOUT)
    await update.message.reply_text(f"⏱ നിലവിലെ വാണിംഗ് ടൈം: {current_time} സെക്കൻഡ്.")


async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ റിപ്ലൈ ആയി ഈ കമാൻഡ് അടിക്കുക.")
        return
    target_user = update.message.reply_to_message.from_user
    try:
        await update.effective_chat.ban_member(user_id=target_user.id)
        await update.message.reply_text(f"🚫 {target_user.mention_html()} ബാൻ ചെയ്യപ്പെട്ടു.", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"❌ പരാജയപ്പെട്ടു: {e}")


async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not context.args:
        await update.message.reply_text("❌ യൂസർ ID നൽകുക. ഉദാ: `/unban 12345`")
        return
    try:
        user_id = int(context.args[0])
        await update.effective_chat.unban_member(user_id=user_id)
        await update.message.reply_text(f"✅ ID: {user_id} അൺബാൻ ചെയ്തു.")
    except Exception as e:
        await update.message.reply_text(f"❌ പരാജയപ്പെട്ടു: {e}")


async def kick_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ റിപ്ലൈ ആയി ഈ കമാൻഡ് അടിക്കുക.")
        return
    target_user = update.message.reply_to_message.from_user
    try:
        await update.effective_chat.ban_member(user_id=target_user.id)
        await update.effective_chat.unban_member(user_id=target_user.id)
        await update.message.reply_text(f"👞 {target_user.mention_html()} കിക്ക് ചെയ്യപ്പെട്ടു.", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"❌ പരാജയപ്പെട്ടു: {e}")


async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ റിപ്ലൈ ആയി ഈ കമാൻഡ് അടിക്കുക.")
        return
    target_user = update.message.reply_to_message.from_user
    try:
        await update.effective_chat.restrict_member(user_id=target_user.id, permissions=ChatPermissions(can_send_messages=False))
        await update.message.reply_text(f"🔇 {target_user.mention_html()} മ്യൂട്ട് ചെയ്യപ്പെട്ടു.", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"❌ പരാജയപ്പെട്ടു: {e}")


async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ റിപ്ലൈ ആയി ഈ കമാൻഡ് അടിക്കുക.")
        return
    target_user = update.message.reply_to_message.from_user
    try:
        await update.effective_chat.restrict_member(
            user_id=target_user.id,
            permissions=ChatPermissions(
                can_send_messages=True, can_send_audios=True, can_send_documents=True,
                can_send_photos=True, can_send_videos=True, can_send_video_notes=True,
                can_send_voice_notes=True, can_send_polls=True, can_send_other_messages=True,
                can_add_web_page_previews=True
            )
        )
        await update.message.reply_text(f"🔊 {target_user.mention_html()} അൺമ്യൂട്ട് ചെയ്യപ്പെട്ടു.", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"❌ പരാജയപ്പെട്ടു: {e}")


def main():
    Thread(target=run_flask).start()

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("ban", ban_user))
    application.add_handler(CommandHandler("unban", unban_user))
    application.add_handler(CommandHandler("kick", kick_user))
    application.add_handler(CommandHandler("mute", mute_user))
    application.add_handler(CommandHandler("unmute", unmute_user))

    application.add_handler(CommandHandler("settimeout", set_timeout))
    application.add_handler(CommandHandler("gettimeout", get_timeout))

    # ടൈമിംഗ് സെറ്റ് ചെയ്യാനുള്ള പുതിയ കമാൻഡ് ഹാൻഡ്‌ലർ
    application.add_handler(CommandHandler("autodel", set_auto_delete_time))

    application.add_handler(
        MessageHandler(filters.ALL & ~filters.COMMAND, handle_messages)
    )

    print("Bot is running...")
    application.run_polling()


if __name__ == "__main__":
    main()