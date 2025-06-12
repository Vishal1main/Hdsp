const express = require("express");
const TelegramBot = require("node-telegram-bot-api");
const { MongoClient } = require("mongodb");

// 🔐 CONFIGURATION
const BOT_TOKEN = "7861502352:AAFcS7xZk2NvN7eJ3jcPm_HyYh74my8vRyU";
const MONGO_URI = "mongodb+srv://drozmarizabel991hull:Xh89XLrFTYOPgupl@cluster0.x8qoe.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0";
const CHANNEL_ID = -1002178270630;
const PORT = process.env.PORT || 3000;
const URL = "https://hdsp.onrender.com/"; // 🔁 Your Render/webhook domain

// 🔗 MongoDB connection
const mongo = new MongoClient(MONGO_URI);
let db;
(async () => {
  await mongo.connect();
  db = mongo.db("premium_bot");
  console.log("✅ MongoDB connected");
})();

// ⚙️ Webhook mode setup
const app = express();
app.use(express.json());

const bot = new TelegramBot(BOT_TOKEN);
bot.setWebHook(`${URL}/bot${BOT_TOKEN}`);

app.post(`/bot${BOT_TOKEN}`, (req, res) => {
  bot.processUpdate(req.body);
  res.sendStatus(200);
});

// 🧾 Command: /addpremium
bot.onText(/\/addpremium (@\w+|\d+) (\d+)/, async (msg, match) => {
  const chatId = msg.chat.id;
  const user = match[1];
  const days = parseInt(match[2]);
  const expireDate = Math.floor(Date.now() / 1000) + days * 86400;

  try {
    const invite = await bot.createChatInviteLink(CHANNEL_ID, {
      expire_date: expireDate,
      member_limit: 1
    });

    await db.collection("premium_users").insertOne({
      user,
      added_by: msg.from.id,
      invite_link: invite.invite_link,
      added_on: new Date(),
      expire_at: new Date(Date.now() + days * 86400 * 1000)
    });

    bot.sendMessage(chatId, `✅ Premium access granted to ${user} for ${days} days.\n🔗 Invite: ${invite.invite_link}`);
  } catch (err) {
    console.error("❌ Error:", err.message);
    bot.sendMessage(chatId, "❌ Could not add premium user. Ensure bot is admin and channel is private.");
  }
});

// 🕓 Auto-removal of expired users
setInterval(async () => {
  const now = new Date();
  const expiredUsers = await db.collection("premium_users").find({ expire_at: { $lte: now } }).toArray();

  for (const user of expiredUsers) {
    try {
      const id = user.user.startsWith("@") ? user.user : parseInt(user.user);
      await bot.banChatMember(CHANNEL_ID, id);
      await bot.unbanChatMember(CHANNEL_ID, id);
      await db.collection("premium_users").deleteOne({ _id: user._id });
      console.log(`🚫 Removed expired user: ${user.user}`);
    } catch (err) {
      console.error(`⚠️ Failed to remove ${user.user}:`, err.message);
    }
  }
}, 60 * 60 * 1000); // every 1 hour

// 🌐 Start Express server
app.listen(PORT, () => {
  console.log(`🌐 Webhook server running on port ${PORT}`);
});
