const TelegramBot = require("node-telegram-bot-api");

// നിങ്ങളുടെ ബോട്ട് ടോക്കൺ
const token = "8673412670:AAFW2QTdkHH_LxecEzJNE-SkflJZe1X8Y0g";
const bot = new TelegramBot(token, { polling: true });

console.log("Bot is running...");

// ബോട്ട് സ്റ്റാർട്ട് ചെയ്യുമ്പോൾ കാണിക്കേണ്ടത്
bot.onText(/\/start/, (msg) => {
  bot.sendMessage(
    msg.chat.id, 
    "ഹലോ! ഞാൻ റെഡിയാണ്. ഈ ഗ്രൂപ്പിൽ വരുന്ന മീഡിയ ഫയലുകൾ (ഫോട്ടോ, വീഡിയോ മുതലായവ) 15 മിനിറ്റിന് ശേഷം ഞാൻ സ്വയം ഡിലീറ്റ് ചെയ്തോളാം."
  );
});

// മീഡിയ ഫയലുകൾ ഡിലീറ്റ് ചെയ്യാനുള്ള ഫങ്ഷൻ
bot.on("message", async (msg) => {
  // സ്റ്റാർട്ട് കമാൻഡ് ആണെങ്കിൽ ഇത് ഒഴിവാക്കും
  if (msg.text === "/start") return;

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
    console.log(`Media detected. Will delete in 15 minutes. Message ID: ${msg.message_id}`);
    
    // 15 മിനിറ്റ് (15 * 60 * 1000 മില്ലിസെക്കൻഡ്) കഴിഞ്ഞാൽ ഡിലീറ്റ് ചെയ്യും
    setTimeout(async () => {
      try {
        await bot.deleteMessage(msg.chat.id, msg.message_id);
        console.log("Message deleted successfully");
      } catch (e) {
        console.log("Error deleting message:", e.message);
      }
    }, 15 * 60 * 1000);
  }
});