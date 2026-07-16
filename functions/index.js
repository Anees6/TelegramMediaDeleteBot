const functions = require("firebase-functions");
const admin = require("firebase-admin");
const TelegramBot = require("node-telegram-bot-api");

admin.initializeApp();

const token = process.env.BOT_TOKEN;

const bot = new TelegramBot(token);

exports.telegramWebhook = functions.https.onRequest(async (req, res) => {
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
        setTimeout(async () => {
          try {
            await bot.deleteMessage(
              msg.chat.id,
              msg.message_id
            );
          } catch (e) {
            console.log(e);
          }
        }, 15 * 60 * 1000);
      }
    }

    res.status(200).send("OK");
  } catch (err) {
    console.log(err);
    res.status(500).send("Error");
  }
});