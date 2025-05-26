from pyrogram import Client, filters
from pyrogram.errors import SessionPasswordNeeded
import asyncio

API_ID = 24369670        # Your API ID
API_HASH = "1d9a1f3aefe6e65bcfa51a35ba103735"  # Your API Hash
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # Your Telegram Bot Token

bot = Client("bot", bot_token=BOT_TOKEN)

@bot.on_message(filters.command("start"))
async def start(_, message):
    await message.reply("Hi! Send /gen to generate your Pyrogram string session.")

@bot.on_message(filters.command("gen"))
async def generate_string(_, message):
    await message.reply("Send me your phone number in international format (e.g. +1234567890):")

    try:
        phone_msg = await bot.listen(message.chat.id, filters=filters.text, timeout=120)
    except asyncio.TimeoutError:
        return await message.reply("Timeout! Please send /gen again.")

    phone = phone_msg.text.strip()

    session = None

    async with Client(":memory:", api_id=API_ID, api_hash=API_HASH) as user_client:
        try:
            await user_client.send_code(phone)
            await message.reply("Code sent! Please send me the login code you received:")

            code_msg = await bot.listen(message.chat.id, filters=filters.text, timeout=120)
            code = code_msg.text.strip()

            try:
                await user_client.sign_in(phone, code)
            except SessionPasswordNeeded:
                await message.reply("Two-step verification enabled! Send me your password:")
                password_msg = await bot.listen(message.chat.id, filters=filters.text, timeout=120)
                password = password_msg.text.strip()
                await user_client.check_password(password)

            session = user_client.export_session_string()

            await message.reply(f"Your Pyrogram String Session:\n\n`{session}`", parse_mode="markdown")

        except Exception as e:
            await message.reply(f"Error: {e}")

bot.run()
