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

console.log("Bot is running: Warning message fixing included...");

// ബോട്ട് സ്റ്റാർട്ട് ചെയ്യുമ്പോൾ കാണിക്കുന്ന മെസ്സേജ്
bot.onText(/\/start/, (msg) => {
  const commandsList = `
👋 *ഹലോ! ഞാൻ റെഡിയാണ്.*

• ഈ ഗ്രൂപ്പിൽ വരുന്ന ലിങ്കുകളും മീഡിയകളും (അഡ്മിൻമാരുടേത് ഉൾപ്പെടെ) *15 മിനിറ്റിന്* ശേഷം ഓട്ടോമാറ്റിക്കായി ഡിലീറ്റ് ചെയ്യപ്പെടും.
• ലിങ്കുകൾ വരുമ്പോൾ ഞാൻ അതിന് റിയാക്ഷനുകൾ നൽകും.
• ലിങ്ക് അല്ലാത്ത വെറും മെസ്സേജുകൾ അയച്ചാൽ ഉടൻ ഡിലീറ്റ് ചെയ്ത് ഞാൻ 10 സെക്കൻഡ് വാണിംഗ് നൽകും.

🛠️ *ബോട്ട് കമാൻഡുകൾ:*
• \`/welcome on\` - പുതിയ മെമ്പർമാർ വരുമ്പോൾ വെൽക്കം മെസ്സേജ് കാണിക്കാൻ (Admin Only)
• \`/welcome off\` - വെൽക്കം മെസ്സേജ് ഓഫ് ചെയ്യാൻ (Admin Only)
  `;

  bot.sendMessage(msg.chat.id, commandsList, { parse_mode: "Markdown" });
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

// പുതിയ ആളുകൾ ഗ്രൂപ്പിൽ വരുമ്പോൾ വെൽക്കം മെസ്സേജ് അയക്കൽ
bot.on("new_chat_members", async (msg) => {
  if (!isWelcomeEnabled) return;

  const chatId = msg.chat.id;
  const newMember = msg.new_chat_members[0];
  const name = newMember.first_name || "കൂട്ടുകാരൻ";

  try {
    const welcome = await bot.sendMessage(
      chatId,
      `👋 ഹലോ [${name}](tg://user?id=${newMember.id}), ഈ ഗ്രൂപ്പിലേക്ക് സ്വാഗതം!\n\n⚠️ ഇവിടെ ലിങ്കുകളും മീഡിയകളും മാത്രമേ അനുവദിക്കൂ. മറ്റ് മെസ്സേജുകൾ ഉടൻ ഡിലീറ്റ് ചെയ്യപ്പെടും.`,
      { parse_mode: "Markdown" }
    );

    setTimeout(async () => {
      try { await bot.deleteMessage(chatId, welcome.message_id); } catch (e) {}
    }, 30000);
  } catch (e) {
    console.log("Welcome error:", e.message);
  }
});

// മെസ്സേജുകൾ പരിശോധിക്കാനും ഡിലീറ്റ് ചെയ്യാനുമുള്ള ഫങ്ഷൻ
bot.on("message", async (msg) => {
  if (!msg.from || msg.from.is_bot) return;
  
  // ബോട്ട് കമാൻഡുകൾ ഒഴിവാക്കുന്നു
  if (msg.text && (msg.text === "/start" || msg.text.toLowerCase().startsWith("/welcome"))) return;
  
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
  }

  // മീഡിയ ഫയലുകൾ ഉണ്ടോ എന്ന് പരിശോധിക്കുന്നു
  const isMedia = msg.photo || msg.video || msg.document || msg.audio || msg.voice || msg.sticker || msg.animation || msg.video_note;

  // ലിങ്കുകൾ ഉണ്ടോ എന്ന് പരിശോധിക്കുന്നു
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

  // 1. ലിങ്ക് മെസ്സേജ് ആണെങ്കിൽ റിയാക്ഷൻ ഇടുകയും 15 മിനിറ്റിൽ ഡിലീറ്റ് ചെയ്യുകയും ചെയ്യുന്നു
  if (isLink) {
    try {
      const randomEmoji = reactions[Math.floor(Math.random() * reactions.length)];
      await bot.setMessageReaction(chatId, msg.message_id, {
        reaction: [{ type: "emoji", emoji: randomEmoji }],
        is_big: false
      });
    } catch (e) {
      console.log("Error adding reaction:", e.message);
    }

    // 15 മിനിറ്റിന് ശേഷം ഡിലീറ്റ് ചെയ്യുന്നു
    setTimeout(async () => {
      try { await bot.deleteMessage(chatId, msg.message_id); } catch (e) {}
    }, DELETE_TIMEOUT);
  } 
  
  // 2. ലിങ്ക് അല്ലാത്ത വെറും മീഡിയ ആണെങ്കിൽ 15 മിനിറ്റിൽ ഡിലീറ്റ് ചെയ്യുന്നു
  else if (isMedia) {
    setTimeout(async () => {
      try { await bot.deleteMessage(chatId, msg.message_id); } catch (e) {}
    }, DELETE_TIMEOUT);
  } 
  
  // 3. ലിങ്കോ മീഡിയയോ അല്ലാത്ത വെറും ടെക്സ്റ്റ് മെസ്സേജ് ആണെങ്കിൽ (അഡ്മിൻമാർക്ക് ബാധകമല്ല)
  else if (msg.text && !isAdmin) {
    try {
      // വന്ന മെസ്സേജ് അപ്പോൾ തന്നെ ഡിലീറ്റ് ചെയ്യുന്നു
      await bot.deleteMessage(chatId, msg.message_id);

      // മെൻഷൻ ചെയ്തുള്ള വാണിംഗ് മെസ്സേജ് അയക്കുന്നു
      const warningMsg = await bot.sendMessage(
        chatId, 
        `⚠️ [${firstName}](tg://user?id=${userId}), ഇത് ലിങ്കുകളും മീഡിയകളും പങ്കുവെക്കാനുള്ള ഗ്രൂപ്പ് മാത്രമാണ്! സാധാരണ മെസ്സേജുകൾ അനുവദിക്കില്ല.`, 
        { parse_mode: "Markdown" }
      );

      // വാണിംഗ് മെസ്സേജ് കൃത്യം 10 സെക്കൻഡിൽ ഡിലീറ്റ് ചെയ്യുന്നു
      setTimeout(async () => {
        try { await bot.deleteMessage(chatId, warningMsg.message_id); } catch (err) {}
      }, 10000);

    } catch (e) {
      console.log("Error handling non-link text message:", e.message);
    }
  } 
  
  // 4. അഡ്മിൻമാർ അയക്കുന്ന സാധാരണ ടെക്സ്റ്റ് മെസ്സേജുകൾ 15 മിനിറ്റിന് ശേഷം ഡിലീറ്റ് ചെയ്യുന്നു
  else if (msg.text && isAdmin) {
    setTimeout(async () => {
      try { await bot.deleteMessage(chatId, msg.message_id); } catch (e) {}
    }, DELETE_TIMEOUT);
  }
});