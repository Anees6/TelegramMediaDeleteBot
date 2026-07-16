const functions = require("firebase-functions");
const admin = require("firebase-admin");
const TelegramBot = require("node-telegram-bot-api");

admin.initializeApp();

// നിങ്ങളുടെ ബോട്ട് ടോക്കൺ ഇവിടെ സെറ്റ് ചെയ്തിട്ടുണ്ട്
const token = "8673412670:AAFW2QTdkHH_LxecEzJNE-SkflJZe1X8Y0g";
const bot = new TelegramBot(token);

// ഫങ്ഷൻ ടൈംഔട്ട് 16 മിനിറ്റാക്കി മാറ്റുന്നു (15 മിനിറ്റ് ടൈമറിന് ശേഷം ഡിലീറ്റ് ചെയ്യാൻ സമയം വേണം)
exports.telegramWebhook = functions.runWith({ timeoutSeconds: 960 }).https.onRequest(async (req, res) => {
  try {
    const update = req.body;

    if (update.message) {
      const msg = update.message;

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
        // 15 മിനിറ്റ് കഴിഞ്ഞ ശേഷം മാത്രം റെസ്പോൺസ് അയക്കുകയും ഡിലീറ്റ് ചെയ്യുകയും ചെയ്യുന്നു
        setTimeout(async () => {
          try {
            await bot.deleteMessage(msg.chat.id, msg.message_id);
            console.log("Message deleted successfully");
          } catch (e) {
            console.log("Error deleting message:", e);
          }
          // ഡിലീറ്റ് ചെയ്ത ശേഷം മാത്രം ഫങ്ഷൻ അവസാനിപ്പിക്കുന്നു
          res.status(200).send("OK");
        }, 15 * 60 * 1000); // 15 മിനിറ്റ്
        
        return; // ഇവിടെ വെച്ച് ഫങ്ഷൻ താഴേക്ക് പോകുന്നത് തടയുന്നു
      }
    }

    // മീഡിയ അല്ലെങ്കിൽ ഉടനെ തന്നെ OK അയക്കുന്നു
    res.status(200).send("OK");
  } catch (err) {
    console.log(err);
    res.status(500).send("Error");
  }
});