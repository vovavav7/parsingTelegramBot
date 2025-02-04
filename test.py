import time
import schedule
import asyncio
from selenium import webdriver
from selenium.webdriver.common.by import By
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
import json
import os
import datetime
import parsing_mobile_de
import parsing_marktplaats_nl
import parsing_autoscout24_nl
from concurrent.futures import ThreadPoolExecutor

API_TOKEN = os.getenv("botToken")
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Шлях до файлу, де будемо зберігати налаштування користувачів та таймер
settings_file = "user_settings.json"

def get_cars_data(url, user_id):
    """Синхронна функція для парсингу одного сайту."""
    with open(settings_file, 'r') as f:
        user_settings = json.load(f)

    if "cars" not in user_settings[user_id]:
        user_settings[user_id]["cars"] = []
    
    with open(settings_file, 'w') as f:
        json.dump(user_settings, f, indent=4)

    if url.startswith("https://suchen.mobile.de"):
        return parsing_mobile_de.get_website_data(url, user_id)
    elif url.startswith("https://www.marktplaats.nl"):
        return parsing_marktplaats_nl.get_website_data(url, user_id)
    elif url.startswith("https://www.autoscout24.nl"):
        return parsing_autoscout24_nl.get_website_data(url, user_id)
    
    return []

async def parse_website(user_id):
    """Асинхронно парсить всі сайти для користувача."""
    try:
        with open(settings_file, 'r') as f:
            user_settings = json.load(f)

        urls = user_settings[str(user_id)]['urls']

        loop = asyncio.get_running_loop()
        new_cars_list = []

        with ThreadPoolExecutor() as executor:
            tasks = [loop.run_in_executor(executor, get_cars_data, url, user_id) for url in urls]
            results = await asyncio.gather(*tasks)

        for new_cars in results:
            new_cars_list.extend(new_cars)

        for car in new_cars_list:
            name, price, kilometerage, year, acu, link = car
            content = f"🚗 Ім'я: {name}\n💰 Ціна: {price}\n📏 Пробіг: {kilometerage}\n📅 Рік: {year}\n⚡ Потужність: {acu}\n🔗 Силка: {link}"
            await bot.send_message(user_id, content)

    except Exception as e:
        print(f"❌ Помилка при парсингу для користувача {user_id}: {e}")


# Функція для виконання парсингу
async def job(user_id):
    with open(settings_file, 'r') as f:
        user_settings = json.load(f)

    if user_settings[user_id]["interval"] != 0:
        await parse_website(user_id)

def set_schedule(user_id, interval_minutes):
    if any(f"parse_{user_id}" in job1.tags for job1 in schedule.jobs):
        return

    job_timer = schedule.every(interval_minutes).minutes.do(lambda: asyncio.create_task(job(user_id)))
    job_timer.tag(f"parse_{user_id}")



def load_timer(user_id):
    try:
        with open(settings_file, 'r') as f:
            user_settings = json.load(f)
        return user_settings[str(user_id)]["interval"]
    except Exception as e:
        print(f"Error loading timer: {e}")
        return 0

@dp.message(Command("help", "Help"))
async def help(message: Message):
    await message.answer("я можу парсити сайти та надіслати вам результати через Telegram. "
                         "Для початку, введіть /start.\n"
                         "Для початку парсингу сайтів, введіть /parse.\n"
                         "Для зупинення парсингу сайтів, ввудіть /stop.\n"
                         "Для додавання сайтів, введіть /add <url>.\n"
                         "Для видалення сайтів, введіть /remove <номер>.\n"
                         "Для заміни сайту, ввудіть /replace <номер> <url>.\т"
                         "Для виведення списку сайтів, введіть /list.\n"
                         "Щоб побачити через скільки часу буде наступний парсинг, введіть /next_parse.\n"
                         "Для налаштування інтервалу парсингу, введіть /set_timer <час_в_секундах>.")
    

@dp.message(Command("next_parse", "Next_parse"))
async def help(message: Message):
    user_id = str(message.from_user.id)

    with open(settings_file, 'r') as f:
        user_settings = json.load(f)

    if user_id not in user_settings:
        user_settings[user_id] = {"urls": [], "interval": 0, "cars": []}

    # Отримуємо наступний час запуску парсингу
    job_time = next((job.next_run for job in schedule.jobs if f'parse_{user_id}' in job.tags), None)

    if job_time is None:
        await message.answer("Парсинг не включений.")
        return

    # Розрахунок часу до наступного парсингу
    secunde_left = (job_time - datetime.datetime.now()).total_seconds()
    formatted_time = job_time.strftime('%Y-%m-%d %H:%M:%S')  # Форматування дати

    text = f"Наступний парсинг через {int(secunde_left)} секунд ({formatted_time})."
    await message.answer(text)


@dp.message(Command("replace", "Replace"))
async def replace(message: Message):
    with open(settings_file, 'r') as f:
        user_settings = json.load(f)
    
    user_id = str(message.from_user.id)
    if user_id not in user_settings:
        user_settings[user_id] = {
            "urls": [],
            "interval": 0,
            "cars": []
        }
    
    url = message.text.split(" ")[2]
    index = message.text.split(" ")[1]
    
    try:
        user_settings[user_id]["urls"][index] = url
    except IndexError:
        await message.answer("Не вірно вказано індекс. щоб замінити сайт напишіть /replace <номер> <url_сайта>")
        return

    with open(settings_file, 'w') as f:
        json.dump(user_settings, f, indent=4)
    
    await message.answer("Сайт успішно замінено.")

@dp.message(Command("add", "Add"))
async def add(message: Message):
    with open(settings_file, 'r') as f:
        user_settings = json.load(f)
    
    user_id = str(message.from_user.id)
    if user_id not in user_settings:
        user_settings[user_id] = {
            "urls": [],
            "interval": 0,
            "cars": []
        }
    try:
        url = message.text.split(" ")[1]

        user_settings[user_id]["urls"].append(url)

        with open(settings_file, 'w') as f:
            json.dump(user_settings, f, indent=4)
        
        await message.answer("Сайт успішно додано.")
    except IndexError:
        await message.answer("Не вказано сайт для додавання. Щоб додати сайт напишіть /add <url_сайта>")

@dp.message(Command("remove", "Remove"))
async def remove(message: Message):
    with open(settings_file, 'r') as f:
        user_settings = json.load(f)
    
    user_id = str(message.from_user.id)

    if user_id not in user_settings:
        user_settings[user_id] = {
            "urls": [],
            "interval": 0,
            "cars": []
        }
    try:
        index = message.text.split(" ")[1]

        user_settings[user_id]["urls"].pop(index)

        with open(settings_file, 'w') as f:
            json.dump(user_settings, f, indent=4)
        
        await message.answer("Сайт успішно видалено.")
    except IndexError:
        await message.answer("Не вказано номер сайту для видалення. Щоб видалити сайт напишіть /remove <номер>")

# Функція обробки команд від користувача
@dp.message(Command("start"))
async def start(message: Message):
    with open(settings_file, 'r') as f:
        user_settings = json.load(f)
    if user_settings == None:
        user_settings = {}
    
    user_id = str(message.from_user.id)
    if user_id not in user_settings:
        user_settings[user_id] = {
            "urls": [],
            "interval": 0,
            "cars": []
        }
        with open(settings_file, 'w') as f:
            json.dump(user_settings, f, indent=4)

    await message.answer("Привіт! Я бот для парсингу сайтів. Напиши /help, щоб дізнатись про доступні команди.")


@dp.message(Command("list"))
async def list(message: Message):
    with open(settings_file, 'r') as f:
        user_settings = json.load(f)

    user_id = str(message.from_user.id)
    user_urls = user_settings[str(user_id)]['urls']

    await message.answer("\n".join([f"{i + 1}. {url}" for i, url in enumerate(user_urls)]))

@dp.message(Command("stop"))
async def stop(message: Message):
    user_id = str(message.from_user.id)
    if any(f"parse_{user_id}" in job1.tags for job1 in schedule.jobs):
        schedule.clear()
        await message.answer("Парсинг сайтів зупинено.")
    else:
        await message.answer("Парсинг сайтів не запущений.")

@dp.message(Command("parse", "Parse"))
async def parse(message: Message):
    print(schedule.jobs)

    with open(settings_file, 'r') as f:
        user_settings = json.load(f)

    user_id = str(message.from_user.id)
    user_urls = user_settings[str(user_id)]['urls']

    if not user_urls or user_urls == []:
        await message.answer("Немає доданих сайтів.\nДля додавання сайтів, введіть /add <url>.")
        return
    
    if any(f"parse_{user_id}" in job.tags for job in schedule.jobs):
        await message.answer("Парсинг сайтів вже запущений.\nЩоб зупигти його напишіть /stop")
        return
    
    if user_settings[user_id]["interval"] <= 0:
        await message.answer("Ви не встановили інтервал.\nЩоб встановити інтервал використовуйте команду /set_timer <час_в_мінуьах>")
        return

    await message.answer("Парсинг сайтів запущено.")

    set_schedule(user_id, user_settings[user_id]["interval"])

@dp.message(Command("set_timer"))
async def set_timer(message: Message):
    user_id = str(message.from_user.id)
    try:
        new_timer = int(message.text.split(" ")[-1])

    except ValueError:
        await message.answer("Будь ласка, введіть ціле число")
        return
    
    except IndexError:
        await message.answer("Не вказано час для зміни таймера. Щоб змінити таймер напишіть /set_timer <час_в_хвилинах>.")
        return
    
    try:
        if new_timer < 1:
            await message.answer("Будь ласка, введіть коректне значення таймера (в хвилинах).")
            return

        with open(settings_file, 'r') as f:
            user_settings = json.load(f)

        if str(user_id) not in user_settings:
            user_settings[str(user_id)] = {"urls": [], "interval": 0, "cars": []}

        user_settings[str(user_id)]["interval"] = new_timer

        with open(settings_file, 'w') as f:
            json.dump(user_settings, f, indent=4)

        # Оновлення планувальника
        set_schedule(user_id, new_timer)
        if new_timer == 1:
            await message.answer(f"Таймер успішно змінено на {new_timer} хвилина.")
        else:
            await message.answer(f"Таймер успішно змінено на {new_timer} хвилин.")
    except ValueError:
        await message.answer("Будь ласка, введіть коректне число для таймера (в хвилинах).")

async def scheduler():
    while True:
        schedule.run_pending()
        await asyncio.sleep(1)

# Запуск бота
async def main():
    # Стартуємо обробку повідомлень
    await dp.start_polling(bot)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(scheduler())  # Запуск планувальника в окремому потоці
    loop.run_until_complete(main())  # Запуск бота
