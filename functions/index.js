const TelegramBot = require("node-telegram-bot-api");

// Bot Token സെറ്റ് ചെയ്യുന്നു
const token = "8673412670:AAFW2QTdkHH_LxecEzJNE-SkflJZe1X8Y0g";
const bot = new TelegramBot(token, { polling: true });

// ഓരോ ഗ്രൂപ്പിന്റെയും ഡിലീറ്റ് സമയം സൂക്ഷിക്കാൻ (Default: 15 മിനിറ്റ്)
const groupTimeouts = {}; 

// വെൽക്കം മെസ്സേജ് ഓൺ/ഓഫ് ചെയ്യാൻ
let isWelcomeEnabled = true;

// Anti-Flood ഫീച്ചറിന് വേണ്ടിയുള്ള വേരിയബിളുകൾ
const userMessages = {};
const FLOOD_LIMIT = 5; 
const FLOOD_TIME = 5000; 

// തടയേണ്ട മോശം വാക്കുകളുടെ ലിസ്റ്റ്
const badWords = ["spammer", "scam", "fraud", "abuse"];

console.log("Bot is running successfully with dynamic timeouts...");

// ബോട്ട് സ്റ്റാർട്ട് ചെയ്യുമ്പോൾ എല്ലാ കമാൻഡുകളും ലിസ്റ്റ് ചെയ്തു കാണിക്കുന്നു
bot.onText(/\/start/, (msg) => {
  const commandsList = `
👋 *ഹലോ! ഞാൻ റെഡിയാണ്.*

ഗ്രൂപ്പുകളിൽ വരുന്ന മീഡിയ ഫയലുകളും ലിങ്കുകളും ഞാൻ നിശ്ചിത സമയത്തിന് ശേഷം ഡിലീറ്റ് ചെയ്തോളാം. വെറും ടെക്സ്റ്റ് മെസ്സേജുകൾ അയക്കുന്നവരെ ഞാൻ മ്യൂട്ട് ചെയ്യുന്നതുമായിരിക്കും.

🛠️ *ബോട്ട് കമാൻഡുകളുടെ ലിസ്റ്റ് (ഗ്രൂപ്പ് അഡ്മിൻമാർക്ക് മാത്രം):*

⏱️ *മീഡിയ/ലിങ്ക് ഡിലീറ്റ് ടൈം മാറ്റാൻ:*
• \`/m5\` - 5 മിനിറ്റിന് ശേഷം ഡിലീറ്റ് ചെയ്യാൻ
• \`/m10\` - 10 മിനിറ്റിന് ശേഷം ഡിലീറ്റ് ചെയ്യാൻ
• \`/m15\` - 15 മിനിറ്റിന് ശേഷം ഡിലീറ്റ് ചെയ്യാൻ
_(ഇതുപോലെ \`/m30\` അല്ലെങ്കിൽ \`/m60\` എന്നിങ്ങനെ എത്ര മിനിറ്റ് വേണമെങ്കിലും നൽകാം)_

👋 *വെൽക്കം മെസ്സേജ് നിയന്ത്രിക്കാൻ:*
• \`/welcome on\` - പുതിയ മെമ്പർമാർ വരുമ്പോൾ വെൽക്കം മെസ്സേജ് കാണിക്കാൻ
• \`/welcome off\` - വെൽക്കം മെസ്സേജ് ഓഫ് ചെയ്യാൻ

🔓 *മ്യൂട്ട് ചെയ്തയാളെ അൺമ്യൂട്ട് ചെയ്യാൻ:*
• \`/unmute\` - മ്യൂട്ട് ചെയ്യപ്പെട്ട വ്യക്തിയുടെ ഏതെങ്കിലും പഴയ മെസ്സേജിന് *Reply* ആയി ഈ കമാൻഡ് അടിക്കുക.
  `;

  bot.sendMessage(msg.chat.id, commandsList, { parse_mode: "Markdown" });
});

// സമയം മാറ്റാനുള്ള കമാൻഡ് ഫങ്ഷൻ (/m5, /m10, /m15 മുതലായവ)
bot.onText(/\/m(\d+)/, async (msg, match) => {
  const chatId = msg.chat.id;
  const userId = msg.from.id;
  const minutes = parseInt(match[1]);

  if (msg.chat.type === "private") return;

  try {
    const chatMember = await bot.getChatMember(chatId, userId);
    if (chatMember.status !== "administrator" && chatMember.status !== "creator") {
      return bot.sendMessage(chatId, "❌ ക്ഷമിക്കണം, ഒരു ഗ്രൂപ്പ് അഡ്മിന് മാത്രമേ സമയം മാറ്റാൻ സാധിക്കൂ.");
    }

    // ആ പ്രത്യേക ഗ്രൂപ്പിലെ സമയം മാറ്റുന്നു
    groupTimeouts[chatId] = minutes * 60 * 1000;
    bot.sendMessage(chatId, `⏱️ ഇനി മുതൽ ഈ ഗ്രൂപ്പിലെ മീഡിയകളും ലിങ്കുകളും **${minutes} മിനിറ്റിന്** ശേഷം ഡിലീറ്റ് ചെയ്യപ്പെടും.`, { parse_mode: "Markdown" });
  } catch (e) {
    console.log("Error changing time:", e.message);
  }
});

// വെൽക്കം മെസ്സേജ് ഓൺ/ഓഫ് ചെയ്യാനുള്ള കമാൻഡ് ഫങ്ഷൻ (/welcome on/off)
bot.onText(/\/welcome\s+(on|off)/i, async (msg, match) => {
  const chatId = msg.chat.id;
  const userId = msg.from.id;
  const status = match[1].toLowerCase();

  if (msg.chat.type === "private") return;

  try {
    const chatMember = await bot.getChatMember(chatId, userId);
    if (chatMember.status !== "administrator" && chatMember.status !== "creator") {
      return bot.sendMessage(chatId, "❌ ക്ഷമിക്കണം, ഒരു ഗ്രൂപ്പ് അഡ്മിന് മാത്രമേ വെൽക്കം മെസ്സേജ് ഓൺ/ഓഫ് ചെയ്യാൻ സാധിക്കൂ.");
    }

    if (status === "on") {
      isWelcomeEnabled = true;
      bot.sendMessage(chatId, "✅ പുതിയ മെമ്പർമാർ വരുമ്പോൾ ഇനി മുതൽ ബോട്ട് **സ്വാഗതം (Welcome)** ചെയ്യുന്നതായിരിക്കും.", { parse_mode: "Markdown" });
    } else {
      isWelcomeEnabled = false;
      bot.sendMessage(chatId, "📴 വെൽക്കം മെസ്സേജ് **ഓഫ്** ചെയ്തിരിക്കുന്നു. പുതിയ മെമ്പർമാർ വരുമ്പോൾ ബോട്ട് മെസ്സേജ് അയക്കില്ല.", { parse_mode: "Markdown" });
    }
  } catch (e) {
    console.log("Error toggling welcome settings:", e.message);
  }
});

// അൺമ്യൂട്ട് ചെയ്യാനുള്ള കമാൻഡ് (/unmute)
bot.onText(/\/unmute/, async (msg) => {
  const chatId = msg.chat.id;
  const adminId = msg.from.id;

  if (msg.chat.type === "private") return;

  try {
    const chatMember = await bot.getChatMember(chatId, adminId);
    if (chatMember.status !== "administrator" && chatMember.status !== "creator") return;

    if (!msg.reply_to_message) {
      return bot.sendMessage(chatId, "❌ അൺമ്യൂട്ട് ചെയ്യേണ്ട ആളുടെ മെസ്സേജിന് Reply ആയി /unmute എന്ന് ടൈപ്പ് ചെയ്യുക.");
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

    bot.sendMessage(chatId, `✅ [${targetName}](tg://user?id=${targetUserId}) അൺമ്യൂട്ട് ചെയ്യപ്പെട്ടിരിക്കുന്നു.`, { parse_mode: "Markdown" });
  } catch (e) {
    console.log("Unmute Error:", e.message);
  }
});

// പുതിയ ആളുകൾ ഗ്രൂപ്പിൽ വരുമ്പോൾ വെൽക്കം മെസ്സേജ് അയക്കൽ
bot.on("new_chat_members", async (msg) => {
  if (!isWelcomeEnabled) return;

  const chatId = msg.chat.id;
  const newMember = msg.new_chat_members[0];
  const name = newMember.first_name || "കൂട്ടുകാരൻ";

  try {
    const welcome = await bot.sendMessage(
      chatId,
      `👋 ഹലോ [${name}](tg://user?id=${newMember.id}), ഈ ഗ്രൂപ്പിലേക്ക് സ്വാഗതം!\n\n⚠️ ശ്രദ്ധിക്കുക: ഇത് ലിങ്കുകൾ പങ്കുവെക്കാൻ മാത്രമുള്ള ഗ്രൂപ്പാണ്. മറ്റ് മെസ്സേജുകൾ അയച്ചാൽ ബോട്ട് നിങ്ങളെ മ്യൂട്ട് ചെയ്യുന്നതായിരിക്കും.`,
      { parse_mode: "Markdown" }
    );

    setTimeout(async () => {
      try { await bot.deleteMessage(chatId, welcome.message_id); } catch (e) {}
    }, 30000);
  } catch (e) {
    console.log("Welcome error:", e.message);
  }
});

// മെസ്സേജുകൾ പരിശോധിക്കാനുള്ള പ്രധാന ഫങ്ഷൻ
bot.on("message", async (msg) => {
  if (!msg.from || msg.from.is_bot) return;
  
  if (msg.text && (msg.text === "/start" || msg.text.startsWith("/m") || msg.text === "/unmute" || msg.text.toLowerCase().startsWith("/welcome"))) return;
  
  const chatId = msg.chat.id;
  const userId = msg.from.id;
  const firstName = msg.from.first_name || "യൂസർ";

  let isAdmin = false;
  try {
    const chatMember = await bot.getChatMember(chatId, userId);
    if (chatMember.status === "administrator" || chatMember.status === "creator") {
      isAdmin = true;
    }
  } catch (e) {
    console.log("Error checking admin status:", e.message);
  }

  if (isAdmin) return;

  // Anti-Flood ഫീച്ചർ
  const now = Date.now();
  if (!userMessages[userId]) {
    userMessages[userId] = [];
  }
  userMessages[userId].push(now);
  userMessages[userId] = userMessages[userId].filter(timestamp => now - timestamp < FLOOD_TIME);

  if (userMessages[userId].length > FLOOD_LIMIT) {
    try {
      await bot.deleteMessage(chatId, msg.message_id);
      await bot.restrictChatMember(chatId, userId, {
        permissions: { can_send_messages: false },
        until_date: Math.floor(Date.now() / 1000) + 5 * 60
      });
      const floodWarning = await bot.sendMessage(chatId, `🚨 [${firstName}](tg://user?id=${userId}), ഗ്രൂപ്പിൽ സ്പാം ചെയ്തതിനാൽ നിങ്ങളെ 5 മിനിറ്റത്തേക്ക് മ്യൂട്ട് ചെയ്തിരിക്കുന്നു.`, { parse_mode: "Markdown" });
      setTimeout(() => bot.deleteMessage(chatId, floodWarning.message_id).catch(() => {}), 15000);
      return;
    } catch (e) {
      console.log("Flood restriction error:", e.message);
    }
  }

  // Bad Words Blocker ഫീച്ചർ
  if (msg.text) {
    const hasBadWord = badWords.some(word => msg.text.toLowerCase().includes(word));
    if (hasBadWord) {
      try {
        await bot.deleteMessage(chatId, msg.message_id);
        const badWordWarning = await bot.sendMessage(chatId, `❌ [${firstName}](tg://user?id=${userId}), ഗ്രൂപ്പിൽ മോശം വാക്കുകൾ ഉപയോഗിക്കാൻ പാടില്ല.`, { parse_mode: "Markdown" });
        setTimeout(() => bot.deleteMessage(chatId, badWordWarning.message_id).catch(() => {}), 10000);
        return;
      } catch (e) {
        console.log("Bad word filter error:", e.message);
      }
    }
  }

  // മീഡിയ ഫയലുകൾ ഉണ്ടോ എന്ന് പരിശോധിക്കുന്നു
  const isMedia = msg.photo || msg.video || msg.document || msg.audio || msg.voice || msg.sticker || msg.animation || msg.video_note;

  // ലിങ്കുകൾ ഉണ്ടോ എന്ന് പരിശോധിക്കുന്നു (കൂടുതൽ കൃത്യതയോടെ)
  let isLink = false;
  if (msg.entities) {
    isLink = msg.entities.some(entity => entity.type === "url" || entity.type === "text_link");
  }
  if (msg.text) {
    const textLower = msg.text.toLowerCase();
    if (textLower.includes("http://") || textLower.includes("https://") || textLower.includes("t.me/") || textLower.includes("www.")) {
      isLink = true;
    }
  }

  // ഈ ഗ്രൂപ്പിലെ ഡിലീറ്റ് സമയം എടുക്കുന്നു (ഇല്ലെങ്കിൽ ഡിഫോൾട്ട് 15 മിനിറ്റ്)
  const currentTimeout = groupTimeouts[chatId] || (15 * 60 * 1000);

  // മീഡിയയോ ലിങ്കോ ആണെങ്കിൽ ടൈമർ വെച്ച് ഡിലീറ്റ് ചെയ്യുന്നു
  if (isMedia || isLink) {
    setTimeout(async () => {
      try {
        await bot.deleteMessage(chatId, msg.message_id);
        console.log(`Deleted media/link after timeout in chat ${chatId}`);
      } catch (e) {
        console.log("Error deleting media/link:", e.message);
      }
    }, currentTimeout);
  } 
  // വെറും ടെക്സ്റ്റ് മെസ്സേജ് ആണെങ്കിൽ ഉടൻ ഡിലീറ്റ് ചെയ്ത് മ്യൂട്ട് ചെയ്യുന്നു
  else if (msg.text) {
    try {
      await bot.deleteMessage(chatId, msg.message_id);
      
      await bot.restrictChatMember(chatId, userId, {
        permissions: {
          can_send_messages: false,
          can_send_media_messages: false,
          can_send_polls: false,
          can_send_other_messages: false,
          can_add_web_page_previews: false
        }
      });

      const warningMsg = await bot.sendMessage(
        chatId, 
        `🔒 [${firstName}](tg://user?id=${userId}), ഇത് ലിങ്കുകൾ ഇടാൻ മാത്രമുള്ള ഗ്രൂപ്പ് ആണ്. ചട്ടങ്ങൾ ലംഘിച്ചതിനാൽ നിങ്ങളെ മ്യൂട്ട് ചെയ്തിരിക്കുന്നു!`, 
        { parse_mode: "Markdown" }
      );

      setTimeout(async () => {
        try { await bot.deleteMessage(chatId, warningMsg.message_id); } catch (err) {}
      }, 15000);

    } catch (e) {
      console.log("Error handling text/mute message:", e.message);
    }
  }
});