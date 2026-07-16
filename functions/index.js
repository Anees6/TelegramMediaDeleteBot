const TelegramBot = require("node-telegram-bot-api");

// നിങ്ങളുടെ ബോട്ട് ടോക്കൺ
const token = "8673412670:AAFW2QTdkHH_LxecEzJNE-SkflJZe1X8Y0g";
const bot = new TelegramBot(token, { polling: true });

// ഡിഫോൾട്ട് ഡിലീറ്റ് സമയം 15 മിനിറ്റ് ആയി സെറ്റ് ചെയ്യുന്നു (മില്ലിസെക്കൻഡിൽ)
let deleteTimeout = 15 * 60 * 1000; 

console.log("Bot is running...");

// ബോട്ട് സ്റ്റാർട്ട് ചെയ്യുമ്പോൾ കാണിക്കേണ്ടത്
bot.onText(/\/start/, (msg) => {
  bot.sendMessage(
    msg.chat.id, 
    "ഹലോ! ഞാൻ റെഡിയാണ്. ഗ്രൂപ്പുകളിൽ വരുന്ന മീഡിയ ഫയലുകൾ ഞാൻ സ്വയം ഡിലീറ്റ് ചെയ്തോളാം.\n\n⏱️ സമയം മാറ്റാൻ അഡ്മിൻമാർക്ക് /m5, /m10, /m15 കമാൻഡുകൾ ഉപയോഗിക്കാം."
  );
});

// സമയം മാറ്റാനുള്ള കമാൻഡ് ഫങ്ഷൻ (/m5, /m10, /m15 മുതലായവ)
bot.onText(/\/m(\d+)/, async (msg, match) => {
  const chatId = msg.chat.id;
  const userId = msg.from.id;
  const minutes = parseInt(match[1]); // യൂസർ ടൈപ്പ് ചെയ്ത മിനിറ്റ് എടുക്കുന്നു

  // ഗ്രൂപ്പിൽ ആണോ എന്ന് നോക്കുന്നു
  if (msg.chat.type === "private") {
    return bot.sendMessage(chatId, "ഈ കമാൻഡ് ഗ്രൂപ്പുകളിൽ മാത്രമേ വർക്ക് ആകുകയുള്ളൂ.");
  }

  try {
    // കമാൻഡ് അയച്ച ആൾ ഗ്രൂപ്പിലെ അഡ്മിൻ ആണോ എന്ന് പരിശോധിക്കുന്നു
    const chatMember = await bot.getChatMember(chatId, userId);
    if (chatMember.status !== "administrator" && chatMember.status !== "creator") {
      return bot.sendMessage(chatId, "❌ ക്ഷമിക്കണം, ഒരു ഗ്രൂപ്പ് അഡ്മിന് മാത്രമേ സമയം മാറ്റാൻ സാധിക്കൂ.");
    }

    // പുതിയ സമയം മില്ലിസെക്കൻഡിലേക്ക് മാറ്റുന്നു
    deleteTimeout = minutes * 60 * 1000;
    
    bot.sendMessage(chatId, `⏱️ ഇനി മുതൽ മീഡിയ ഫയലുകൾ **${minutes} മിനിറ്റിന്** ശേഷം ഡിലീറ്റ് ചെയ്യപ്പെടും.`, { parse_mode: "Markdown" });
  } catch (e) {
    console.log("Error changing time:", e.message);
  }
});

// മീഡിയ ഫയലുകൾ ഡിലീറ്റ് ചെയ്യാനുള്ള ഫങ്ഷൻ
bot.on("message", async (msg) => {
  // കമാൻഡുകൾ ആണെങ്കിൽ ഈ ഫങ്ഷൻ ഒഴിവാക്കും
  if (msg.text && (msg.text === "/start" || msg.text.startsWith("/m"))) return;

  const isMedia =
    msg.photo ||
    msg.video ||
    msg.document ||
    msg.audio ||
    msg.voice ||
    msg.sticker ||
    msg.animation ||
    msg.video_note;

  if (isMedia) {
    // നിലവിലുള്ള 'deleteTimeout' സമയത്തിന് ശേഷം ഡിലീറ്റ് ചെയ്യുന്നു
    setTimeout(async () => {
      try {
        await bot.deleteMessage(msg.chat.id, msg.message_id);
        console.log("Message deleted successfully");
      } catch (e) {
        console.log("Error deleting message:", e.message);
      }
    }, deleteTimeout);
  }
});