bot.on("message", async (msg) => {
  if (!msg.text) return;

  // Private chat ഒഴിവാക്കുക
  if (msg.chat.type === "private") return;

  // അഡ്മിൻ ആണോ എന്ന് പരിശോധിക്കുക
  const admins = await bot.getChatAdministrators(msg.chat.id);
  const isAdmin = admins.some(admin => admin.user.id === msg.from.id);

  if (isAdmin) return;

  // Telegram / Web ലിങ്ക് ആണോ?
  const linkRegex = /(https?:\/\/|www\.|t\.me\/|telegram\.me\/)/i;

  // ലിങ്ക് ആണെങ്കിൽ അനുവദിക്കുക
  if (linkRegex.test(msg.text)) return;

  try {
    // യൂസറുടെ ടെക്സ്റ്റ് ഡിലീറ്റ് ചെയ്യുക
    await bot.deleteMessage(msg.chat.id, msg.message_id);

    // മുന്നറിയിപ്പ് അയയ്ക്കുക
    const warn = await bot.sendMessage(
      msg.chat.id,
      `[${
        msg.from.first_name
      }](tg://user?id=${msg.from.id}) ലിങ്ക് മാത്രം അനുവദനീയമാണ്.`,
      {
        parse_mode: "Markdown"
      }
    );

    // 10 സെക്കൻഡിന് ശേഷം മുന്നറിയിപ്പ് ഡിലീറ്റ് ചെയ്യുക
    setTimeout(async () => {
      try {
        await bot.deleteMessage(msg.chat.id, warn.message_id);
      } catch (e) {}
    }, 10000);

  } catch (err) {
    console.log(err);
  }
});