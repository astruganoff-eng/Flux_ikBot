import asyncio
import os
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import ContentType, InputFile

# Токены
BOT_TOKEN = os.getenv('BOT_TOKEN')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')  # Ключ от DeepSeek
FAL_API_KEY = os.getenv('FAL_API_KEY')
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

async def ask_deepseek(prompt: str, use_web_search: bool = False) -> str:
    """
    Отправляет запрос к DeepSeek API.
    
    Args:
        prompt: Текст запроса пользователя
        use_web_search: Если True, включает поиск в интернете (требует модель deepseek-chat с веб-поиском)
    
    Returns:
        Ответ от модели или текст ошибки
    """
    try:
        # Проверяем наличие ключа
        if not DEEPSEEK_API_KEY:
            return "❌ Ключ DeepSeek API не найден. Проверь переменную окружения DEEPSEEK_API_KEY в Replit Secrets."
        
        async with aiohttp.ClientSession() as session:
            # Формируем тело запроса
            request_data = {
                "model": "deepseek-chat",  # Основная модель DeepSeek
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 2000,
                "stream": False
            }
            
            # Если нужен веб-поиск (только для моделей с поддержкой)
            if use_web_search:
                request_data["web_search"] = True
            
            async with session.post(
                "https://api.deepseek.com/chat/completions",  # Официальный endpoint DeepSeek
                json=request_data,
                headers={
                    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json"
                },
                timeout=30
            ) as resp:
                # Логируем статус для отладки
                print(f"[DeepSeek API] Status: {resp.status}")
                
                if resp.status != 200:
                    # Пробуем получить детали ошибки
                    try:
                        error_data = await resp.json()
                        error_msg = error_data.get("message", "Неизвестная ошибка")
                        return f"⚠️ DeepSeek вернул ошибку {resp.status}: {error_msg}"
                    except:
                        return f"⚠️ DeepSeek вернул ошибку {resp.status} (проверь ключ или квоту)"
                
                # Парсим успешный ответ
                data = await resp.json()
                
                # Извлекаем ответ из структуры DeepSeek
                if "choices" in data and len(data["choices"]) > 0:
                    return data["choices"][0]["message"]["content"]
                else:
                    return "🤔 DeepSeek ничего не ответил (неожиданный формат ответа)"
                    
    except asyncio.TimeoutError:
        return "⏱️ Таймаут запроса к DeepSeek (более 30 секунд)"
    except Exception as e:
        return f"🔌 Ошибка связи с DeepSeek: {str(e)}"


# Flux картинка (оставляем без изменений)
async def generate_image(prompt: str) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://fal.run/fal-ai/flux-pro/v1.1",
            json={"prompt": prompt, "image_size": "square_hd"},
            headers={"Authorization": f"Key {FAL_API_KEY}"}
        ) as resp:
            result = await resp.json()
            return result['images'][0]['url']

# ElevenLabs голос (оставляем без изменений)
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

    # Определяем, нужно ли включать веб-поиск
    # (например, если пользователь спрашивает о свежих новостях)
    use_web_search = any(word in user_text.lower() for word in 
                        ["новости", "погода", "курс", "сегодня", "сейчас", "последние"])
    
    # Ответ текстом от DeepSeek
    response = await ask_deepseek(user_text, use_web_search=use_web_search)

    # Если просит картинку
    if any(word in user_text.lower() for word in 
           ["нарисуй", "сгенерируй", "картинку", "арт", "flux", "изобрази", "фото", "рисунок"]):
        try:
            img_url = await generate_image(user_text)
            await message.answer_photo(img_url, caption=response[:200])  # Обрезаем подпись
        except Exception as e:
            print(f"Ошибка генерации изображения: {e}")
            await message.answer(f"{response}\n\n🖼️ Не удалось сгенерировать изображение: {str(e)}")
    else:
        await message.answer(response)

    # Голосовое (только если ответ не слишком длинный и не ошибка)
    if response and not response.startswith(("❌", "⚠️", "⏱️", "🔌")):
        audio = await text_to_speech(response[:800])  # Обрезаем для ElevenLabs
        if audio:
            await message.answer_voice(InputFile(audio, filename="answer.ogg"))

async def main():
    print("🤖 Бот запущен с DeepSeek API!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
