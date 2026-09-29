```
`import asyncio
import os
import re
from collections import defaultdict
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ChatType
from groq import AsyncGroq

# Чтение ключей из переменных окружения хостинга
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not BOT_TOKEN or not GROQ_API_KEY:
    raise ValueError("ОШИБКА: Задай BOT_TOKEN и GROQ_API_KEY в настройках сервера!")

BAD_WORDS = ["спам", "скам", "дурак", "лох", "мат1", "мат2"]

SYSTEM_PROMPT = (
    "Ты — строгая альтушка, но справедливый и остроумный модератор чата. "
    "Твоя цель — следить за порядком, отвечать на вопросы участников и пресекать спам. "
    "Твои ответы должны быть короткими и подкалывать. Ты молодая красивая девушка."
)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
groq_client = AsyncGroq(api_key=GROQ_API_KEY)

user_memory = defaultdict(list)
URL_REGEX = re.compile(r"(https?://\S+|t\.me/\S+|www\.\S+)", re.IGNORECASE)


async def get_ai_reply(user_id: int, user_text: str) -> str:
    history = user_memory[user_id]
    history.append({"role": "user", "content": user_text})

    if len(history) > 10:
        history = history[-10:]
        user_memory[user_id] = history

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history

    try:
        chat_completion = await groq_client.chat.completions.create(
            messages=messages,
            model="llama-3.1-8b-instant",
            max_tokens=150,
            temperature=0.8,
        )
        reply = chat_completion.choices[0].message.content
        history.append({"role": "assistant", "content": reply})
        return reply
    except Exception as e:
        return f"Кринж, у меня сеть упала: {e}"


@dp.message(F.text)
async def handle_messages(message: types.Message):
    if message.from_user.is_bot:
        return

    text = message.text.lower()
    user_id = message.from_user.id
    name = message.from_user.first_name

    # Удаление ссылок
    if URL_REGEX.search(message.text):
        try:
            await message.delete()
            await message.answer(f"{name}, ссылки сюда не кидай, бан близко.")
        except Exception:
            pass
        return

    # Удаление мата
    for bad_word in BAD_WORDS:
        if bad_word in text:
            try:
                await message.delete()
                await message.answer(f"{name}, рот помой, потом пиши.")
            except Exception:
                pass
            return

    # Ответ на 'помощь', упоминание или ЛС
    bot_info = await bot.get_me()
    is_mentioned = f"@{bot_info.username.lower()}" in text
    is_help = "помощь" in text
    is_private = message.chat.type == ChatType.PRIVATE

    if is_mentioned or is_help or is_private:
        clean_text = message.text.replace(f"@{bot_info.username}", "").strip()
        if not clean_text:
            clean_text = "Че надо?"

        await bot.send_chat_action(chat_id=message.chat.id, action="typing")
        reply = await get_ai_reply(user_id, clean_text)
        await message.reply(reply)


async def main():
    print("Бот успешно запущен в облаке!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())`
```
