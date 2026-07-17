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
            "❌ അൺബാൻ ചെയ്യേണ്ട യൂസറുടെ ID നൽകുക. ഉദാഹരണം: /unban 12345678"
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