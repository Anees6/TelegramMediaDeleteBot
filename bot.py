import re
from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes

# ലിങ്കുകൾ ഉണ്ടോ എന്ന് പരിശോധിക്കാനുള്ള റീജെക്സ് (Regex)
LINK_REGEX = r'(https?://[^\s]+|www\.[^\s]+)'

async def check_text_only(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # മെസ്സേജ് ഇല്ലെങ്കിലോ ടെക്സ്റ്റ് ഇല്ലെങ്കിലോ ഒഴിവാക്കുക
    if not update.message or not update.message.text:
        return

    # അഡ്മിൻമാർ അയക്കുന്ന മെസ്സേജുകൾ ഡിലീറ്റ് ചെയ്യേണ്ടതില്ലെങ്കിൽ ഇത് നിലനിർത്താം
    if await is_admin(update, context):
        return

    message_text = update.message.text
    
    # മെസ്സേജിൽ ലിങ്ക് ഉണ്ടോ എന്ന് പരിശോധിക്കുന്നു
    # ലിങ്ക് ഉണ്ടെങ്കിൽ ഒന്നും ചെയ്യേണ്ടതില്ല (റിട്ടേൺ ചെയ്യും)
    if re.search(LINK_REGEX, message_text, re.IGNORECASE):
        return

    # ലിങ്ക് ഇല്ലാത്ത വെറും ടെക്സ്റ്റ് മെസ്സേജ് ആണെങ്കിൽ താഴോട്ടുള്ള കോഡ് പ്രവർത്തിക്കും
    target_user = update.message.from_user
    user_id = target_user.id
    
    # വെറും ടെക്സ്റ്റ് അടങ്ങിയ മെസ്സേജ് ഉടൻ തന്നെ ഡിലീറ്റ് ചെയ്യുന്നു
    try:
        await update.message.delete()
    except Exception as e:
        print(f"മെസ്സേജ് ഡിലീറ്റ് ചെയ്യാൻ സാധിച്ചില്ല: {e}")
        return

    # യൂസറുടെ നിലവിലുള്ള വാണിംഗ് കൗണ്ട് എടുക്കുന്നു (ഇല്ലെങ്കിൽ 0)
    if 'text_warnings' not in context.user_data:
        context.user_data['text_warnings'] = {}
        
    current_warnings = context.user_data['text_warnings'].get(user_id, 0) + 1
    context.user_data['text_warnings'][user_id] = current_warnings

    # 3 വാണിംഗ് ആയാൽ മ്യൂട്ട് ചെയ്യും
    if current_warnings >= 3:
        try:
            mute_permissions = ChatPermissions(can_send_messages=False)
            await update.effective_chat.restrict_member(
                user_id=user_id, permissions=mute_permissions
            )
            await update.effective_chat.send_message(
                f"🔇 {target_user.mention_html()} താങ്കൾ ലിങ്ക് ഇല്ലാതെ 3 തവണ മെസ്സേജ് അയച്ചതിനാൽ ഗ്രൂപ്പിൽ നിന്നും മ്യൂട്ട് ചെയ്തിരിക്കുന്നു. ഇനി ലിങ്കുകൾ മാത്രമേ ഷെയർ ചെയ്യാൻ സാധിക്കൂ.",
                parse_mode="HTML"
            )
            # മ്യൂട്ട് ചെയ്ത ശേഷം വാണിംഗ് കൗണ്ട് റീസെറ്റ് ചെയ്യുന്നു
            context.user_data['text_warnings'][user_id] = 0
        except Exception as e:
            await update.effective_chat.send_message(f"❌ മ്യൂട്ട് ചെയ്യാൻ സാധിച്ചില്ല: {e}")
    else:
        # വാണിംഗ് മെസ്സേജ് അയക്കുന്നു
        await update.effective_chat.send_message(
            f"⚠️ {target_user.mention_html()}, ഈ ഗ്രൂപ്പിൽ ലിങ്കുകൾ മാത്രമേ അനുവദിക്കൂ. വെറും ടെക്സ്റ്റ് മെസ്സേജുകൾ അയക്കാൻ പാടുള്ളതല്ല. താങ്കളുടെ മെസ്സേജ് ഡിലീറ്റ് ചെയ്തിട്ടുണ്ട്.\n\n"
            f"Status: **{current_warnings}/3 Warnings**",
            parse_mode="HTML"
        )