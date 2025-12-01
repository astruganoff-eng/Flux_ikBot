import asyncio
import os
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import ContentType, InputFile

# Токены
BOT_TOKEN = os.getenv('BOT_TOKEN')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
FAL_API_KEY = os.getenv('FAL_API_KEY')
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# DeepSeek — с защитой от ошибок
async def ask_deepseek(prompt: str) -> str:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.deepseek.com/chat/completions",
                json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 1000
                },
                headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}"},
                timeout=30
            ) as resp:
                if resp.status != 200:
                    return f"DeepSeek вернул ошибку {resp.status}"
                data = await resp.json()
                # Защита от странных ответов
                if "choices" in data and len(data["choices"]) > 0:
                    return data["choices"][0]["message"]["content"]
                else:
                    return "DeepSeek ничего не ответил :("
    except Exception as e:
        return f"Ошибка связи с DeepSeek: {str(e)}"

# Flux картинка
async def generate_image(prompt: str) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://fal.run/fal-ai/flux-pro/v1.1",
            json={"prompt": prompt, "image_size": "square_hd"},
            headers={"Authorization": f"Key {FAL_API_KEY}"}
        ) as resp:
            result = await resp.json()
            return result['images'][0]['url']

# ElevenLabs голос
async def text_to_speech(text: str):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://api.elevenlabs.io/v1/text-to-speech/EXAVITQu4vr4xnSDxMaL",  # Antoni
            json={"text": text[:1000], "model_id": "eleven_multilingual_v2"},
            headers={"xi-api-key": ELEVENLABS_API_KEY}
        ) as resp:
            if resp.status == 200:
                return await resp.read()
    return None

@dp.message()
async def handle_message(message: types.Message):
    user_text = message.text or message.caption or "Привет"

    # Ответ текстом
    response = await ask_deepseek(user_text)

    # Если просит картинку
    if any(word in user_text.lower() for word in ["нарисуй", "сгенерируй", "картинку", "арт", "flux", "изобрази"]):
        try:
            img_url = await generate_image(user_text)
            await message.answer_photo(img_url, caption=response)
        except:
            await message.answer(response)
    else:
        await message.answer(response)

    # Голосовое
    audio = await text_to_speech(response)
    if audio:
        await message.answer_voice(InputFile(audio, filename="answer.ogg"))

async def main():
    print("Bot started!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
