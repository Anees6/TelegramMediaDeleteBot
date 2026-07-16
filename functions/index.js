const TelegramBot = require("node-telegram-bot-api");

// Bot Token സെറ്റ് ചെയ്യുന്നു
const token = "8673412670:AAFW2QTdkHH_LxecEzJNE-SkflJZe1X8Y0g";
const bot = new TelegramBot(token, { polling: true });

// ഡിഫോൾട്ട് ഡിലീറ്റ് സമയം 15 മിനിറ്റ് (മില്ലിസെക്കൻഡിൽ)
let deleteTimeout = 15 * 60 * 1000; 

console.log("Bot is running successfully...");

// ബോട്ട് സ്റ്റാർട്ട് ചെയ്യുമ്പോൾ കാണിക്കേണ്ടത്
bot.onText(/\/start/, (msg) => {
  bot.sendMessage(
    msg.chat.id, 
    "ഹലോ! ഞാൻ റെഡിയാണ്. ഗ്രൂപ്പുകളിൽ വരുന്ന മീഡിയ ഫയലുകളും ലിങ്കുകളും ഞാൻ നിശ്ചിത സമയത്തിന് ശേഷം ഡിലീറ്റ് ചെയ്തോളാം. വെറും ടെക്സ്റ്റ് മെസ്സേജുകൾ അയക്കുന്നവരെ ഞാൻ മ്യൂട്ട് ചെയ്യുന്നതായിരിക്കും.\n\n⏱️ സമയം മാറ്റാൻ അഡ്മിൻമാർക്ക് /m5, /m10, /m15 കമാൻഡുകൾ ഉപയോഗിക്കാം."
  );
});

// സമയം മാറ്റാനുള്ള കമാൻഡ് ഫങ്ഷൻ (/m5, /m10, /m15 മുതലായവ)
bot.onText(/\/m(\d+)/, async (msg, match) => {
  const chatId = msg.chat.id;
  const userId = msg.from.id;
  const minutes = parseInt(match[1]);

  if (msg.chat.type === "private") {
    return bot.sendMessage(chatId, "ഈ കമാൻഡ് ഗ്രൂപ്പുകളിൽ മാത്രമേ വർക്ക് ആകുകയുള്ളൂ.");
  }

  try {
    const chatMember = await bot.getChatMember(chatId, userId);
    if (chatMember.status !== "administrator" && chatMember.status !== "creator") {
      return bot.sendMessage(chatId, "❌ ക്ഷമിക്കണം, ഒരു ഗ്രൂപ്പ് അഡ്മിന് മാത്രമേ സമയം മാറ്റാൻ സാധിക്കൂ.");
    }

    deleteTimeout = minutes * 60 * 1000;
    bot.sendMessage(chatId, `⏱️ ഇനി മുതൽ മീഡിയകളും ലിങ്കുകളും **${minutes} മിനിറ്റിന്** ശേഷം ഡിലീറ്റ് ചെയ്യപ്പെടും.`, { parse_mode: "Markdown" });
  } catch (e) {
    console.log("Error changing time:", e.message);
  }
});

// മ്യൂട്ട് ചെയ്തയാളെ അൺമ്യൂട്ട് ചെയ്യാനുള്ള കമാൻഡ് (/unmute) - റിപ്ലൈ ആയി ചെയ്യണം
bot.onText(/\/unmute/, async (msg) => {
  const chatId = msg.chat.id;
  const adminId = msg.from.id;

  if (msg.chat.type === "private") return;

  try {
    // കമാൻഡ് അടിച്ചത് അഡ്മിൻ ആണോ എന്ന് നോക്കുന്നു
    const chatMember = await bot.getChatMember(chatId, adminId);
    if (chatMember.status !== "administrator" && chatMember.status !== "creator") return;

    // ഏതെങ്കിലും മെസ്സേജിന് റിപ്ലൈ ആയിട്ടാണോ കമാൻഡ് അടിച്ചത് എന്ന് നോക്കുന്നു
    if (!msg.reply_to_message) {
      return bot.sendMessage(chatId, "❌ അൺമ്യൂട്ട് ചെയ്യേണ്ട ആളുടെ മെസ്സേജിന് Reply ആയി /unmute എന്ന് ടൈപ്പ് ചെയ്യുക.");
    }

    const targetUserId = msg.reply_to_message.from.id;
    const targetName = msg.reply_to_message.from.first_name || "യൂസർ";

    // അൺമ്യൂട്ട് ചെയ്യുന്നു (മെസ്സേജ് അയക്കാനുള്ള പെർമിഷൻ തിരികെ നൽകുന്നു)
    await bot.restrictChatMember(chatId, targetUserId, {
      permissions: {
        can_send_messages: true,
        can_send_media_messages: true,
        can_send_polls: true,
        can_send_other_messages: true,
        can_add_web_page_previews: true
      }
    });

    bot.sendMessage(chatId, `✅ [${targetName}](tg://user?id=${targetUserId}) അൺമ്യൂട്ട് ചെയ്യപ്പെട്ടിരിക്കുന്നു. ഇനി മുതൽ മെസ്സേജുകൾ അയക്കാം.`, { parse_mode: "Markdown" });

  } catch (e) {
    console.log("Unmute Error:", e.message);
  }
});

// മെസ്സേജുകൾ പരിശോധിക്കാനുള്ള പ്രധാന ഫങ്ഷൻ
bot.on("message", async (msg) => {
  if (!msg.from || msg.from.is_bot) return;
  if (msg.text && (msg.text === "/start" || msg.text.startsWith("/m") || msg.text === "/unmute")) return;
  
  const chatId = msg.chat.id;
  const userId = msg.from.id;
  const firstName = msg.from.first_name || "യൂസർ";

  // അഡ്മിൻമാർ അയക്കുന്ന സാധാരണ മെസ്സേജുകൾ ഡിലീറ്റ് ചെയ്യുകയോ മ്യൂട്ട് ചെയ്യുകയോ ഇല്ല
  try {
    const chatMember = await bot.getChatMember(chatId, userId);
    if (chatMember.status === "administrator" || chatMember.status === "creator") {
      return; 
    }
  } catch (e) {
    console.log("Error checking admin status:", e.message);
  }

  // മീഡിയ ഫയലുകൾ ഉണ്ടോ എന്ന് പരിശോധിക്കുന്നു
  const isMedia =
    msg.photo ||
    msg.video ||
    msg.document ||
    msg.audio ||
    msg.voice ||
    msg.sticker ||
    msg.animation ||
    msg.video_note;

  // ലിങ്കുകൾ ഉണ്ടോ എന്ന് പരിശോധിക്കുന്നു
  let isLink = false;
  if (msg.entities) {
    isLink = msg.entities.some(entity => entity.type === "url" || entity.type === "text_link");
  }
  if (msg.text && (msg.text.includes("http://") || msg.text.includes("https://") || msg.text.includes("t.me/"))) {
    isLink = true;
  }

  // മീഡിയയോ ലിങ്കോ ആണെങ്കിൽ ടൈമർ വെച്ച് ഡിലീറ്റ് ചെയ്യുന്നു
  if (isMedia || isLink) {
    setTimeout(async () => {
      try {
        await bot.deleteMessage(chatId, msg.message_id);
        console.log("Media/Link deleted successfully");
      } catch (e) {
        console.log("Error deleting media/link:", e.message);
      }
    }, deleteTimeout);
  } 
  // വെറും ടെക്സ്റ്റ് മെസ്സേജ് (ലിങ്ക് ഇല്ലാത്തത്) ആണെങ്കിൽ ഉടൻ ഡിലീറ്റ് ചെയ്ത് മെമ്പർ മ്യൂട്ട് ചെയ്യുന്നു
  else if (msg.text) {
    try {
      // വന്ന മെസ്സേജ് ഉടൻ ഡിലീറ്റ് ചെയ്യുന്നു
      await bot.deleteMessage(chatId, msg.message_id);
      
      // യൂസറെ മ്യൂട്ട് ചെയ്യുന്നു (മെസ്സേജ് അയക്കാനുള്ള പെർമിഷൻ ബ്ലോക്ക് ചെയ്യുന്നു)
      await bot.restrictChatMember(chatId, userId, {
        permissions: {
          can_send_messages: false,
          can_send_media_messages: false,
          can_send_polls: false,
          can_send_other_messages: false,
          can_add_web_page_previews: false
        }
      });

      // മ്യൂട്ട് ചെയ്ത വിവരം ഗ്രൂപ്പിൽ അറിയിക്കുന്നു
      const warningMsg = await bot.sendMessage(
        chatId, 
        `🔒 [${firstName}](tg://user?id=${userId}), ഇത് ലിങ്കുകൾ ഇടാൻ മാത്രമുള്ള ഗ്രൂപ്പ് ആണ്. ചട്ടങ്ങൾ ലംഘിച്ചതിനാൽ നിങ്ങളെ മ്യൂട്ട് ചെയ്തിരിക്കുന്നു!`, 
        { parse_mode: "Markdown" }
      );

      // ബോട്ടിന്റെ ഈ മെസ്സേജ് 15 സെക്കൻഡിന് ശേഷം ഡിലീറ്റ് ചെയ്യുന്നു
      setTimeout(async () => {
        try {
          await bot.deleteMessage(chatId, warningMsg.message_id);
        } catch (err) {
          console.log("Error deleting warning:", err.message);
        }
      }, 15000);

    } catch (e) {
      console.log("Error handling text/mute message:", e.message);
    }
  }
});