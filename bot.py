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

TOKEN = "8673412670:AAGd09Zfk-RSY83drPF01ZJqniJkrLWDJh4"

# പഴയ മെസ്സേജുകളുടെ ഐഡി സൂക്ഷിക്കാനുള്ള ഗ്ലോബൽ വേരിയബിളുകൾ
last_warning_message_id = {} # {chat_id: message_id}
last_welcome_message_id = {} # {chat_id: message_id}

# --- ഓരോ ഗ്രൂപ്പിനും വെവ്വേറെ ഡാറ്റ സൂക്ഷിക്കാൻ ഡാറ്റാ സ്ട്രക്ചർ മാറ്റി ---
antilink_status = {}  # {chat_id: True/False}
autolb_status = {}    # {chat_id: True/False} -> ഓരോ ഗ്രൂപ്പിലെയും ഓട്ടോ ലീഡർബോർഡ് സ്റ്റാറ്റസ്
user_photo_count = {} # {chat_id: {user_id: {"name": str, "count": int}}}
user_link_count = {}  # {chat_id: {user_id: {"name": str, "count": int}}}
active_chats = set()  # ആക്ടീവ് ആയ ഗ്രൂപ്പുകളുടെ ചാറ്റ് ഐഡികൾ സൂക്ഷിക്കാൻ

# ഷെയർ ബട്ടണിനായുള്ള Inline Keyboard Markup
share_keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("🔗 Inline Share", url="https://t.me/share/url?url=https://t.me/+mJhoOlJlNKwzOThl")]
])

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
        ],
        [
            InlineKeyboardButton("📊 /autolb on", callback_data="none"),
            InlineKeyboardButton("🛑 /autolb off", callback_data="none")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        start_text,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

# --- ഓൺ / ഓഫ് ചെയ്യാനുള്ള കമാൻഡ് ഫങ്ഷൻ (antilink) ---
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

# --- ഓട്ടോ ലീഡർബോർഡ് ഓൺ / ഓഫ് ചെയ്യാനുള്ള കമാൻഡ് ഫങ്ഷൻ (/autolb on / off) ---
async def toggle_autolb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    if not await is_admin(update, context):
        await update.message.reply_text("❌ നിങ്ങൾക്ക് ഈ കമാൻഡ് ഉപയോഗിക്കാൻ അധികാരമില്ല!")
        return

    if not context.args:
        await update.message.reply_text("⚠️ ഉപയോഗിക്കേണ്ട രീതി: `/autolb on` അല്ലെങ്കിൽ `/autolb off`", parse_mode="Markdown")
        return

    command = context.args[0].lower()
    if command == "on":
        autolb_status[chat_id] = True
        active_chats.add(chat_id)
        await update.message.reply_text("✅ ഈ ഗ്രൂപ്പിൽ 1 മിനിറ്റ് കൂടുമ്പോൾ ഓട്ടോമാറ്റിക് ലീഡർബോർഡ് വരുന്നത് ഓൺ ആക്കി!")
    elif command == "off":
        autolb_status[chat_id] = False
        await update.message.reply_text("🛑 ഈ ഗ്രൂപ്പിൽ ഓട്ടോമാറ്റിക് ലീഡർബോർഡ് ഓഫ് ആക്കി!")
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

    # ഈ ഗ്രൂപ്പിൽ antilink ഓൺ ആണോ എന്ന് നോക്കുന്നു (ഡിഫോൾട്ടായി True)
    is_on = antilink_status.get(chat_id, True)
    if not is_on:
        return

    # അഡ്മിൻമാർ അയക്കുന്ന മെസ്സേജുകൾ ഡിലീറ്റ് ചെയ്യരുത്
    if await is_admin(update, context):
        return

    # മെസ്സേജിൽ ലിങ്കുകൾ ഉണ്ടെങ്കിൽ ഒഴിവാക്കുന്നു
    if update.message.entities and any(entity.type in ["url", "text_link"] for entity in update.message.entities):
        return

    try:
        # 1. ഗ്രൂപ്പിൽ വന്ന ലിങ്ക് അല്ലാത്ത ടെക്സ്റ്റ് മെസ്സേജ് ഡിലീറ്റ് ചെയ്യുന്നു
        await context.bot.delete_message(chat_id=chat_id, message_id=update.message.message_id)

        # 2. മെസ്സേജ് അയച്ച ആളെയ 1 മിനിറ്റത്തേക്ക് മ്യൂട്ട് ചെയ്യുന്നു
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

        # 3. മുൻപത്തെ വാണിംഗ് മെസ്സേജ് ഡിലീറ്റ് ചെയ്യുന്നു
        if chat_id in last_warning_message_id:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=last_warning_message_id[chat_id])
            except Exception:
                pass

        # 4. പുതിയ വാണിംഗ് മെസ്സേജ് അയക്കുന്നു
        warning_text = f"⚠️ {user.mention_html()} ഗ്രൂപ്പിൽ ലിങ്ക് മാത്രം ഇടുക! നിങ്ങൾക്ക് 1 മിനിറ്റ് മ്യൂട്ട് നൽകിയിട്ടുണ്ട്."
        sent_message = await context.bot.send_message(chat_id=chat_id, text=warning_text, parse_mode="HTML")
        
        last_warning_message_id[chat_id] = sent_message.message_id

        # 5. വാണിംഗ് മെസ്സേജ് 5 സെക്കൻഡ് കഴിഞ്ഞ് ഡിലീറ്റ് ആകുന്നു
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

# --- ഓരോ ഗ്രൂപ്പിലെയും ഫോട്ടോകളും ലിങ്കുകളും വേറെയായി ട്രാക്ക് ചെയ്യാൻ ---
async def track_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or update.effective_user.is_bot:
        return

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    msg = update.message

    if not msg:
        return

    # ഗ്രൂപ്പിന്റെ ഐഡി ലിസ്റ്റിലേക്ക് ചേർക്കുന്നു
    active_chats.add(chat_id)

    # ഫോട്ടോസ് ട്രാക്ക് ചെയ്യുന്നു
    if msg.photo:
        if chat_id not in user_photo_count:
            user_photo_count[chat_id] = {}
        if user_id not in user_photo_count[chat_id]:
            user_photo_count[chat_id][user_id] = {"name": user_name, "count": 0}
        user_photo_count[chat_id][user_id]["count"] += 1
        user_photo_count[chat_id][user_id]["name"] = user_name

    # ലിങ്കുകൾ ട്രാക്ക് ചെയ്യുന്നു
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

# --- 1. Top 5 Photos Leaderboard കമാൻഡ് ---
async def photo_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    if chat_id not in user_photo_count or not user_photo_count[chat_id]:
        await update.message.reply_text("🖼️ നിലവിൽ ഈ ഗ്രൂപ്പിൽ ഫോട്ടോകൾ അയച്ചവരുടെ ഡാറ്റ ലഭ്യമല്ല.")
        return

    sorted_users = sorted(user_photo_count[chat_id].items(), key=lambda x: x[1]["count"], reverse=True)[:5]
    
    text = "🏆 <b><u>TOP 5 PHOTO LEADERBOARD</u></b> 🏆\n\n"
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    
    for idx, (uid, user_info) in enumerate(sorted_users):
        text += f"{medals[idx]} <a href='tg://user?id={uid}'>{user_info['name']}</a> — <b>{user_info['count']}</b> ഫോട്ടോകൾ 🔥\n"
        
    sent_msg = await update.message.reply_text(text, parse_mode="HTML", reply_markup=share_keyboard)
    
    # 1 മിനിറ്റിന് ശേഷം മെസ്സേജ് താനേ ഡിലീറ്റ് ആകുന്നു
    await asyncio.sleep(60)
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=sent_msg.message_id)
    except Exception:
        pass

# --- 2. Top 5 Links Leaderboard കമാൻഡ് ---
async def link_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if chat_id not in user_link_count or not user_link_count[chat_id]:
        await update.message.reply_text("🔗 നിലവിൽ ഈ ഗ്രൂപ്പിൽ ലിങ്കുകൾ അയച്ചവരുടെ ഡാറ്റ ലഭ്യമല്ല.")
        return

    sorted_users = sorted(user_link_count[chat_id].items(), key=lambda x: x[1]["count"], reverse=True)[:5]
    
    text = "🏆 <b><u>TOP 5 LINK LEADERBOARD</u></b> 🏆\n\n"
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    
    for idx, (uid, user_info) in enumerate(sorted_users):
        text += f"{medals[idx]} <a href='tg://user?id={uid}'>{user_info['name']}</a> — <b>{user_info['count']}</b> ലിങ്കുകൾ ⚡\n"
        
    sent_msg = await update.message.reply_text(text, parse_mode="HTML", reply_markup=share_keyboard)
    
    # 1 മിനിറ്റിന് ശേഷം മെസ്സേജ് താനേ ഡിലീറ്റ് ആകുന്നു
    await asyncio.sleep(900)
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=sent_msg.message_id)
    except Exception:
        pass

# --- ഓട്ടോമാറ്റിക് ലിഡർ ബോർഡ് അയക്കുന്ന ഫങ്ഷൻ (1 മിനിറ്റ് കൂടുമ്പോൾ) ---
async def auto_send_leaderboards(context: ContextTypes.DEFAULT_TYPE):
    for chat_id in list(active_chats):
        # ഓരോ ഗ്രൂപ്പിലും ഓട്ടോ ലീഡർബോർഡ് ഓൺ ആണോ എന്ന് പരിശോധിക്കുന്നു
        if not autolb_status.get(chat_id, False):
            continue

        # 1. ഓട്ടോ ഫോട്ടോ ലീഡർബോർഡ്
        if chat_id in user_photo_count and user_photo_count[chat_id]:
            sorted_p = sorted(user_photo_count[chat_id].items(), key=lambda x: x[1]["count"], reverse=True)[:5]
            text_p = "🏆 <b><u>TOP 5 PHOTO LEADERBOARD</u></b> 🏆\n\n"
            medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
            for idx, (uid, uinfo) in enumerate(sorted_p):
                text_p += f"{medals[idx]} <a href='tg://user?id={uid}'>{uinfo['name']}</a> — <b>{uinfo['count']}</b> ഫോട്ടോകൾ 🔥\n"
            
            try:
                msg_p = await context.bot.send_message(chat_id=chat_id, text=text_p, parse_mode="HTML", reply_markup=share_keyboard)
                # 1 മിനിറ്റ് (900 സെക്കൻഡ്) കഴിയുമ്പോൾ ഡിലീറ്റ് ചെയ്യുന്നു
                asyncio.create_task(delete_after_delay(context, chat_id, msg_p.message_id, 60))
            except Exception as e:
                print(f"ഓട്ടോ ഫോട്ടോ ലീഡർബോർഡ് എറർ: {e}")

        # 2. ഓട്ടോ ലിങ്ക് ലീഡർബോർഡ്
        if chat_id in user_link_count and user_link_count[chat_id]:
            sorted_l = sorted(user_link_count[chat_id].items(), key=lambda x: x[1]["count"], reverse=True)[:5]
            text_l = "🏆 <b><u>TOP 5 LINK LEADERBOARD</u></b> 🏆\n\n"
            medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
            for idx, (uid, uinfo) in enumerate(sorted_l):
                text_l += f"{medals[idx]} <a href='tg://user?id={uid}'>{uinfo['name']}</a> — <b>{uinfo['count']}</b> ലിങ്കുകൾ ⚡\n"
            
            try:
                msg_l = await context.bot.send_message(chat_id=chat_id, text=text_l, parse_mode="HTML", reply_markup=share_keyboard)
                # 1 മിനിറ്റ് (900 സെക്കൻഡ്) കഴിയുമ്പോൾ ഡിലീറ്റ് ചെയ്യുന്നു
                asyncio.create_task(delete_after_delay(context, chat_id, msg_l.message_id, 900))
            except Exception as e:
                print(f"ഓട്ടോ ലിങ്ക് ലീഡർബോർഡ് എറർ: {e}")

async def delete_after_delay(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_id: int, delay: int):
    await asyncio.sleep(delay)
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        pass


def main():
    keep_alive()

    app = Application.builder().token(TOKEN).build()

    # 1 മിനിറ്റ് കൂടുമ്പോൾ ഓട്ടോമാറ്റിക് ലീഡർബോർഡ് പ്രവർത്തിക്കാൻ (900 സെക്കൻഡ്)
    if app.job_queue:
        app.job_queue.run_repeating(auto_send_leaderboards, interval=900, first=10)

    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, track_messages), group=1)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("antilink", toggle_antilink))
    app.add_handler(CommandHandler("autolb", toggle_autolb)) # പുതിയ ഓൺ/ഓഫ് കമാൻഡ്
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

    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_normal_messages))

    print("ബോട്ട് പൂർണ്ണ സജ്ജമാണ്...")
    app.run_polling()

if __name__ == '__main__':
    main()