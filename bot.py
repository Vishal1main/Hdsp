const { Telegraf } = require('telegraf');
const mongoose = require('mongoose');
const express = require('express');
const bodyParser = require('body-parser');

const BOT_TOKEN = '7861502352:AAFcS7xZk2NvN7eJ3jcPm_HyYh74my8vRyU';
const MONGO_URL = 'mongodb+srv://drozmarizabel991hull:Xh89XLrFTYOPgupl@cluster0.x8qoe.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'; // Replace with your MongoDB connection string
const CHANNEL_ID = '-1002178270630';
const WEBHOOK_URL = 'https://hdsp.onrender.com/'; // Replace with your deployed domain
const PORT = process.env.PORT || 3000;

const bot = new Telegraf(BOT_TOKEN);
const app = express();
app.use(bodyParser.json());

// DB model
let User;
(async () => {
  await mongoose.connect(MONGO_URL);
  const userSchema = new mongoose.Schema({
    userId: Number,
    username: String,
    expiresAt: Date,
    inviteLink: String
  });
  User = mongoose.model('User', userSchema);
  console.log("✅ MongoDB connected");
})();

// Commands
bot.start((ctx) => {
  if (ctx.from.id.toString() !== '6987799874') return;
  ctx.reply("👋 Welcome Admin! Use /addpremium @username 30");
});

bot.command("addpremium", async (ctx) => {
  if (ctx.from.id.toString() !== '6987799874') return;

  const args = ctx.message.text.split(" ");
  if (args.length < 3) return ctx.reply("❌ Usage: /addpremium @username_or_id <days>");

  const target = args[1].replace("@", "");
  const days = parseInt(args[2]);
  if (isNaN(days)) return ctx.reply("❌ Invalid days.");

  try {
    let user;
    if (/^\d+$/.test(target)) {
      user = await bot.telegram.getChatMember(ctx.chat.id, parseInt(target));
    } else {
      user = await bot.telegram.getChatMember(ctx.chat.id, `@${target}`);
    }

    const userId = user.user.id;
    const username = user.user.username || "";

    const invite = await bot.telegram.createChatInviteLink(CHANNEL_ID, {
      expire_date: Math.floor(Date.now() / 1000) + days * 86400,
      member_limit: 1
    });

    const expiresAt = new Date(Date.now() + days * 86400 * 1000);
    await User.updateOne(
      { userId },
      { userId, username, expiresAt, inviteLink: invite.invite_link },
      { upsert: true }
    );

    ctx.reply(`✅ Premium added for @${username || userId}.\n🔗 Link (valid ${days} days):\n${invite.invite_link}`);
  } catch (err) {
    console.error("❌ Error:", err.message);
    ctx.reply("❌ Couldn't add. User must have messaged bot or be in same group.");
  }
});

// Auto-kick expired users
const checkExpiredUsers = async () => {
  const now = new Date();
  const expired = await User.find({ expiresAt: { $lt: now } });

  for (const user of expired) {
    try {
      await bot.telegram.kickChatMember(CHANNEL_ID, user.userId);
      await User.deleteOne({ userId: user.userId });
      console.log(`⛔ Removed expired user: ${user.username || user.userId}`);
    } catch (err) {
      console.log(`⚠️ Could not remove ${user.username || user.userId}:`, err.message);
    }
  }
};

setInterval(checkExpiredUsers, 60 * 60 * 1000); // every hour

// Webhook Setup
app.use(bot.webhookCallback(`/webhook`));
app.listen(PORT, async () => {
  await bot.telegram.setWebhook(`${WEBHOOK_URL}/webhook`);
  console.log(`🚀 Bot webhook active: ${WEBHOOK_URL}/webhook`);
});
