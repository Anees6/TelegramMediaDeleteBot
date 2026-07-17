import asyncio
import re
import os
from threading import Thread
from flask import Flask
from telegram import Update, ChatPermissions
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Flask വെബ് സെർവർ സെറ്റപ്പ് (Render-ൽ ലിങ്ക് കിട്ടാൻ വേണ്ടി)
app = Flask(__name__)

@app.route('/')
def home():
    return "Rose Bot is alive!"

def run_flask():
    # Render-ൽ പോർട്ട് പ്രശ്നം വരാതിരിക്കാൻ os.environ ഉപയോഗിക്കുന്നു
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# നിങ്ങളുടെ ബോട്ട് ടോക്കൺ ഇവിടെ കൃത്യമായി ചേർത്തിട്ടുണ്ട്
BOT_TOKEN = "8673412670:AAFW2QTdkHH_LxecEzJNE-SkflJZe1X8Y0g"
LINK_REGEX = re.compile(r'https?://\S+|www\.\S+')

# വാണിംഗുകൾ താൽക്കാലികമായി സൂക്ഷിക്കാൻ
user_warnings = {}

# അഡ്മിൻ ആണോ എന്ന് പരിശോധിക്കാനുള്ള ഫങ്ഷൻ
async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    chat = update.effective_chat
    user = update.effective_user
    if chat.type not in ["group", "supergroup"]:
        return False
    member = await chat.get_member(user.id)
    return member.status in ['administrator', 'creator']

# 1. START COMMAND & HELP MENU (ഇമോജികളോടെ ഒതുക്കമുള്ള സ്റ്റൈലിൽ)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🌹 *Rose Management Bot* 🌹\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "ഗ്രൂപ്പുകൾ എളുപ്പത്തിൽ നിയന്ത്രിക്കാൻ സഹായിക്കുന്ന അഡ്മിൻ ബോട്ട്! 🛡️\n\n"
        
        "🛠️ *അഡ്മിൻ കമാൻഡുകൾ (ഗ്രൂപ്പിൽ ഉപയോഗിക്കാൻ):*\n"
        "_(ഏതെങ്കിലും മെസ്സേജിന് *Reply* ആയി താഴെയുള്ളവ ടൈപ്പ് ചെയ്യുക)_\n"
        "🛑 `/ban` ➔ യൂസറെ എന്നെന്നേക്കുമായി പുറത്താക്കാൻ\n"
        "✅ `/unban` ➔ ബാൻ ചെയ്ത യൂസറെ തിരികെ കയറ്റാൻ\n"
        "🔇 `/mute` ➔ ഗ്രൂപ്പിൽ സംസാരിക്കുന്നത് തടയാൻ\n"
        "🔊 `/unmute` ➔ മ്യൂട്ട് പെർമിഷൻ മാറ്റാൻ\n"
        "⚠️ `/warn` ➔ വാണിംഗ് നൽകാൻ (3 വാണിംഗ് ആയാൽ ഓട്ടോ ബാൻ)\n"
        "🔄 `/resetwarns` ➔ യൂസറുടെ വാണിംഗുകൾ പൂജ്യമാക്കാൻ\n"
        "🗑️ `/del` ➔ റിപ്ലൈ ചെയ്ത മെസ്സേജ് മാത്രം ഡിലീറ്റ് ചെയ്യാൻ\n"
        "🧹 `/purge` ➔ ഇതിനു ശേഷമുള്ള മെസ്സേജുകൾ കൂട്ടത്തോടെ കളയാൻ\n"
        "📌 `/pin` ➔ പ്രധാന സന്ദേശങ്ങൾ ഗ്രൂപ്പിൽ പിൻ ചെയ്യാൻ\n"
        "📝 `/setrules [നിയമങ്ങൾ]` ➔ ഗ്രൂപ്പ് റൂൾസ് സെറ്റ് ചെയ്യാൻ\n\n"
        
        "👥 *പൊതുവായ കമാൻഡുകൾ:*\n"
        "📜 `/rules` ➔ ഗ്രൂപ്പിലെ നിയമങ്ങൾ കാണാൻ\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "💡 _ശ്രദ്ധിക്കുക: ലിങ്ക് അല്ലാത്ത സന്ദേശങ്ങൾ സാധാരണ യൂസർമാർ അയച്ചാൽ ബോട്ട് അവരെ ഓട്ടോമാറ്റിക് ആയി മ്യൂട്ട് ചെയ്യുന്നതാണ്!_"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

# 2. BAN USER
async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    chat_id = update.effective_chat.id
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        await context.bot.ban_chat_member(chat_id, target_user.id)
        await update.message.reply_text(f"🛑 {target_user.mention_html()} ഗ്രൂപ്പിൽ നിന്നും ബാൻ ചെയ്യപ്പെട്ടു.", parse_mode="HTML")

# 3. UNBAN USER
async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    chat_id = update.effective_chat.id
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        await context.bot.unban_chat_member(chat_id, target_user.id)
        await update.message.reply_text(f"✅ {target_user.mention_html()} അൺബാൻ ചെയ്യപ്പെട്ടു.", parse_mode="HTML")

# 4. MUTE USER
async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    chat_id = update.effective_chat.id
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        await chat.restrict_member(user_id=target_user.id, permissions=ChatPermissions(can_send_messages=False))
        await update.message.reply_text(f"🔇 {target_user.mention_html()} മ്യൂട്ട് ചെയ്യപ്പെട്ടു.", parse_mode="HTML")

# 5. UNMUTE USER
async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    chat_id = update.effective_chat.id
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        full_permissions = ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True, can_add_web_page_previews=True)
        await chat.restrict_member(user_id=target_user.id, permissions=full_permissions)
        await update.message.reply_text(f"🔊 {target_user.mention_html()} അൺമ്യൂട്ട് ചെയ്യപ്പെട്ടു.", parse_mode="HTML")

# 6. WARN USER (3 വാണിംഗ് ആയാൽ ഓട്ടോ ബാൻ)
async def warn_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    chat_id = update.effective_chat.id
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        user_id = target_user.id
        
        user_warnings[user_id] = user_warnings.get(user_id, 0) + 1
        count = user_warnings[user_id]
        
        if count >= 3:
            await context.bot.ban_chat_member(chat_id, user_id)
            await update.message.reply_text(f"🛑 {target_user.mention_html()} 3 വാണിംഗുകൾ ലഭിച്ചതിനാൽ ബാൻ ചെയ്യപ്പെട്ടു.", parse_mode="HTML")
            user_warnings[user_id] = 0
        else:
            await update.message.reply_text(f"⚠️ {target_user.mention_html()}, നിങ്ങൾക്ക് ഒരു വാണിംഗ് നൽകിയിരിക്കുന്നു! ({count}/3)", parse_mode="HTML")

# 7. RESET WARNS
async def reset_warns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        user_warnings[target_user.id] = 0
        await update.message.reply_text(f"✅ {target_user.mention_html()}-ന്റെ വാണിംഗുകൾ റീസെറ്റ് ചെയ്തു.", parse_mode="HTML")

# 8. DEL SINGLE MESSAGE
async def delete_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    if update.message.reply_to_message:
        await context.bot.delete_message(update.effective_chat.id, update.message.reply_to_message.message_id)
        await update.message.delete()

# 9. PURGE MESSAGES
async def purge_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    chat_id = update.effective_chat.id
    if update.message.reply_to_message:
        start_id = update.message.reply_to_message.message_id
        end_id = update.message.message_id
        
        for msg_id in range(start_id, end_id + 1):
            try:
                await context.bot.delete_message(chat_id, msg_id)
            except Exception:
                continue
        del_note = await context.bot.send_message(chat_id, "🧹 ഗ്രൂപ്പ് വൃത്തിയാക്കി (Purge പൂർത്തിയായി)!")
        await asyncio.sleep(4)
        await del_note.delete()

# 10. PIN MESSAGE
async def pin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    if update.message.reply_to_message:
        await context.bot.pin_chat_message(update.effective_chat.id, update.message.reply_to_message.message_id)
        await update.message.reply_text("📌 മെസ്സേജ് പിൻ ചെയ്തു!")

# 11. SET & GET RULES
async def set_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    rules_text = " ".join(context.args)
    if not rules_text:
        await update.message.reply_text("ഉപയോഗിക്കേണ്ട രീതി: `/setrules ഇവിടെ നിയമങ്ങൾ എഴുതുക`")
        return
    context.chat_data['rules'] = rules_text
    await update.message.reply_text("✅ ഗ്രൂപ്പ് നിയമങ്ങൾ വിജയകരമായി സെറ്റ് ചെയ്തു.")

async def get_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rules = context.chat_data.get('rules', "ഈ ഗ്രൂപ്പിൽ നിയമങ്ങൾ ഒന്നും സെറ്റ് ചെയ്തിട്ടില്ല.")
    await update.message.reply_text(f"📜 *ഗ്രൂപ്പ് നിയമങ്ങൾ:*\n\n{rules}", parse_mode="Markdown")

# 12. AUTOMATIC LINK FILTER & AUTO MUTE
async def delete_warning(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    try:
        await context.bot.delete_message(chat_id=job.chat_id, message_id=job.data)
    except Exception as e:
        print(f"Error deleting message: {e}")

async def filter_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    chat = update.effective_chat
    user = update.effective_user

    if not message or chat.type not in ["group", "supergroup"]:
        return
        
    # അഡ്മിൻമാരെയും ബോട്ടുകളെയും ഒഴിവാക്കുന്നു
    member = await chat.get_member(user.id)
    if member.status in ['administrator', 'creator'] or user.is_bot:
        return

    # മെസ്സേജിൽ ലിങ്ക് ഉണ്ടെങ്കിൽ ബോട്ട് ഒന്നും ചെയ്യില്ല
    if message.text and LINK_REGEX.search(message.text):
        return

    try:
        # 1. ലിങ്ക് അല്ലാത്ത മെസ്സേജ് ഡിലീറ്റ് ചെയ്യുന്നു
        await message.delete()

        # 2. യൂസറെ മ്യൂട്ട് ചെയ്യുന്നു
        mute_permissions = ChatPermissions(can_send_messages=False)
        await chat.restrict_member(user_id=user.id, permissions=mute_permissions)

        # 3. വാണിംഗ് മെസ്സേജ് അയക്കുന്നു
        warning_msg = await context.bot.send_message(
            chat_id=chat.id,
            text=f"⚠️ {user.mention_html()}, ഈ ഗ്രൂപ്പിൽ ലിങ്കുകൾ മാത്രമേ അനുവദിക്കൂ! നിങ്ങളുടെ മെസ്സേജ് ഡിലീറ്റ് ചെയ്ത് നിങ്ങളെ മ്യൂട്ട് ചെയ്തിരിക്കുന്നു.",
            parse_mode="HTML"
        )

        # 4. 1 മിനിറ്റിന് (60 സെക്കൻഡ്) ശേഷം വാണിംഗ് മെസ്സേജ് ഡിലീറ്റ് ചെയ്യുന്നു
        context.job_queue.run_once(
            delete_warning, 
            when=60, 
            chat_id=chat.id, 
            data=warning_msg.message_id
        )
    except Exception as e:
        print(f"Error: {e}")

def main():
    # വെബ് സെർവർ സ്റ്റാർട്ട് ചെയ്യുന്നു
    Thread(target=run_flask, daemon=True).start()

    # ബോട്ട് സ്റ്റാർട്ട് ചെയ്യുന്നു (Job Queue സഹിതം)
    application = Application.builder().token(BOT_TOKEN).build()
    
    # കമാൻഡുകൾ രജിസ്റ്റർ ചെയ്യുന്നു
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ban", ban_user))
    application.add_handler(CommandHandler("unban", unban_user))
    application.add_handler(CommandHandler("mute", mute_user))
    application.add_handler(CommandHandler("unmute", unmute_user))
    application.add_handler(CommandHandler("warn", warn_user))
    application.add_handler(CommandHandler("resetwarns", reset_warns))
    application.add_handler(CommandHandler("del", delete_msg))
    application.add_handler(CommandHandler("purge", purge_messages))
    application.add_handler(CommandHandler("pin", pin_message))
    application.add_handler(CommandHandler("setrules", set_rules))
    application.add_handler(CommandHandler("rules", get_rules))
    
    # ഗ്രൂപ്പിലെ മെസ്സേജുകൾ ഫിൽട്ടർ ചെയ്യാൻ
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, filter_messages))

    print("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()