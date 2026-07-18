import time
import random
import telebot
from telebot.types import ReactionTypeEmoji

# നിങ്ങളുടെ ടെലിഗ്രാം ബോട്ട് ടോക്കൺ
BOT_TOKEN = '8397424887:AAEyNXWcGS6e9NoJ_JrUw_TB6ulRlcm-vL4'
bot = telebot.TeleBot(BOT_TOKEN)

# വെൽക്കം മെസ്സേജ് സെറ്റിംഗ്സ്
welcome_enabled = True

# ലഭ്യമായ ചില ഇമോജി റിയാക്ഷനുകൾ
reactions = ['👍', '❤️', '🔥', '👏', '🎉', '🤩', '👌', '⚡']

# അഡ്മിൻ ആണോ എന്ന് പരിശോധിക്കാനുള്ള ഫങ്ഷൻ
def is_admin(message):
    if message.chat.type == 'private':
        return False
    member = bot.get_chat_member(message.chat.id, message.from_user.id)
    return member.status in ['creator', 'administrator']

# 1. വെൽക്കം മെസ്സേജ് ഓൺ/ഓഫ് (/welcome on അല്ലെങ്കിൽ /welcome off)
@bot.message_handler(commands=['welcome'])
def toggle_welcome(message):
    global welcome_enabled
    
    # കമാൻഡ് മെസ്സേജ് ഉടൻ തന്നെ ഡിലീറ്റ് ചെയ്യുന്നു
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except Exception:
        pass

    if not is_admin(message):
        bot.reply_to(message, 'നിങ്ങൾക്ക് ഈ കമാൻഡ് ഉപയോഗിക്കാൻ അനുവാദമില്ല.')
        return

    # കമാൻഡിനൊപ്പമുള്ള ടെക്സ്റ്റ് (on/off) എടുക്കുന്നു
    args = message.text.split()
    if len(args) > 1:
        status = args[1].lower()
        if status == 'on':
            welcome_enabled = True
            bot.send_message(message.chat.id, 'പുതിയ മെമ്പേഴ്സിനായുള്ള സ്വാഗതം ഓൺ ചെയ്തു.')
        elif status == 'off':
            welcome_enabled = False
            bot.send_message(message.chat.id, 'Welcome മെസ്സേജ് ഓഫ് ചെയ്തു.')
        else:
            bot.send_message(message.chat.id, 'ഉപയോഗിക്കേണ്ട രീതി: /welcome on അല്ലെങ്കിൽ /welcome off')
    else:
        bot.send_message(message.chat.id, 'ഉപയോഗിക്കേണ്ട രീതി: /welcome on അല്ലെങ്കിൽ /welcome off')

# പുതിയ ആളുകൾ ഗ്രൂപ്പിൽ വരുമ്പോൾ
@bot.message_handler(content_types=['new_chat_members'])
def greet_new_members(message):
    if not welcome_enabled:
        return
    for user in message.new_chat_members:
        bot.send_message(message.chat.id, f"ഹലോ {user.first_name}, ഗ്രൂപ്പിലേക്ക് സ്വാഗതം!")

# 2. താൽക്കാലിക മ്യൂട്ട് (/tmute 10) - മെസ്സേജിന് റിപ്ലൈ ആയി നൽകുക
@bot.message_handler(commands=['tmute'])
def temporary_mute(message):
    # കമാൻഡ് മെസ്സേജ് ഉടൻ തന്നെ ഡിലീറ്റ് ചെയ്യുന്നു
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except Exception:
        pass

    if not is_admin(message):
        bot.reply_to(message, 'നിങ്ങൾ ഒരു അഡ്മിൻ അല്ല.')
        return
    
    if not message.reply_to_message:
        bot.send_message(message.chat.id, 'ഏത് യൂസറെയാണ് മ്യൂട്ട് ചെയ്യേണ്ടത്, അവരുടെ മെസ്സേജിന് റിപ്ലൈ ആയി ഈ കമാൻഡ് അടിക്കുക.')
        return

    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        bot.send_message(message.chat.id, 'മിനിറ്റുകൾ കൃത്യമായി നൽകുക. ഉദാഹരണത്തിന്: /tmute 10')
        return

    duration = int(args[1])
    user_id = message.reply_to_message.from_user.id
    until_date = int(time.time()) + (duration * 60)

    try:
        # മെസ്സേജ് അയക്കാനുള്ള പെർമിഷൻ ബ്ലോക്ക് ചെയ്യുന്നു
        bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=user_id,
            until_date=until_date,
            can_send_messages=False
        )
        bot.send_message(message.chat.id, f"{message.reply_to_message.from_user.first_name} എന്ന യൂസറെ {duration} മിനിറ്റിലേക്ക് മ്യൂട്ട് ചെയ്തു.")
    except Exception:
        bot.send_message(message.chat.id, 'മ്യൂട്ട് ചെയ്യാൻ സാധിച്ചില്ല. ബോട്ടിന് അഡ്മിൻ പെർമിഷൻ ഉണ്ടെന്ന് ഉറപ്പാക്കുക.')

# 3. താൽക്കാലിക ബാൻ (/tban 10) - മെസ്സേജിന് റിപ്ലൈ ആയി നൽകുക
@bot.message_handler(commands=['tban'])
def temporary_ban(message):
    # കമാൻഡ് മെസ്സേജ് ഉടൻ തന്നെ ഡിലീറ്റ് ചെയ്യുന്നു
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except Exception:
        pass

    if not is_admin(message):
        bot.reply_to(message, 'നിങ്ങൾ ഒരു അഡ്മിൻ അല്ല.')
        return
    
    if not message.reply_to_message:
        bot.send_message(message.chat.id, 'ഏത് യൂസറെയാണ് ബാൻ ചെയ്യേണ്ടത്, അവരുടെ മെസ്സേജിന് റിപ്ലൈ ആയി ഈ കമാൻഡ് അടിക്കുക.')
        return

    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        bot.send_message(message.chat.id, 'മിനിറ്റുകൾ കൃത്യമായി നൽകുക. ഉദാഹരണത്തിന്: /tban 10')
        return

    duration = int(args[1])
    user_id = message.reply_to_message.from_user.id
    until_date = int(time.time()) + (duration * 60)

    try:
        bot.ban_chat_member(chat_id=message.chat.id, user_id=user_id, until_date=until_date)
        bot.send_message(message.chat.id, f"{message.reply_to_message.from_user.first_name} എന്ന യൂസറെ {duration} മിനിറ്റിലേക്ക് ബാൻ ചെയ്തു.")
    except Exception:
        bot.send_message(message.chat.id, 'ബാൻ ചെയ്യാൻ സാധിച്ചില്ല. ബോട്ടിന് അഡ്മിൻ പെർമിഷൻ ഉണ്ടെന്ന് ഉറപ്പാക്കുക.')

# ലിങ്കുകൾക്ക് റിയാക്ഷൻ നൽകാനുള്ള ഫങ്ഷൻ
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    # മെസ്സേജിൽ ലിങ്കുകൾ (URL) ഉണ്ടോ എന്ന് പരിശോധിക്കുന്നു
    has_link = False
    if message.entities:
        for entity in message.entities:
            if entity.type in ['url', 'text_link']:
                has_link = True
                break

    if has_link:
        # ലിങ്ക് കണ്ടാൽ ഒരു റാണ്ടം ഇമോജി സെലക്ട് ചെയ്ത് റിയാക്ഷൻ നൽകും
        random_emoji = random.choice(reactions)
        try:
            bot.set_message_reaction(
                chat_id=message.chat.id,
                message_id=message.message_id,
                reaction=[ReactionTypeEmoji(type="emoji", emoji=random_emoji)]
            )
        except Exception:
            pass

# ബോട്ട് റൺ ചെയ്യുക
print("ബോട്ട് ഓൺലൈൻ ആയി...")
bot.infinity_polling()