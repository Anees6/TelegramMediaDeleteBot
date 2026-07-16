import os
import time
import telebot
from threading import Thread

# ⚠️ നിങ്ങളുടെ ടെലഗ്രാം ബോട്ട് ടോക്കൺ നേരിട്ട് ഇവിടെ ചേർത്തിട്ടുണ്ട്
BOT_TOKEN = "8673412670:AAFW2QTdkHH_LxecEzJNE-SkflJZe1X8Y0g"

bot = telebot.TeleBot(BOT_TOKEN)

# 🚫 ഗ്രൂപ്പിൽ നിരോധിക്കേണ്ട ചീത്ത വാക്കുകളുടെ ലിസ്റ്റ്
BAD_WORDS = ["badword1", "badword2", "ചീത്തവാക്ക്1"]

# 🛠️ ലിങ്ക് ആണോ എന്ന് പരിശോധിക്കാനുള്ള ഫങ്ക്ഷൻ
def is_link(text):
    if not text:
        return False
    if "http://" in text or "https://" in text or "t.me/" in text or "www." in text or "@" in text:
        return True
    return False

# 🕒 വാർണിങ് മെസ്സേജ് 5 മിനിറ്റ് കഴിഞ്ഞ് ഡിലീറ്റ് ചെയ്യാനുള്ള ഫങ്ക്ഷൻ
def delete_warning_after_delay(chat_id, message_id, delay=300):
    def delay_delete():
        time.sleep(delay)
        try:
            bot.delete_message(chat_id, message_id)
        except Exception as e:
            print(f"Failed to delete warning: {e}")
    Thread(target=delay_delete).start()

# 👤 ഫീച്ചർ 1: പുതിയ ആൾക്കാർ ഗ്രൂപ്പിൽ വരുമ്പോൾ വെൽക്കം മെസ്സേജ് അയക്കുന്നു
@bot.message_handler(content_types=['new_chat_members'])
def welcome_new_member(message):
    for member in message.new_chat_members:
        if member.id == bot.get_me().id:
            continue
            
        user_mention = f"[{member.first_name}](tg://user?id={member.id})"
        welcome_text = f"👋 ഹലോ {user_mention}, നമ്മുടെ ഗ്രൂപ്പിലേക്ക് സ്വാഗതം!\n\n📌 *ഗ്രൂപ്പ് നിയമം:* ഇവിടെ ലിങ്കുകൾ മാത്രമേ അനുവദിക്കൂ. സാധാരണ മെസ്സേജുകൾ സിസ്റ്റം സ്വയം ഡിലീറ്റ് ചെയ്യുന്നതാണ്."
        
        bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown")

# 👮 ഫീച്ചർ 2: അഡ്മിൻ കമാൻഡുകൾ (/ban, /unban, /mute, /unmute)
def is_admin(chat_id, user_id):
    try:
        admins = bot.get_chat_administrators(chat_id)
        return any(admin.user.id == user_id for admin in admins)
    except Exception:
        return False

@bot.message_handler(commands=['ban', 'mute', 'unban', 'unmute'])
def admin_commands(message):
    if not is_admin(message.chat.id, message.from_user.id):
        bot.reply_to(message, "❌ ഈ കമാൻഡ് ഉപയോഗിക്കാൻ നിങ്ങൾ ഒരു അഡ്മിൻ ആയിരിക്കണം!")
        return

    if not message.reply_to_message:
        bot.reply_to(message, "❌ നിങ്ങൾ ഏത് യൂസറെയാണ് ബാൻ/മ്യൂട്ട് ചെയ്യേണ്ടത് എന്ന് വച്ചാൽ ആ മെസ്സേജിന് റിപ്ലൈ ആയി ഈ കമാൻഡ് അടിക്കുക.")
        return

    target_user = message.reply_to_message.from_user
    command = message.text.split()[0].lower()

    try:
        if command == '/ban':
            bot.ban_chat_member(message.chat.id, target_user.id)
            bot.send_message(message.chat.id, f"🛑 {target_user.first_name} നെ ഗ്രൂപ്പിൽ നിന്നും ബാൻ ചെയ്തു!")
        elif command == '/unban':
            bot.unban_chat_member(message.chat.id, target_user.id, only_if_banned=True)
            bot.send_message(message.chat.id, f"✅ {target_user.first_name} ന്റെ ബാൻ നീക്കം ചെയ്തു!")
        elif command == '/mute':
            bot.restrict_chat_member(message.chat.id, target_user.id, can_send_messages=False)
            bot.send_message(message.chat.id, f"🔇 {target_user.first_name} നെ മ്യൂട്ട് ചെയ്തു!")
        elif command == '/unmute':
            bot.restrict_chat_member(message.chat.id, target_user.id, 
                                     can_send_messages=True, can_send_media_messages=True, 
                                     can_send_polls=True, can_add_web_page_previews=True)
            bot.send_message(message.chat.id, f"🔊 {target_user.first_name} ന്റെ മ്യൂട്ട് നീക്കം ചെയ്തു!")
    except Exception as e:
        bot.reply_to(message, f"❌ ഒരു എറർ സംഭവിച്ചു: {e}")

# 💬 ഫീച്ചർ 3 & 4: ചീത്ത വാക്കുകൾ തടയലും ലിങ്ക് അല്ലാത്ത മെസ്സേജുകൾ ഡിലീറ്റ് ചെയ്യലും
@bot.message_handler(func=lambda message: message.chat.type in ['group', 'supergroup'])
def handle_group_moderation(message):
    text = message.text or message.caption
    if not text:
        return

    # അഡ്മിൻമാർ അയക്കുന്ന മെസ്സേജുകൾ ബോട്ട് ഡിലീറ്റ് ചെയ്യില്ല
    if is_admin(message.chat.id, message.from_user.id):
        return

    # 1. ചീത്ത വാക്കുകൾ ഉണ്ടോ എന്ന് പരിശോധിക്കുന്നു
    contains_bad_word = any(word.lower() in text.lower() for word in BAD_WORDS)
    
    if contains_bad_word:
        try:
            bot.delete_message(message.chat.id, message.message_id)
            user_mention = f"[{message.from_user.first_name}](tg://user?id={message.from_user.id})"
            warn = bot.send_message(message.chat.id, f"⚠️ {user_mention}, ദയവായി മോശം വാക്കുകൾ ഉപയോഗിക്കരുത്!", parse_mode="Markdown")
            delete_warning_after_delay(message.chat.id, warn.message_id, delay=60) # 1 മിനിറ്റ് കഴിഞ്ഞ് ഡിലീറ്റ് ചെയ്യും
            return
        except Exception as e:
            print(f"Error filtering bad word: {e}")

    # 2. ലിങ്ക് ആണോ എന്ന് നോക്കുന്നു
    if is_link(text):
        return

    # 3. ലിങ്ക് അല്ലാത്ത മറ്റ് സാധാരണ മെസ്സേജുകൾ ഡിലീറ്റ് ചെയ്യുന്നു
    try:
        bot.delete_message(message.chat.id, message.message_id)
        
        user_mention = f"[{message.from_user.first_name}](tg://user?id={message.from_user.id})"
        warning_text = f"⚠️ ഹേയ് {user_mention}, ഈ ഗ്രൂപ്പിൽ ലിങ്കുകൾ മാത്രമേ അനുവദിക്കൂ! സാധാരണ മെസ്സേജുകൾ ഡിലീറ്റ് ചെയ്യപ്പെടും."
        
        sent_msg = bot.send_message(message.chat.id, warning_text, parse_mode="Markdown")
        delete_warning_after_delay(message.chat.id, sent_msg.message_id, delay=300) # 5 മിനിറ്റ് കഴിഞ്ഞ് ഡിലീറ്റ് ചെയ്യും

    except Exception as e:
        print(f"Error handling text message: {e}")

# ബോട്ട് സ്റ്റാർട്ട് ചെയ്യുന്നു
if __name__ == "__main__":
    print("Bot is running with your token...")
    bot.infinity_polling()