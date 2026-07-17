import re
import random
import logging
import asyncio
from telegram import Update, ChatPermissions, ReactionTypeEmoji
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ലോഗിൻ വിവരങ്ങൾ അറിയാൻ (Debugging)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

# 🔑 നിങ്ങളുടെ ബോട്ട് ടോക്കൺ
BOT_TOKEN = "8397424887:AAEyNXWcGS6e9NoJ_JrUw_TB6ulRlcm-vL4"

# ലിങ്കുകൾ കണ്ടുപിടിക്കാനുള്ള റീജെക്സ് (Regex)
LINK_REGEX = r'(https?://[^\s]+|www\.[^\s]+)'

# ലിങ്ക് ഇടുമ്പോൾ കൊടുക്കേണ്ട റാൻഡം ഇമോജി ലിസ്റ്റ്
REACTIONS = ["👍", "🔥", "❤️", "👏", "🤩", "🎉", "👌"]

# യൂസർ അഡ്മിൻ ആണോ എന്ന് പരിശോധിക്കാനുള്ള ഫങ്ക്ഷൻ
async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    chat_member = await context.bot.get_chat_member(
        chat_id=update.effective_chat.id, 
        user_id=update.effective_user.id
    )
    return chat_member.status in ['creator', 'administrator']


# 1. Ban (ബാൻ ചെയ്യാൻ - റിപ്ലൈ ആയി /ban)
async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text("❌ ഈ കമാൻഡ് ഉപയോഗിക്കാൻ നിങ്ങൾക്ക് അഡ്മിൻ അനുമതിയില്ല.")
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ ബാൻ ചെയ്യേണ്ട വ്യക്തിയുടെ മെസ്സേജിന് റിപ്ലൈ ആയി ഈ കമാൻഡ് അടിക്കുക.")
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
        await update.message.reply_text("❌ ഈ കമാൻഡ് ഉപയോഗിക്കാൻ നിങ്ങൾക്ക് അഡ്മിൻ അനുമതിയില്ല.")
        return
    if not context.args:
        await update.message.reply_text("❌ അൺബാൻ ചെയ്യേണ്ട യൂസറുടെ ID നൽകുക. ഉദാഹരണം: /unban 12345678")
        return

    try:
        user_id = int(context.args[0])
        await update.effective_chat.unban_member(user_id=user_id)
        await update.message.reply_text(f"✅ യൂസർ ID: {user_id} അൺബാൻ ചെയ്തിരിക്കുന്നു.")
    except Exception as e:
        await update.message.reply_text(f"❌ അൺബാൻ ചെയ്യാൻ സാധിച്ചില്ല: {e}")


# 3. Kick (ഗ്രൂപ്പിൽ നിന്നും പുറത്താക്കാൻ - റിപ്ലൈ ആയി /kick)
async def kick_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text("❌ ഈ കമാൻഡ് ഉപയോഗിക്കാൻ നിങ്ങൾക്ക് അഡ്മിൻ അനുമതിയില്ല.")
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ പുറത്താക്കേണ്ട വ്യക്തിയുടെ മെസ്സേജിന് റിപ്ലൈ ആയി ഈ കമാൻഡ് അടിക്കുക.")
        return

    target_user = update.message.reply_to_message.from_user
    try:
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
        await update.message.reply_text("❌ ഈ കമാൻഡ് ഉപയോഗിക്കാൻ നിങ്ങൾക്ക് അഡ്മിൻ അനുമതിയില്ല.")
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ മ്യൂട്ട് ചെയ്യേണ്ട വ്യക്തിയുടെ മെസ്സേജിന് റിപ്ലൈ ആയി ഈ കമാൻഡ് അടിക്കുക.")
        return

    target_user = update.message.reply_to_message.from_user
    try:
        mute_permissions = ChatPermissions(can_send_messages=False)
        await update.effective_chat.restrict_member(user_id=target_user.id, permissions=mute_permissions)
        await update.message.reply_text(
            f"🔇 {target_user.mention_html()} എന്ന യൂസറെ മ്യൂട്ട് ചെയ്തിരിക്കുന്നു (മെസ്സേജ് അയക്കാൻ സാധിക്കില്ല).",
            parse_mode="HTML",
        )
    except Exception as e:
        await update.message.reply_text(f"❌ മ്യൂട്ട് ചെയ്യാൻ സാധിച്ചില്ല: {e}")


# 5. Unmute (അൺമ്യൂട്ട് ചെയ്യാൻ - റിപ്ലൈ ആയി /unmute)
async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text("❌ ഈ കമാൻഡ് ഉപയോഗിക്കാൻ നിങ്ങൾക്ക് അഡ്മിൻ അനുമതിയില്ല.")
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ അൺമ്യൂട്ട് ചെയ്യേണ്ട വ്യക്തിയുടെ മെസ്സേജിന് റിപ്ലൈ ആയി ഈ കമാൻഡ് അടിക്കുക.")
        return

    target_user = update.message.reply_to_message.from_user
    try:
        unmute_permissions = ChatPermissions(
            can_send_messages=True, can_send_audios=True, can_send_documents=True,
            can_send_photos=True, can_send_videos=True, can_send_video_notes=True,
            can_send_voice_notes=True, can_send_polls=True, can_send_other_messages=True,
            can_add_web_page_previews=True
        )
        await update.effective_chat.restrict_member(user_id=target_user.id, permissions=unmute_permissions)
        await update.message.reply_text(
            f"🔊 {target_user.mention_html()} എന്ന യൂസറെ അൺമ്യൂട്ട് ചെയ്തിരിക്കുന്നു.",
            parse_mode="HTML",
        )
    except Exception as e:
        await update.message.reply_text(f"❌ അൺമ്യൂട്ട് ചെയ്യാൻ സാധിച്ചില്ല: {e}")


# 💬 മെസ്സേജുകൾ പരിശോധിക്കുന്ന പ്രധാന ഫങ്ക്ഷൻ
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    if await is_admin(update, context):
        return

    message_text = update.message.text
    
    # 🌟 മെസ്സേജിൽ ലിങ്ക് ഉണ്ടെങ്കിൽ അതിന് റാൻഡം റിയാക്ഷൻ നൽകും
    if re.search(LINK_REGEX, message_text, re.IGNORECASE):
        try:
            random_emoji = random.choice(REACTIONS)
            await update.message.set_reaction(reaction=ReactionTypeEmoji(emoji=random_emoji))
        except Exception as e:
            print(f"റിയാക്ഷൻ നൽകാൻ സാധിച്ചില്ല: {e}")
        return

    # ⚠️ ലിങ്ക് ഇല്ലാത്ത വെറും ടെക്സ്റ്റ് മെസ്സേജുകൾ ഉടൻ ഡിലീറ്റ് ചെയ്യും
    target_user = update.message.from_user
    user_id = target_user.id
    try:
        await update.message.delete()
    except Exception as e:
        print(f"ഡിലീറ്റ് ചെയ്യാൻ സാധിച്ചില്ല: {e}")
        return

    # വാണിംഗ് കൗണ്ട് സെറ്റ് ചെയ്യുന്നു
    if 'text_warnings' not in context.user_data:
        context.user_data['text_warnings'] = {}
        
    current_warnings = context.user_data['text_warnings'].get(user_id, 0) + 1
    context.user_data['text_warnings'][user_id] = current_warnings

    # 3 വാണിംഗ് ആയാൽ മ്യൂട്ട് ചെയ്യും
    if current_warnings >= 3:
        try:
            mute_permissions = ChatPermissions(can_send_messages=False)
            await update.effective_chat.restrict_member(user_id=user_id, permissions=mute_permissions)
            await update.effective_chat.send_message(
                f"🔇 {target_user.mention_html()} താങ്കൾ ലിങ്ക് ഇല്ലാതെ 3 തവണ മെസ്സേജ് അയച്ചതിനാൽ ഗ്രൂപ്പിൽ നിന്നും മ്യൂട്ട് ചെയ്തിരിക്കുന്നു. ഇനി ലിങ്കുകൾ മാത്രമേ ഷെയർ ചെയ്യാൻ സാധിക്കൂ.",
                parse_mode="HTML"
            )
            context.user_data['text_warnings'][user_id] = 0
        except Exception as e:
            await update.effective_chat.send_message(f"❌ മ്യൂട്ട് ചെയ്യാൻ സാധിച്ചില്ല: {e}")
    else:
        # വാണിംഗ് മെസ്സേജ് അയക്കുന്നു
        warn_msg = await update.effective_chat.send_message(
            f"⚠️ {target_user.mention_html()}, ഈ ഗ്രൂപ്പിൽ ലിങ്കുകൾ മാത്രമേ അനുവദിക്കൂ. വെറും ടെക്സ്റ്റ് മെസ്സേജുകൾ അയക്കാൻ പാടുള്ളതല്ല. താങ്കളുടെ മെസ്സേജ് ഡിലീറ്റ് ചെയ്തിട്ടുണ്ട്.\n\n"
            f"Status: <b>{current_warnings}/3 Warnings</b>",
            parse_mode="HTML"
        )
        
        # 🕒 5 സെക്കൻഡിന് ശേഷം ബോട്ട് അയച്ച വാണിംഗ് മെസ്സേജ് തനിയെ ഡിലീറ്റ് ചെയ്യും
        await asyncio.sleep(5)
        try:
            await warn_msg.delete()
        except Exception as e:
            print(f"വാണിംഗ് മെസ്സേജ് ഡിലീറ്റ് ചെയ്യാൻ കഴിഞ്ഞില്ല: {e}")


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # അഡ്മിൻ കമാൻഡുകൾ
    app.add_handler(CommandHandler("ban", ban_user))
    app.add_handler(CommandHandler("unban", unban_user))
    app.add_handler(CommandHandler("kick", kick_user))
    app.add_handler(CommandHandler("mute", mute_user))
    app.add_handler(CommandHandler("unmute", unmute_user))

    # ഗ്രൂപ്പിലെ മെസ്സേജുകൾ ഫിൽട്ടർ ചെയ്യാൻ
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))

    print("🤖 ബോട്ട് വിജയകരമായി റൺ ആയിക്കൊണ്ടിരിക്കുന്നു...")
    app.run_polling()

if __name__ == "__main__":
    main()