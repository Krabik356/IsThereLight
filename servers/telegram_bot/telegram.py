import asyncio
import os
import sys
import selectors
from dotenv import load_dotenv
from telebot.async_telebot import AsyncTeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import database

load_dotenv()
token = os.getenv("BOT_TOKEN")

bot = AsyncTeleBot(token)
pool = database.get_pool(2, 10, os.getenv("DB_NAME"), os.getenv("DB_USER"), int(os.getenv("DB_PASSWORD")))


def greetings_markup():
    markup = InlineKeyboardMarkup()
    adjust = InlineKeyboardButton(text="Налаштувати ⚙️", callback_data="adjust")
    join = InlineKeyboardButton(text="Під'єднатись 🔌", callback_data="join")

    markup.add(adjust, join)
    return markup


@bot.message_handler(commands=["start"])
async def start(message):
    await bot.send_message(message.chat.id, text=f'*Привіт, я Світлячок* 🌞\n\nЯ *створений* щоб ти завжди міг *знати* чи є насправді у тебе в дома *світло* чи ні. 🕯️\n\nТи хочеш *налаштувати* детектор чи *під\'єднатись* до вже працюючого? 🔌', parse_mode="Markdown", reply_markup=greetings_markup())

@bot.message_handler(commands=["pass"])
async def start(message):
    pass

@bot.callback_query_handler()
async def calls(call):
    await bot.answer_callback_query(call.id)
    call_data = call.data

    if call_data == "adjust":
        async with pool.connection() as conn:
            await database.add_user(conn, call.from_user.id, call.message.chat.id)
            await database.change_status(conn, call.from_user.id, "detector_coding")
            await bot.send_message(call.message.chat.id, text=f'*Налаштування* ⚙️\n\nНадішли *код* написаний на *детекторі* і придуманий тобою пароль (до 50 символів) ⌨️\n\n**Пиши у форматі: "код:пароль"**', parse_mode="Markdown")

    elif call_data == "join":
        async with pool.connection() as conn:
            await database.add_user(conn, call.from_user.id, call.message.chat.id)
            await database.change_status(conn, call.from_user.id, "detector_joining")
            await bot.send_message(call.message.chat.id, text=f'*Під\'єднання* 🔌\n\nНадішли *код* детектора та *пароль* яким його *закодовано* ⌨️\n\n**Пиши у форматі: "код:пароль"**',parse_mode="Markdown")

def get_and_validate_detectors_data(message):
    try:
        detectors_id, password = message.split(":")
        if len(detectors_id) > 30 or len(password) > 50:
            return None
        return {"id": detectors_id,"password": password}
    except:
        return None

@bot.message_handler()
async def messages(message):
    async with pool.connection() as conn:
        status = await database.get_status(conn, message.from_user.id)

        if status == "detector_coding":
            data = get_and_validate_detectors_data(message.text)
            if data == None:
                await bot.reply_to(message, text="*Помилка ⚠️*\n\n*Введені* вами дані *некоректн*і! ⌨️", parse_mode="Markdown")
                return

            is_detector_free = await database.is_detector_free(conn, data["id"])
            if not is_detector_free:
                await bot.reply_to(message, text="*Помилка ⚠️*\n\nТакого детектору *не існує* або він вже *закодований* ⌨️...", parse_mode="Markdown")
                return

            async with conn.transaction():
                await database.detector_coding(conn, data["id"], message.from_user.id, data["password"])
                is_ok = await database.detector_user_relation(conn, data["id"], message.from_user.id, data["password"])
                await database.change_status(conn, message.from_user.id, "work")
                if not is_ok:
                    await bot.send_message(message.chat.id, text=f'*Помилка ⚠️*\n\nЗверніться в *тех-підтримку* 📲...', parse_mode="Markdown")
                    return

            await bot.send_message(message.chat.id, text=f'*Чудово* 🥳\n\nВи успішно *зареєстрували* детектор! *Підключіть* його до електромережі і *відстежуйте* наявність світла в будинку в *реальному часі*. 🕛\n\n**Не забудьте записати пароль. 📓**', parse_mode="Markdown")

        elif status == "detector_joining":
            data = get_and_validate_detectors_data(message.text)
            if data == None:
                await bot.reply_to(message, text="*Помилка ⚠️*\n\n*Введені* вами дані *некоректн*і! ⌨️",parse_mode="Markdown")
                return

            is_correct = await database.is_detector_correct(conn, data["id"], data["password"])
            if not is_correct:
                await bot.send_message(message.chat.id, text=f'*Помилка ⚠️*\n\nТакого детектора *не існує* або пароль *не правильний* 📲...', parse_mode="Markdown")
                return

            async with conn.transaction():
                is_ok = await database.detector_user_relation(conn, data["id"], message.from_user.id, data["password"])
                await database.change_status(conn, message.from_user.id, "work")
                if not is_ok:
                    await bot.send_message(message.chat.id, text=f'*Помилка ⚠️*\n\nЗверніться в *тех-підтримку* 📲...', parse_mode="Markdown")
                    return

            await bot.send_message(message.chat.id, text=f'*Чудово* 🥳\n\nВи успішно підключились до детектора! Тепер ви *відстежуєте* наявність світла в *реальному часі*.', parse_mode="Markdown")


async def main():
    await pool.open()
    await bot.polling(non_stop=True)
    await pool.close()

if sys.platform == "win32":
        def selector_loop_factory():
            return asyncio.SelectorEventLoop(selectors.SelectSelector())

        asyncio.run(main(), loop_factory=selector_loop_factory)
asyncio.run(main())