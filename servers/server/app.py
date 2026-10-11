import asyncio
import os
from dotenv import load_dotenv
from telebot.async_telebot import AsyncTeleBot

load_dotenv()
token = os.getenv("BOT_TOKEN")

bot = AsyncTeleBot(token)

async def main():
    await bot.polling(non_stop=True)

asyncio.run(main())