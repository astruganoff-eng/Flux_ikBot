from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ContentType
import aiohttp
import asyncio
import os

BOT_TOKEN = os.getenv('BOT_TOKEN')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
FAL_API_KEY = os.getenv('FAL_API_KEY')
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

async def ask_deepseek(prompt):
    async with aiohttp.ClientSession() as session:
        async with session.post("https://api.deepseek.com/chat/completions",
            json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "temperature": 0.7},
            headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}"}
        ) as resp:
            data = await resp.json()
            return data['choices'][0]['message']['content']

async def generate_image(prompt):
    async with aiohttp.ClientSession() as session:
        async with session.post("https://fal.run/fal-ai/flux-pro/v1.1",
            json={"prompt": prompt, "image_size": "square_hd"},
            headers={"Authorization": f"Key {FAL_API_KEY}"}
        ) as resp:
            result = await resp.json()
            return result['images'][0]['url']

async def text_to_speech(text):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://api.elevenlabs.io/v1/text-to-speech/EXAVITQu4vr4xnSDxMaL",
            json={"text": text[:1000], "model_id": "eleven_multilingual_v2"},
            headers={"xi-api-key": ELEVENLABS_API_KEY}
        ) as resp:
            if resp.status == 200:
                return await resp.read()
    return None

@dp.message_handler(content_types=[ContentType.TEXT, ContentType.PHOTO])
async def handle_message(message: types.Message):
    await message.answer_chat_action("typing")
    user_text = message.caption or message.text or "Привет"

    response = await ask_deepseek(user_text)

    if any(word in user_text.lower() for word in ["нарисуй", "сгенерируй", "картинку", "арт", "flux"]):
        try:
            img_url = await generate_image(user_text)
            await message.answer_photo(img_url, caption=response)
        except:
            await message.answer(response)
    else:
        await message.answer(response)

    audio = await text_to_speech(response)
    if audio:
        await message.answer_voice(types.InputFile.from_bytes(audio, "answer.ogg"))

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
