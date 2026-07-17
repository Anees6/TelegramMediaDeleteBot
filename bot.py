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


# ⏱️ 15 മിനിറ്റിന് ശേഷം മെസ്സേജ് ഡിലീറ്റ് ചെയ്യാനുള്ള ഫങ്ക്ഷൻ
async def delete_scheduled_message(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.chat_id
    message_id = job.data # ടാസ്കിൽ സേവ് ചെയ്തു വെച്ച മെസ്സേജ് ID
    
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        # മെസ്സേജ് നേരത്തെ ഡിലീറ്റ് ചെയ്യപ്പെട്ടിട്ടുണ്ടെങ്കിലോ പെർമിഷൻ ഇല്ലെങ്കിലോ എറർ വരാം
        print(f"മെസ്സേജ് ഡിലീറ്റ് ചെയ്യാൻ സാധിച്ചില്ല (ID: {message_id}): {e}")


# 💬 ഗ്രൂപ്പിൽ വരുന്ന എല്ലാ മെസ്സേജുകളും കൈകാര്യം ചെയ്യുന്ന ഫങ്ക്ഷൻ
async def handle_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
        
    chat_id = update.effective_chat.id
    message_id = update.message.message_id
    
    # 🕒 എല്ലാ മെസ്സേജുകളും 15 മിനിറ്റിന് (15 * 60 = 900 സെക്കൻഡ്) ശേഷം ഡിലീറ്റ് ചെയ്യാൻ ഷെഡ്യൂൾ ചെയ്യുന്നു
    # ശ്രദ്ധിക്കുക: അഡ്മിൻമാരുടെ മെസ്സേജും ഡിലീറ്റ് ചെയ്യണമെങ്കിൽ താഴെയുള്ള ഫിൽട്ടർ മാറ്റാം. നിലവിൽ എല്ലാവരുടെയും ഡിലീറ്റ് ചെയ്യും.
    context.job_queue.run_once(
        delete_scheduled_message, 
        when=900,  # 900 സെക്കൻഡ് = 15 മിനിറ്റ്
        chat_id=chat_id, 
        data=message_id
    )

    # അഡ്മിൻ ആണെങ്കിൽ ബാക്കി റൂളുകൾ (ലിങ്ക് ചെക്കിങ്, വാണിംഗ്) ബാധകമല്ല
    if await is_admin(update, context):
        return

    # മെസ്സേജിൽ ടെക്സ്റ്റ് ഉണ്ടെങ്കിൽ മാത്രം ലിങ്ക് പരിശോധിച്ചാൽ മതി
    if update.message.text:
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
            print(f"ഉടൻ ഡിലീറ്റ് ചെയ്യാൻ സാധിച്ചില്ല: {e}")
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


# --- ബാക്കി അഡ്മിൻ കമാൻഡുകൾ താഴെ (മാറ്റമില്ല) ---

async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    if not update.message.reply_to_message: return
    try:
        await update.effective_chat.ban_member(user_id=update.message.reply_to_message.from_user.id)
        await update.message.reply_text("🚫 ബാൻ ചെയ്തിരിക്കുന്നു.")
    except: pass

async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    if not context.args: return
    try:
        await update.effective_chat.unban_member(user_id=int(context.args[0]))
        await update.message.reply_text("✅ അൺബാൻ ചെയ്തിരിക്കുന്നു.")
    except: pass

async def kick_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    if not update.message.reply_to_message: return
    try:
        u_id = update.message.reply_to_message.from_user.id
        await update.effective_chat.ban_member(user_id=u_id)
        await update.effective_chat.unban_member(user_id=u_id)
        await update.message.reply_text("👞 കിക്ക് ചെയ്തിരിക്കുന്നു.")
    except: pass

async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    if not update.message.reply_to_message: return
    try:
        await update.effective_chat.restrict_member(user_id=update.message.reply_to_message.from_user.id, permissions=ChatPermissions(can_send_messages=False))
        await update.message.reply_text("🔇 മ്യൂട്ട് ചെയ്തിരിക്കുന്നു.")
    except: pass

async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    if not update.message.reply_to_message: return
    try:
        unmute_permissions = ChatPermissions(
            can_send_messages=True, can_send_audios=True, can_send_documents=True,
            can_send_photos=True, can_send_videos=True, can_send_video_notes=True,
            can_send_voice_notes=True, can_send_polls=True, can_send_other_messages=True,
            can_add_web_page_previews=True
        )
        await update.effective_chat.restrict_member(user_id=update.message.reply_to_message.from_user.id, permissions=unmute_permissions)
        await update.message.reply_text("🔊 അൺമ്യൂട്ട് ചെയ്തിരിക്കുന്നു.")
    except: pass


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # അഡ്മിൻ കമാൻഡുകൾ
    app.add_handler(CommandHandler("ban", ban_user))
    app.add_handler(CommandHandler("unban", unban_user))
    app.add_handler(CommandHandler("kick", kick_user))
    app.add_handler(CommandHandler("mute", mute_user))
    app.add_handler(CommandHandler("unmute", unmute_user))

    # 🌟 ടെക്സ്റ്റ്, ഫോട്ടോ, വീഡിയോ, ലിങ്ക് അടക്കം എല്ലാ മീഡിയകളും ട്രാക്ക് ചെയ്യാൻ ALL ഫിൽട്ടർ ഉപയോഗിക്കുന്നു
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_all_messages))

    print("🤖 ബോട്ട് 15 മിനിറ്റ് ഡിലീഷൻ ഫീച്ചറോടെ റൺ ആകുന്നു...")
    app.run_polling()

if __name__ == "__main__":
    main()