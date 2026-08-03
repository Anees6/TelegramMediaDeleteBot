import logging
import os
import asyncio
from datetime import datetime, timedelta, timezone
from threading import Thread
from flask import Flask
from telegram import Update, ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# --- FLASK WEB SERVER SETUP ---
flask_app = Flask('')

@flask_app.route('/')
def home():
    return "ബോട്ട് വിജയകരമായി പ്രവർത്തിക്കുന്നു!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()


# --- TELEGRAM BOT SETUP ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

TOKEN = "8673412670:AAGCYcqdMWXXnR73MmtEMGIaPR06d2aDZNw"

# പഴയ മെസ്സേജുകളുടെ ഐഡി സൂക്ഷിക്കാനുള്ള വേരിയബിളുകൾ
last_warning_message_id = {} # {chat_id: message_id}
last_welcome_message_id = {} # {chat_id: message_id}

# --- ഓരോ ഗ്രൂപ്പിനും വെവ്വേറെ ഡാറ്റ സൂക്ഷിക്കാൻ ഡാറ്റാ സ്ട്രക്ചർ ---
antilink_status = {}  # {chat_id: True/False}
user_photo_count = {} # {chat_id: {user_id: {"name": str, "count": int}}}
user_link_count = {}  # {chat_id: {user_id: {"name": str, "count": int}}}

# കമാൻഡ് അടിക്കുന്ന ആൾ ഗ്രൂപ്പിലെ അഡ്മിൻ ആണോ എന്ന് പരിശോധിക്കാനുള്ള ഫങ്ഷൻ
async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ['creator', 'administrator']
    except Exception:
        return False

# /start കമാൻഡ് വരുമ്പോൾ കാണിക്കേണ്ട മെസ്സേജ്
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_name = user.first_name

    start_text = (
        f"✨ **ഹലോ {user_name}!** ✨\n\n"
        "ഞാൻ നിങ്ങളുടെ ഗ്രൂപ്പ് മാനേജ്‌മെന്റ് ബോട്ട് ആണ്. എന്നെ നിർമ്മിച്ചത് @faseena ആണ്.\n\n"
        "താഴെ കാണുന്ന ബട്ടണുകളിൽ അമർത്തി അഡ്മിൻ കമാൻഡുകൾ മനസ്സിലാക്കാം 👇"
    )

    keyboard = [
        [
            InlineKeyboardButton("🔨 /ban", callback_data="none"),
            InlineKeyboardButton("👞 /kick", callback_data="none")
        ],
        [
            InlineKeyboardButton("🔇 /mute", callback_data="none"),
            InlineKeyboardButton("⏳ /tmute", callback_data="none")
        ],
        [
            InlineKeyboardButton("🔊 /unmute", callback_data="none"),
            InlineKeyboardButton("🔓 /unban", callback_data="none")
        ],
        [
            InlineKeyboardButton("⚙️ /antilink on", callback_data="none"),
            InlineKeyboardButton("🛑 /antilink off", callback_data="none")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        start_text,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

# --- ഓൺ / ഓഫ് ചെയ്യാനുള്ള കമാൻഡ് ഫങ്ഷൻ ---
async def toggle_antilink(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    if not await is_admin(update, context):
        await update.message.reply_text("❌ നിങ്ങൾക്ക് ഈ കമാൻഡ് ഉപയോഗിക്കാൻ അധികാരമില്ല!")
        return

    if not context.args:
        await update.message.reply_text("⚠️ ഉപയോഗിക്കേണ്ട രീതി: `/antilink on` അല്ലെങ്കിൽ `/antilink off`", parse_mode="Markdown")
        return

    command = context.args[0].lower()
    if command == "on":
        antilink_status[chat_id] = True
        await update.message.reply_text("✅ ഈ ഗ്രൂപ്പിൽ ലിങ്ക് ഒഴികെയുള്ള മറ്റ് മെസ്സേജുകൾ ഡിലീറ്റ് ചെയ്യുന്ന സിസ്റ്റം ഓൺ ആക്കി!")
    elif command == "off":
        antilink_status[chat_id] = False
        await update.message.reply_text("🛑 ഈ ഗ്രൂപ്പിൽ ലിങ്ക് ഒഴികെയുള്ള മറ്റ് മെസ്സേജുകൾ ഡിലീറ്റ് ചെയ്യുന്ന സിസ്റ്റം ഓഫ് ആക്കി!")
    else:
        await update.message.reply_text("⚠️ ദയവായി `on` അല്ലെങ്കിൽ `off` എന്ന് മാത്രം ചേർക്കുക.", parse_mode="Markdown")

# /ban കമാൻഡ്
async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text("❌ നിങ്ങൾക്ക് ഈ കമാൻഡ് ഉപയോഗിക്കാൻ അധികാരമില്ല!")
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ ഏത് യൂസറെയാണ് ബാൻ ചെയ്യേണ്ടത് അവരുടെ മെസ്സേജിന് റിപ്ലൈ ആയി ഈ കമാൻഡ് അടിക്കുക.")
        return
    user_to_ban = update.message.reply_to_message.from_user
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, user_to_ban.id)
        await update.message.reply_text(f"❌ {user_to_ban.first_name} എന്ന യൂസറെ ബാൻ ചെയ്തു.")
    except Exception as e:
        await update.message.reply_text(f"ബാൻ ചെയ്യാൻ പറ്റിയില്ല: {e}")

# /unban കമാൻഡ്
async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not context.args:
        await update.message.reply_text("⚠️ ഉപയോഗിക്കേണ്ട രീതി: `/unban [user_id]`", parse_mode="Markdown")
        return
    try:
        user_id = int(context.args[0])
        await context.bot.unban_chat_member(update.effective_chat.id, user_id)
        await update.message.reply_text(f"✓ യൂസർ (ID: {user_id}) അൺബാൻ ചെയ്യപ്പെട്ടു.")
    except Exception as e:
        await update.message.reply_text(f"അൺബാൻ ചെയ്യാൻ പറ്റിയില്ല: {e}")

# /kick കമാൻഡ്
async def kick_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ ആരെയാണ് കിക്ക് ചെയ്യേണ്ടത് അവരുടെ മെസ്സേജിന് റിപ്ലൈ ആയി ചെയ്യുക.")
        return
    user_to_kick = update.message.reply_to_message.from_user
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, user_to_kick.id)
        await context.bot.unban_chat_member(update.effective_chat.id, user_to_kick.id)
        await update.message.reply_text(f"🏃 {user_to_kick.first_name} ഗ്രൂപ്പിൽ നിന്നും പുറത്താക്കപ്പെട്ടു.")
    except Exception as e:
        await update.message.reply_text(f"കിക്ക് ചെയ്യാൻ പറ്റിയില്ല: {e}")

# /mute കമാൻഡ്
async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ ആരെയാണ് മ്യൂട്ട് ചെയ്യേണ്ടത് അവരുടെ മെസ്സേജിന് റിപ്ലൈ ആയി ചെയ്യുക.")
        return
    user_to_mute = update.message.reply_to_message.from_user
    no_send_permissions = ChatPermissions(can_send_messages=False)
    try:
        await context.bot.restrict_chat_member(update.effective_chat.id, user_to_mute.id, permissions=no_send_permissions)
        await update.message.reply_text(f"🔇 {user_to_mute.first_name} മ്യൂട്ട് ചെയ്യപ്പെട്ടു.")
    except Exception as e:
        await update.message.reply_text(f"മ്യൂട്ട് ചെയ്യാൻ പറ്റിയില്ല: {e}")

# /tmute കമാൻഡ്
async def timed_mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ ആരെയാണ് മ്യൂട്ട് ചെയ്യേണ്ടത് അവരുടെ മെസ്സേജിന് റിപ്ലൈ ആയി ചെയ്യുക.")
        return
    if not context.args:
        await update.message.reply_text("⚠️ എത്ര മിനിറ്റാണ് മ്യൂട്ട് ചെയ്യേണ്ടത് എന്ന് കൂടി പറയുക. ഉദാഹരണത്തിന്: `/tmute 10`", parse_mode="Markdown")
        return

    try:
        minutes = int(context.args[0])
        user_to_mute = update.message.reply_to_message.from_user
        until_time = datetime.now(timezone.utc) + timedelta(minutes=minutes)
        no_send_permissions = ChatPermissions(can_send_messages=False)
        
        await context.bot.restrict_chat_member(
            update.effective_chat.id, 
            user_to_mute.id, 
            permissions=no_send_permissions, 
            until_date=until_time
        )
        await update.message.reply_text(f"⏳ {user_to_mute.first_name} {minutes} മിനിറ്റത്തേക്ക് മ്യൂട്ട് ചെയ്യപ്പെട്ടു.")
    except ValueError:
        await update.message.reply_text("⚠️ സമയം നമ്പറായി തന്നെ നൽകുക (ഉദാഹരണത്തിന്: 10).")
    except Exception as e:
        await update.message.reply_text(f"മ്യൂട്ട് ചെയ്യാൻ പറ്റിയില്ല: {e}")

# /unmute കമാൻഡ്
async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ ആരുടെ മ്യൂട്ടാണ് മാറ്റേണ്ടത് അവരുടെ മെസ്സേജിന് റിപ്ലൈ ആയി ചെയ്യുക.")
        return
    user_to_unmute = update.message.reply_to_message.from_user
    full_permissions = ChatPermissions(
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
    try:
        await context.bot.restrict_chat_member(update.effective_chat.id, user_to_unmute.id, permissions=full_permissions)
        await update.message.reply_text(f"🔊 {user_to_unmute.first_name} അൺമ്യൂട്ട് ചെയ്യപ്പെട്ടു. ഇനി മെസ്സേജ് അയക്കാം.")
    except Exception as e:
        await update.message.reply_text(f"അൺമ്യൂട്ട് ചെയ്യാൻ പറ്റിയില്ല: {e}")

# --- ഡിലീറ്റ് ചെയ്യാനും വാണിംഗ് നൽകാനുമുള്ള ഫങ്ഷൻ ---
async def handle_normal_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user

    is_on = antilink_status.get(chat_id, True)
    if not is_on:
        return

    if await is_admin(update, context):
        return

    if update.message.entities and any(entity.type in ["url", "text_link"] for entity in update.message.entities):
        return

    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=update.message.message_id)

        until_time = datetime.now(timezone.utc) + timedelta(minutes=1)
        no_send_permissions = ChatPermissions(can_send_messages=False)
        try:
            await context.bot.restrict_chat_member(
                chat_id,
                user.id,
                permissions=no_send_permissions,
                until_date=until_time
            )
        except Exception as e:
            print(f"യൂസറെ മ്യൂട്ട് ചെയ്യുന്നതിൽ എറർ: {e}")

        if chat_id in last_warning_message_id:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=last_warning_message_id[chat_id])
            except Exception:
                pass

        warning_text = f"⚠️ {user.mention_html()} ഗ്രൂപ്പിൽ ലിങ്ക് മാത്രം ഇടുക! നിങ്ങൾക്ക് 1 മിനിറ്റ് മ്യൂട്ട് നൽകിയിട്ടുണ്ട്."
        sent_message = await context.bot.send_message(chat_id=chat_id, text=warning_text, parse_mode="HTML")
        
        last_warning_message_id[chat_id] = sent_message.message_id

        await asyncio.sleep(5)
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=sent_message.message_id)
        except Exception:
            pass

    except Exception as e:
        print(f"മെസ്സേജ് കൈകാര്യം ചെയ്യുന്നതിൽ എറർ: {e}")

# --- വെൽക്കം മെസ്സേജ് ---
async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    for new_member in update.message.new_chat_members:
        if new_member.id == context.bot.id:
            continue
            
        try:
            if chat_id in last_welcome_message_id:
                try:
                    await context.bot.delete_message(chat_id=chat_id, message_id=last_welcome_message_id[chat_id])
                except Exception:
                    pass

            welcome_text = f"👋 ഹലോ {new_member.mention_html()}, നമ്മുടെ ഗ്രൂപ്പിലേക്ക് സ്വാഗതം!"
            sent_message = await context.bot.send_message(chat_id=chat_id, text=welcome_text, parse_mode="HTML")
            last_welcome_message_id[chat_id] = sent_message.message_id
            
        except Exception as e:
            print(f"വെൽക്കം പറയുന്നതിൽ എറർ: {e}")

# --- ട്രാക്കിംഗ് ഫങ്ഷൻ ---
async def track_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or update.effective_user.is_bot:
        return

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    msg = update.message

    if not msg:
        return

    if msg.photo:
        if chat_id not in user_photo_count:
            user_photo_count[chat_id] = {}
        if user_id not in user_photo_count[chat_id]:
            user_photo_count[chat_id][user_id] = {"name": user_name, "count": 0}
        user_photo_count[chat_id][user_id]["count"] += 1
        user_photo_count[chat_id][user_id]["name"] = user_name

    has_link = False
    if msg.entities and any(e.type in ["url", "text_link"] for e in msg.entities):
        has_link = True
    elif msg.caption_entities and any(e.type in ["url", "text_link"] for e in msg.caption_entities):
        has_link = True

    if has_link:
        if chat_id not in user_link_count:
            user_link_count[chat_id] = {}
        if user_id not in user_link_count[chat_id]:
            user_link_count[chat_id][user_id] = {"name": user_name, "count": 0}
        user_link_count[chat_id][user_id]["count"] += 1
        user_link_count[chat_id][user_id]["name"] = user_name

# --- 1. Photos Leaderboard കമാൻഡ് ---
async def photo_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    if chat_id not in user_photo_count or not user_photo_count[chat_id]:
        await update.message.reply_text("🖼️ നിലവിൽ ഈ ഗ്രൂപ്പിൽ ഫോട്ടോകൾ അയച്ചവരുടെ ഡാറ്റ ലഭ്യമല്ല.")
        return

    sorted_users = sorted(user_photo_count[chat_id].values(), key=lambda x: x["count"], reverse=True)[:5]
    
    text = "🖼️ **TOP 5 PHOTO LEADERBOARD** 🖼️\n\n"
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    
    for idx, user_info in enumerate(sorted_users):
        text += f"{medals[idx]} **{user_info['name']}** - {user_info['count']} ഫോട്ടോകൾ\n"
        
    await update.message.reply_text(text, parse_mode="Markdown")

# --- 2. Links Leaderboard കമാൻഡ് ---
async def link_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if chat_id not in user_link_count or not user_link_count[chat_id]:
        await update.message.reply_text("🔗 നിലവിൽ ഈ ഗ്രൂപ്പിൽ ലിങ്കുകൾ അയച്ചവരുടെ ഡാറ്റ ലഭ്യമല്ല.")
        return

    sorted_users = sorted(user_link_count[chat_id].values(), key=lambda x: x["count"], reverse=True)[:5]
    
    text = "🔗 **TOP 5 LINK LEADERBOARD** 🔗\n\n"
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    
    for idx, user_info in enumerate(sorted_users):
        text += f"{medals[idx]} **{user_info['name']}** - {user_info['count']} ലിങ്കുകൾ\n"
        
    await update.message.reply_text(text, parse_mode="Markdown")


# --- ഓട്ടോ ഫങ്ഷനുകൾ (ഓരോ 15 മിനിറ്റിലും റൺ ചെയ്യാൻ) ---

# 1 മിനിറ്റ് കഴിഞ്ഞ് ബോട്ടിന്റെ മെസ്സേജ് ഡിലീറ്റ് ചെയ്യുന്ന ജോബ്
async def delete_leaderboard_msg(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    try:
        await context.bot.delete_message(chat_id=job.data["chat_id"], message_id=job.data["message_id"])
    except Exception:
        pass

# 15 മിനിറ്റ് കൂടുമ്പോൾ ബോട്ട് സ്വയം അയക്കുന്ന ലീഡർബോർഡ് ഫങ്ഷൻ
async def auto_send_leaderboard(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    
    text = "📊 **AUTOMATIC LEADERBOARD UPDATE** 📊\n\n"

    # Photo leaderboard ചേർക്കുന്നു
    if chat_id in user_photo_count and user_photo_count[chat_id]:
        sorted_photos = sorted(user_photo_count[chat_id].values(), key=lambda x: x["count"], reverse=True)[:5]
        text += "🖼️ **Top Photo Sharers:**\n"
        for idx, user_info in enumerate(sorted_photos):
            text += f"{medals[idx]} **{user_info['name']}** - {user_info['count']} ഫോട്ടോകൾ\n"
        text += "\n"

    # Link leaderboard ചേർക്കുന്നു
    if chat_id in user_link_count and user_link_count[chat_id]:
        sorted_links = sorted(user_link_count[chat_id].values(), key=lambda x: x["count"], reverse=True)[:5]
        text += "🔗 **Top Link Sharers:**\n"
        for idx, user_info in enumerate(sorted_links):
            text += f"{medals[idx]} **{user_info['name']}** - {user_info['count']} ലിങ്കുകൾ\n"

    # ഡാറ്റ ഉണ്ടെങ്കിൽ മാത്രം അയക്കുന്നു
    if text != "📊 **AUTOMATIC LEADERBOARD UPDATE** 📊\n\n":
        msg = await context.bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
        
        # 1 മിനിറ്റ് (60 സെക്കൻഡ്) കഴിഞ്ഞ് ഡിലീറ്റ് ചെയ്യാൻ ഷെഡ്യൂൾ ചെയ്യുന്നു
        context.job_queue.run_once(
            delete_leaderboard_msg, 
            60, 
            data={"chat_id": chat_id, "message_id": msg.message_id}
        )

# ഓട്ടോമാറ്റിക് ലീഡർബോർഡ് On/Off ചെയ്യാനുള്ള കമാൻഡ് (/autolb on /autolb off)
async def toggle_autolb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if not await is_admin(update, context):
        await update.message.reply_text("❌ നിങ്ങൾക്ക് ഈ കമാൻഡ് ഉപയോഗിക്കാൻ അധികാരമില്ല!")
        return

    if not context.args:
        await update.message.reply_text("⚠️ ഉപയോഗിക്കേണ്ട രീതി: `/autolb on` അല്ലെങ്കിൽ `/autolb off`", parse_mode="Markdown")
        return

    command = context.args[0].lower()
    job_name = f"autolb_{chat_id}"

    if command == "on":
        # പഴയ ജോബ് ഉണ്ടെങ്കിൽ റിമൂവ് ചെയ്യുന്നു
        current_jobs = context.job_queue.get_jobs_by_name(job_name)
        for job in current_jobs:
            job.schedule_removal()

        # 15 മിനിറ്റ് (300 സെക്കൻഡ്) കൂടുമ്പോൾ റൺ ആവാൻ സെറ്റ് ചെയ്യുന്നു
        context.job_queue.run_repeating(
            auto_send_leaderboard,
            interval=900,
            first=10, # കമാൻഡ് അടിച്ച് 10 സെക്കൻഡിനകം ആദ്യ മെസ്സേജ് വരും
            chat_id=chat_id,
            name=job_name
        )
        await update.message.reply_text("✅ ഈ ഗ്രൂപ്പിൽ ഓരോ 15 മിനിറ്റിലും ഓട്ടോ-ലീഡർബോർഡ് (1 മിനിറ്റിൽ ഡിലീറ്റ് ആകുന്നത്) ഓൺ ആക്കി!")

    elif command == "off":
        current_jobs = context.job_queue.get_jobs_by_name(job_name)
        for job in current_jobs:
            job.schedule_removal()
        await update.message.reply_text("🛑 ഓട്ടോ-ലീഡർബോർഡ് ഓഫ് ആക്കി!")

    else:
        await update.message.reply_text("⚠️ ദയവായി `on` അല്ലെങ്കിൽ `off` എന്ന് മാത്രം ചേർക്കുക.", parse_mode="Markdown")


def main():
    keep_alive()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, track_messages), group=1)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("antilink", toggle_antilink))
    app.add_handler(CommandHandler("ban", ban_user))
    app.add_handler(CommandHandler("unban", unban_user))
    app.add_handler(CommandHandler("kick", kick_user))
    app.add_handler(CommandHandler("mute", mute_user))
    app.add_handler(CommandHandler("tmute", timed_mute_user))
    app.add_handler(CommandHandler("unmute", unmute_user))
    
    app.add_handler(CommandHandler("photoleaderboard", photo_leaderboard))
    app.add_handler(CommandHandler("photolb", photo_leaderboard))
    app.add_handler(CommandHandler("linkleaderboard", link_leaderboard))
    app.add_handler(CommandHandler("linklb", link_leaderboard))
    
    # ഓട്ടോ ലീഡർബോർഡ് കമാൻഡ്
    app.add_handler(CommandHandler("autolb", toggle_autolb))

    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_normal_messages))

    print("ബോട്ട് പൂർണ്ണ സജ്ജമാണ്...")
    app.run_polling()

if __name__ == '__main__':
    main()