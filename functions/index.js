const TelegramBot = require("node-telegram-bot-api");

// Bot Token സെറ്റ് ചെയ്യുന്നു
const token = "8673412670:AAFW2QTdkHH_LxecEzJNE-SkflJZe1X8Y0g";
const bot = new TelegramBot(token, { polling: true });

// ഫിക്സഡ് ഡിലീറ്റ് സമയം: 15 മിനിറ്റ് (മില്ലിസെക്കൻഡിൽ)
const DELETE_TIMEOUT = 15 * 60 * 1000; 

// വെൽക്കം മെസ്സേജ് ഓൺ/ഓഫ് ചെയ്യാനുള്ള വേരിയബിൾ (Default: true)
let isWelcomeEnabled = true;

// Anti-Flood ഫീച്ചറിന് വേണ്ടിയുള്ള വേരിയബിളുകൾ
const userMessages = {};
const FLOOD_LIMIT = 5; 
const FLOOD_TIME = 5000; 

// തടയേണ്ട മോശം വാക്കുകളുടെ ലിസ്റ്റ്
const badWords = ["spammer", "scam", "fraud", "abuse"];

// ലിങ്ക് മെസ്സേജുകൾക്ക് നൽകാനുള്ള വിവിധ റിയാക്ഷനുകളുടെ ലിസ്റ്റ്
const reactions = ["👍", "🔥", "❤️", "👏", "🤩", "🎉", "⚡", "👀"];

// അനൗൺസ്മെന്റ് മെസ്സേജുകളുടെ ID സൂക്ഷിക്കാൻ
const announcementMessages = new Set();

// ഗ്ലോബൽ എററുകൾ കാരണം ബോട്ട് ക്രാഷ് ആകാതിരിക്കാൻ
process.on('uncaughtException', (err) => {
  console.log('Caught exception: ', err);
});
process.on('unhandledRejection', (reason, p) => {
  console.log('Unhandled Rejection at: Promise', p, 'reason:', reason);
});

console.log("Bot is running perfectly with global error handling...");

// ബോട്ട് സ്റ്റാർട്ട് ചെയ്യുമ്പോൾ കാണിക്കുന്ന മെസ്സേജ്
bot.onText(/\/start/, (msg) => {
  const commandsList = `
👋 *ഹലോ! ഞാൻ റെഡിയാണ്.*

🛠️ *അഡ്മിൻ കമാൻഡുകൾ (ഗ്രൂപ്പിൽ മാത്രം):*
• \`/say [മെസ്സേജ്]\` - ബോട്ടിന്റെ പേരിൽ അനൗൺസ്മെന്റ് നടത്താൻ.
• \`/mute\` - ഒരാളുടെ മെസ്സേജിന് Reply ആയി അടിച്ചാൽ അയാളെ മ്യൂട്ട് ചെയ്യാം.
• \`/unmute\` - ഒരാളുടെ മെസ്സേജിന് Reply ആയി അടിച്ചാൽ മ്യൂട്ട് മാറ്റാം.
• \`/ban\` - ഒരാളുടെ മെസ്സേജിന് Reply ആയി അടിച്ചാൽ ഗ്രൂപ്പിൽ നിന്ന് ബാൻ ചെയ്യാം.
• \`/unban\` - ബാൻ ചെയ്തയാളുടെ യൂസർ ഐഡി വെച്ച് ബാൻ മാറ്റാം (\`/unban USER_ID\`).
• \`/welcome on/off\` - വെൽക്കം മെസ്സേജ് നിയന്ത്രിക്കാൻ.
  `;
  bot.sendMessage(msg.chat.id, commandsList, { parse_mode: "Markdown" }).catch(()=>{});
});

// 📢 അനൗൺസ്മെന്റ് കമാൻഡ് (/say മെസ്സേജ്)
bot.onText(/\/say\s+(.+)/, async (msg, match) => {
  const chatId = msg.chat.id;
  const userId = msg.from.id;
  const announcementText = match[1];

  if (msg.chat.type === "private") return;

  try {
    const chatMember = await bot.getChatMember(chatId, userId);
    if (chatMember.status !== "administrator" && chatMember.status !== "creator") return;

    await bot.deleteMessage(chatId, msg.message_id).catch(() => {});
    const sentMsg = await bot.sendMessage(chatId, `📢 *അനൗൺസ്മെന്റ്:*\n\n${announcementText}`, { parse_mode: "Markdown" });
    announcementMessages.add(sentMsg.message_id);
  } catch (e) {
    console.log("Announcement Error:", e.message);
  }
});

// 🔇 മ്യൂട്ട് കമാൻഡ് (/mute)
bot.onText(/\/mute/, async (msg) => {
  const chatId = msg.chat.id;
  const adminId = msg.from.id;

  if (msg.chat.type === "private") return;

  try {
    const chatMember = await bot.getChatMember(chatId, adminId);
    if (chatMember.status !== "administrator" && chatMember.status !== "creator") return;

    if (!msg.reply_to_message) {
      return bot.sendMessage(chatId, "❌ മ്യൂട്ട് ചെയ്യേണ്ട ആളുടെ മെസ്സേജിന് Reply ആയി /mute എന്ന് അടിക്കുക.").catch(()=>{});
    }

    const targetUserId = msg.reply_to_message.from.id;
    const targetName = msg.reply_to_message.from.first_name || "യൂസർ";

    await bot.restrictChatMember(chatId, targetUserId, { permissions: { can_send_messages: false } });
    bot.sendMessage(chatId, `🔇 [${targetName}](tg://user?id=${targetUserId}) ഗ്രൂപ്പിൽ മ്യൂട്ട് ചെയ്യപ്പെട്ടിരിക്കുന്നു.`, { parse_mode: "Markdown" }).catch(()=>{});
  } catch (e) {
    console.log("Mute Error:", e.message);
  }
});

// 🔊 അൺമ്യൂട്ട് കമാൻഡ് (/unmute)
bot.onText(/\/unmute/, async (msg) => {
  const chatId = msg.chat.id;
  const adminId = msg.from.id;

  if (msg.chat.type === "private") return;

  try {
    const chatMember = await bot.getChatMember(chatId, adminId);
    if (chatMember.status !== "administrator" && chatMember.status !== "creator") return;

    if (!msg.reply_to_message) {
      return bot.sendMessage(chatId, "❌ അൺമ്യൂട്ട് ചെയ്യേണ്ട ആളുടെ മെസ്സേജിന് Reply ആയി /unmute എന്ന് അടിക്കുക.").catch(()=>{});
    }

    const targetUserId = msg.reply_to_message.from.id;
    const targetName = msg.reply_to_message.from.first_name || "യൂസർ";

    await bot.restrictChatMember(chatId, targetUserId, {
      permissions: {
        can_send_messages: true,
        can_send_media_messages: true,
        can_send_polls: true,
        can_send_other_messages: true,
        can_add_web_page_previews: true
      }
    });

    bot.sendMessage(chatId, `🔊 [${targetName}](tg://user?id=${targetUserId}) അൺമ്യൂട്ട് ചെയ്യപ്പെട്ടു.`, { parse_mode: "Markdown" }).catch(()=>{});
  } catch (e) {
    console.log("Unmute Error:", e.message);
  }
});

// 🚫 ബാൻ കമാൻഡ് (/ban)
bot.onText(/\/ban/, async (msg) => {
  const chatId = msg.chat.id;
  const adminId = msg.from.id;

  if (msg.chat.type === "private") return;

  try {
    const chatMember = await bot.getChatMember(chatId, adminId);
    if (chatMember.status !== "administrator" && chatMember.status !== "creator") return;

    if (!msg.reply_to_message) {
      return bot.sendMessage(chatId, "❌ ബാൻ ചെയ്യേണ്ട ആളുടെ മെസ്സേജിന് Reply ആയി /ban എന്ന് അടിക്കുക.").catch(()=>{});
    }

    const targetUserId = msg.reply_to_message.from.id;
    const targetName = msg.reply_to_message.from.first_name || "യൂസർ";

    await bot.banChatMember(chatId, targetUserId);
    bot.sendMessage(chatId, `🚫 [${targetName}](tg://user?id=${targetUserId}) ഗ്രൂപ്പിൽ നിന്നും ബാൻ ചെയ്യപ്പെട്ടു.`, { parse_mode: "Markdown" }).catch(()=>{});
  } catch (e) {
    console.log("Ban Error:", e.message);
  }
});

// 🔓 അൺബാൻ കമാൻഡ് (/unban USER_ID)
bot.onText(/\/unban\s+(\d+)/, async (msg, match) => {
  const chatId = msg.chat.id;
  const adminId = msg.from.id;
  const targetUserId = match[1];

  if (msg.chat.type === "private") return;

  try {
    const chatMember = await bot.getChatMember(chatId, adminId);
    if (chatMember.status !== "administrator" && chatMember.status !== "creator") return;

    await bot.unbanChatMember(chatId, targetUserId, { only_if_banned: true });
    bot.sendMessage(chatId, `✅ യൂസർ ഐഡി \`${targetUserId}\` വിജയകരമായി അൺബാൻ ചെയ്യപ്പെട്ടു.`, { parse_mode: "Markdown" }).catch(()=>{});
  } catch (e) {
    console.log("Unban Error:", e.message);
  }
});

// വെൽക്കം മെസ്സേജ് കൺട്രോൾ ഫങ്ഷൻ
bot.onText(/\/welcome\s+(on|off)/i, async (msg, match) => {
  const chatId = msg.chat.id;
  const userId = msg.from.id;
  const status = match[1].toLowerCase();

  if (msg.chat.type === "private") return;

  try {
    const chatMember = await bot.getChatMember(chatId, userId);
    if (chatMember.status !== "administrator" && chatMember.status !== "creator") return;

    isWelcomeEnabled = status === "on";
    bot.sendMessage(chatId, `✅ വെൽക്കം മെസ്സേജ് *${status.toUpperCase()}* ആക്കി.`, { parse_mode: "Markdown" }).catch(()=>{});
  } catch (e) {
    console.log("Welcome toggle error:", e.message);
  }
});

// പുതിയ ആളുകൾ വരുമ്പോൾ വെൽക്കം മെസ്സേജ്
bot.on("new_chat_members", async (msg) => {
  if (!isWelcomeEnabled) return;
  const chatId = msg.chat.id;
  const newMember = msg.new_chat_members[0];
  const name = newMember.first_name || "കൂട്ടുകാരൻ";

  try {
    const welcome = await bot.sendMessage(
      chatId,
      `👋 ഹലോ [${name}](tg://user?id=${newMember.id}), ഗ്രൂപ്പിലേക്ക് സ്വാഗതം!\n\n⚠️ ഇവിടെ ലിങ്കുകളും മീഡിയകളും മാത്രമേ അനുവദിക്കൂ.`,
      { parse_mode: "Markdown" }
    );
    setTimeout(() => { bot.deleteMessage(chatId, welcome.message_id).catch(()=>{}); }, 30000);
  } catch (e) {
    console.log("Welcome error:", e.message);
  }
});

// മെസ്സേജുകൾ പരിശോധിക്കാനും ഡിലീറ്റ് ചെയ്യാനുമുള്ള ഫങ്ഷൻ
bot.on("message", async (msg) => {
  if (!msg.from || msg.from.is_bot) return;
  
  // ബോട്ട് കമാൻഡുകൾ ആണെങ്കിൽ പ്രോസസ്സ് ചെയ്യില്ല
  if (msg.text && (msg.text === "/start" || msg.text.startsWith("/say") || msg.text === "/mute" || msg.text === "/unmute" || msg.text === "/ban" || msg.text.startsWith("/unban") || msg.text.toLowerCase().startsWith("/welcome"))) return;
  
  const chatId = msg.chat.id;
  const userId = msg.from.id;
  const firstName = msg.from.first_name || "യൂസർ";

  // അഡ്മിൻ ആണോ എന്ന് പരിശോധിക്കുന്നു
  let isAdmin = false;
  try {
    const chatMember = await bot.getChatMember(chatId, userId);
    if (chatMember.status === "administrator" || chatMember.status === "creator") {
      isAdmin = true;
    }
  } catch (e) {
    console.log("Error checking admin status:", e.message);
  }

  // അഡ്മിൻ അല്ലെങ്കിൽ മാത്രം Anti-Flood ഫീച്ചർ പ്രവർത്തിക്കും
  if (!isAdmin) {
    const now = Date.now();
    if (!userMessages[userId]) userMessages[userId] = [];
    userMessages[userId].push(now);
    userMessages[userId] = userMessages[userId].filter(timestamp => now - timestamp < FLOOD_TIME);

    if (userMessages[userId].length > FLOOD_LIMIT) {
      try {
        await bot.deleteMessage(chatId, msg.message_id).catch(()=>{});
        await bot.restrictChatMember(chatId, userId, {
          permissions: { can_send_messages: false },
          until_date: Math.floor(Date.now() / 1000) + 5 * 60
        }).catch(()=>{});
        const floodWarning = await bot.sendMessage(chatId, `🚨 [${firstName}](tg://user?id=${userId}), സ്പാം ചെയ്തതിനാൽ 5 മിനിറ്റത്തേക്ക് മ്യൂട്ട് ചെയ്തു.`, { parse_mode: "Markdown" });
        setTimeout(() => bot.deleteMessage(chatId, floodWarning.message_id).catch(() => {}), 15000);
        return;
      } catch (e) {
        console.log("Flood restriction error:", e.message);
      }
    }

    // Bad Words Blocker
    if (msg.text) {
      const hasBadWord = badWords.some(word => msg.text.toLowerCase().includes(word));
      if (hasBadWord) {
        try {
          await bot.deleteMessage(chatId, msg.message_id).catch(()=>{});
          const badWordWarning = await bot.sendMessage(chatId, `❌ [${firstName}](tg://user?id=${userId}), മോശം വാക്കുകൾ ഉപയോഗിക്കരുത്.`, { parse_mode: "Markdown" });
          setTimeout(() => bot.deleteMessage(chatId, badWordWarning.message_id).catch(() => {}), 10000);
          return;
        } catch (e) {
          console.log("Bad word filter error:", e.message);
        }
      }
    }
  }

  // മീഡിയ ഫയലുകൾ ഉണ്ടോ എന്ന് പരിശോധിക്കുന്നു
  const isMedia = msg.photo || msg.video || msg.document || msg.audio || msg.voice || msg.sticker || msg.animation || msg.video_note;

  // ലിങ്കുകൾ ഉണ്ടോ എന്ന് പരിശോധിക്കുന്നു
  let isLink = false;
  if (msg.entities) {
    isLink = msg.entities.some(entity => entity.type === "url" || entity.type === "text_link");
  }
  if (msg.caption_entities) {
    isLink = isLink || msg.caption_entities.some(entity => entity.type === "url" || entity.type === "text_link");
  }
  const textToCheck = (msg.text || msg.caption || "").toLowerCase();
  if (textToCheck.includes("http://") || textToCheck.includes("https://") || textToCheck.includes("t.me/") || textToCheck.includes("www.")) {
    isLink = true;
  }

  // 1. ലിങ്ക് അടങ്ങിയ മെസ്സേജ് ആണെങ്കിൽ റിയാക്ഷൻ ഇടുകയും 15 മിനിറ്റിൽ ഡിലീറ്റ് ചെയ്യുകയും ചെയ്യുന്നു
  if (isLink) {
    try {
      const randomEmoji = reactions[Math.floor(Math.random() * reactions.length)];
      await bot.setMessageReaction(chatId, msg.message_id, {
        reaction: [{ type: "emoji", emoji: randomEmoji }],
        is_big: false
      }).catch(()=>{});
    } catch (e) {}

    setTimeout(() => {
      if (!announcementMessages.has(msg.message_id)) {
        bot.deleteMessage(chatId, msg.message_id).catch(()=>{});
      }
    }, DELETE_TIMEOUT);
  } 
  
  // 2. വെറും മീഡിയ ഫയൽ ആണെങ്കിൽ (15 മിനിറ്റിൽ ഡിലീറ്റ് ചെയ്യും)
  else if (isMedia) {
    setTimeout(() => {
      if (!announcementMessages.has(msg.message_id)) {
        bot.deleteMessage(chatId, msg.message_id).catch(()=>{});
      }
    }, DELETE_TIMEOUT);
  } 
  
  // 3. ലിങ്കോ മീഡിയയോ അല്ലാത്ത വെറും സാധാരണ മെസ്സേജ് ആണെങ്കിൽ
  else {
    // അഡ്മിൻമാർ അയക്കുന്ന സാധാരണ ടെക്സ്റ്റ് മെസ്സേജുകൾ 15 മിനിറ്റിൽ ഡിലീറ്റ് ചെയ്യും
    if (isAdmin) {
      setTimeout(() => {
        if (!announcementMessages.has(msg.message_id)) {
          bot.deleteMessage(chatId, msg.message_id).catch(()=>{});
        }
      }, DELETE_TIMEOUT);
    } 
    // മറ്റുള്ള സാധാരണ യൂസർമാർ അയക്കുന്നതാണെങ്കിൽ അപ്പോൾ തന്നെ ഡിലീറ്റ് ചെയ്ത് മ്യൂട്ട് ആക്കുകയും 1 മിനിറ്റ് വാണിംഗ് നൽകുകയും ചെയ്യും
    else {
      try {
        // വന്ന മെസ്സേജ് ഉടൻ തന്നെ ഡിലീറ്റ് ചെയ്യുന്നു
        await bot.deleteMessage(chatId, msg.message_id).catch((err) => {
          console.log("Original message delete failed:", err.message);
        });

        // ആ യൂസറെ ഗ്രൂപ്പിൽ ഓട്ടോമാറ്റിക്കായി മ്യൂട്ട് ചെയ്യുന്നു
        await bot.restrictChatMember(chatId, userId, {
          permissions: {
            can_send_messages: false,
            can_send_media_messages: false,
            can_send_polls: false,
            can_send_other_messages: false,
            can_add_web_page_previews: false
          }
        }).catch((err) => {
          console.log("Auto-mute failed:", err.message);
        });

        // മെൻഷൻ ചെയ്ത് വാണിംഗ് അയക്കുന്നു
        const warningMsg = await bot.sendMessage(
          chatId, 
          `🔒 [${firstName}](tg://user?id=${userId}), ഇത് ലിങ്കുകളും മീഡിയകളും പങ്കുവെക്കാനുള്ള ഗ്രൂപ്പ് മാത്രമാണ്! സാധാരണ മെസ്സേജുകൾ അനുവദിക്കില്ല. ചട്ടങ്ങൾ ലംഘിച്ചതിനാൽ നിങ്ങളെ മ്യൂട്ട് ചെയ്തിരിക്കുന്നു.`, 
          { parse_mode: "Markdown" }
        ).catch((err) => { console.log("Warning send failed:", err.message); });

        // വാണിംഗ് മെസ്സേജ് കൃത്യം 1 മിനിറ്റിൽ (60000 ms) ഡിലീറ്റ് ചെയ്യുന്നു
        if (warningMsg) {
          setTimeout(() => {
            bot.deleteMessage(chatId, warningMsg.message_id).catch((err) => {
              console.log("Warning message delete failed:", err.message);
            });
          }, 60000);
        }

      } catch (e) {
        console.log("Error executing text delete/warning/mute:", e.message);
      }
    }
  }
});