import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
import aiohttp

# ================= НАСТРОЙКИ (ЗАПОЛНИТЕ ИХ!) =================
TELEGRAM_BOT_TOKEN = "ВАШ_ТЕЛЕГРАМ_БОТ_ТОКЕН"
DESTINATION_TG_CHANNEL_ID = "@ваш_канал"  # Название канала с собачкой или ID (-100...)

# Настройки Facebook
FB_PAGE_ACCESS_TOKEN = "ВАШ_TOKEN_СТРАНИЦЫ_FACEBOOK"  # Page Access Token
FB_PAGE_ID = "ID_ВАШЕЙ_СТРАНИЦЫ"                      # ID страницы Facebook
FB_GROUP_IDS = ["ID_ГРУППЫ_1", "ID_ГРУППЫ_2"]         # ID групп для рассылки (или [] если не нужны)
# ==============================================================

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()


async def post_to_facebook(text: str, photo_bytes: bytes):
    """Функция отправки фото с текстом на страницу и в группы Facebook."""
    async with aiohttp.ClientSession() as session:
        # 1. Публикация на страницу Facebook
        if FB_PAGE_ACCESS_TOKEN and FB_PAGE_ACCESS_TOKEN != "ВАШ_TOKEN_СТРАНИЦЫ_FACEBOOK":
            try:
                url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/photos"
                form = aiohttp.FormData()
                form.add_field('access_token', FB_PAGE_ACCESS_TOKEN)
                form.add_field('caption', text)
                form.add_field('source', photo_bytes, filename='image.jpg', content_type='image/jpeg')

                async with session.post(url, data=form) as resp:
                    result = await resp.json()
                    if "id" in result:
                        logging.info("Успешно опубликовано на странице Facebook!")
                    else:
                        logging.error(f"Ошибка публикации на страницу FB: {result}")
            except Exception as e:
                logging.error(f"Исключение при публикации на страницу FB: {e}")

        # 2. Рассылка по группам Facebook
        for group_id in FB_GROUP_IDS:
            if not group_id or group_id.startswith("ID_ГРУППЫ"):
                continue
            try:
                url = f"https://graph.facebook.com/v19.0/{group_id}/photos"
                form = aiohttp.FormData()
                form.add_field('access_token', FB_PAGE_ACCESS_TOKEN)
                form.add_field('caption', text)
                form.add_field('source', photo_bytes, filename='image.jpg', content_type='image/jpeg')

                async with session.post(url, data=form) as resp:
                    result = await resp.json()
                    if "id" in result:
                        logging.info(f"Успешно опубликовано в группе FB ({group_id})!")
                    else:
                        logging.error(f"Ошибка публикации в группу {group_id}: {result}")
            except Exception as e:
                logging.error(f"Исключение при публикации в группу {group_id}: {e}")


@dp.message(F.photo)
async def handle_post(message: Message):
    """Обработчик входящих сообщений с картинкой и подписью."""
    caption = message.caption or ""
    photo_file_id = message.photo[-1].file_id

    # Скачивание изображения из Telegram в оперативную память
    file_info = await bot.get_file(photo_file_id)
    photo_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_info.file_path}"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(photo_url) as resp:
            photo_bytes = await resp.read()

    # 1. Отправка в Telegram-канал
    try:
        await bot.send_photo(
            chat_id=DESTINATION_TG_CHANNEL_ID,
            photo=photo_file_id,
            caption=caption
        )
        await message.answer("✅ В Telegram-канал отправлено!")
    except Exception as e:
        await message.answer(f"❌ Ошибка отправки в Telegram: {e}")

    # 2. Отправка в Facebook (Страница + Группы)
    await post_to_facebook(text=caption, photo_bytes=photo_bytes)
    await message.answer("🌐 Рассылка в Facebook завершена (подробности в логах).")


async def main():
    print("Бот-кросспостер запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())