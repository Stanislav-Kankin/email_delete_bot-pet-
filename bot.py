import imaplib
import re
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import ParseMode

from config import (
    API_TOKEN, IMAP_SERVER, USERNAME, PASSWORD,
    DELETE_EMAIL_ADDRESS, DELETE_EMAIL_SUBJECT
)


# Создание бота и диспетчера
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


async def send_notification(message: str):
    await bot.send_message(
        chat_id="YOUR_CHAT_ID", text=message,
        parse_mode=ParseMode.HTML)


async def check_email():
    try:
        # Подключение к почтовому серверу
        with imaplib.IMAP4_SSL(IMAP_SERVER) as connection:
            connection.login(USERNAME, PASSWORD)
            connection.select("INBOX")

            # Поиск писем
            _, message_nums = connection.search(None, "ALL")

            # Обработка каждого письма
            for num in message_nums[0].split():
                _, raw_email = connection.fetch(num, "(RFC822)")
                email_body = raw_email[0][1]

                # Парсинг информации о письме
                email_info = re.findall(
                    r"From: .*?Subject: (.*?)\r\n\r\n(.*?)\r\n",
                    email_body.decode(), re.DOTALL)
                sender_email = email_info[0][0]
                subject = email_info[0][1]

        # Проверка адреса и темы письма и удаление, если условия выполняются
                if sender_email == DELETE_EMAIL_ADDRESS and subject == DELETE_EMAIL_SUBJECT:
                    connection.store(num, "+FLAGS", "\\Deleted")
                
                # Отправка уведомления о новом письме
                await send_notification(f"<b>Новое письмо:</b>\n<b>ОТ:</b> {sender_email}\n<b>ТЕМА:</b> {subject}")

            # Применение изменений и выход
            connection.expunge()
            connection.close()

    except Exception as e:
        print(f"Ошибка при получении и обработке писем: {e}")


@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    await message.answer("Привет! Я буду уведомлять тебя о новых письмах.")


async def scheduled(sleep_for):
    while True:
        await check_email()
        await asyncio.sleep(sleep_for)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(dp.start_polling())
    loop.create_task(scheduled(60))  # Проверять каждую минуту
    loop.run_forever()
