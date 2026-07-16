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
    "ഹലോ! ഞാൻ റെഡിയാണ്. ഗ്രൂപ്പുകളിൽ വരുന്ന മീഡിയ ഫയലുകളും ലിങ്കുകളും ഞാൻ നിശ്ചിത സമയത്തിന് ശേഷം ഡിലീറ്റ് ചെയ്തോളാം. വെറും ടെക്സ്റ്റ് മെസ്സേജുകൾ ഉടൻ തന്നെ ഡിലീറ്റ് ചെയ്യും.\n\n⏱️ സമയം മാറ്റാൻ അഡ്മിൻമാർക്ക് /m5, /m10, /m15 കമാൻഡുകൾ ഉപയോഗിക്കാം."
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

// മെസ്സേജുകൾ പരിശോധിക്കാനുള്ള പ്രധാന ഫങ്ഷൻ
bot.on("message", async (msg) => {
  // ബോട്ട് സ്വന്തമായി അയക്കുന്ന മെസ്സേജുകളും കമാൻഡുകളും ഒഴിവാക്കുന്നു
  if (!msg.from || msg.from.is_bot) return;
  if (msg.text && (msg.text === "/start" || msg.text.startsWith("/m"))) return;
  
  const chatId = msg.chat.id;
  const userId = msg.from.id;
  const firstName = msg.from.first_name || "യൂസർ";

  // അഡ്മിൻമാരുടെ സാധാരണ മെസ്സേജുകൾ ഡിലീറ്റ് ചെയ്യാതിരിക്കാൻ (വേണമെങ്കിൽ മാത്രം)
  try {
    const chatMember = await bot.getChatMember(chatId, userId);
    if (chatMember.status === "administrator" || chatMember.status === "creator") {
      return; // അഡ്മിൻ അയക്കുന്ന മെസ്സേജുകൾ ബോട്ട് ഡിലീറ്റ് ചെയ്യില്ല
    }
  } catch (e) {
    console.log("Error checking admin status:", e.message);
  }

  // ഫോട്ടോ, വീഡിയോ തുടങ്ങിയ മീഡിയ ഫയലുകൾ ഉണ്ടോ എന്ന് നോക്കുന്നു
  const isMedia =
    msg.photo ||
    msg.video ||
    msg.document ||
    msg.audio ||
    msg.voice ||
    msg.sticker ||
    msg.animation ||
    msg.video_note;

  // ലിങ്കുകൾ ഉണ്ടോ എന്ന് നോക്കുന്നു
  let isLink = false;
  if (msg.entities) {
    isLink = msg.entities.some(entity => entity.type === "url" || entity.type === "text_link");
  }
  if (msg.text && (msg.text.includes("http://") || msg.text.includes("https://") || msg.text.includes("t.me/"))) {
    isLink = true;
  }

  // കേസ് 1: മീഡിയയോ ലിങ്കോ ആണെങ്കിൽ ടൈമർ വെച്ച് ഡിലീറ്റ് ചെയ്യുന്നു
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
  // കേസ് 2: വെറും ടെക്സ്റ്റ് മെസ്സേജ് (ലിങ്ക് ഇല്ലാത്തത്) ആണെങ്കിൽ ഉടൻ ഡിലീറ്റ് ചെയ്ത് മെൻഷൻ ചെയ്യുന്നു
  else if (msg.text) {
    try {
      // വന്ന മെസ്സേജ് ഉടൻ ഡിലീറ്റ് ചെയ്യുന്നു
      await bot.deleteMessage(chatId, msg.message_id);
      
      // മെമ്പർക്ക് വാർണിങ് മെൻഷൻ അയക്കുന്നു
      const warningMsg = await bot.sendMessage(
        chatId, 
        `⚠️ [${firstName}](tg://user?id=${userId}), ഇത് ലിങ്കുകൾ ഇടാൻ മാത്രമുള്ള ഗ്രൂപ്പ് ആണ്. ദയവായി മറ്റ് മെസ്സേജുകൾ ഒഴിവാക്കുക.`, 
        { parse_mode: "Markdown" }
      );

      // ബോട്ട് അയച്ച വാർണിങ് മെസ്സേജ് ഗ്രൂപ്പിൽ കുന്നുകൂടാതിരിക്കാൻ 10 സെക്കൻഡിന് ശേഷം അതും ഡിലീറ്റ് ചെയ്യുന്നു
      setTimeout(async () => {
        try {
          await bot.deleteMessage(chatId, warningMsg.message_id);
        } catch (err) {
          console.log("Error deleting warning:", err.message);
        }
      }, 10000);

    } catch (e) {
      console.log("Error handling text message:", e.message);
    }
  }
});