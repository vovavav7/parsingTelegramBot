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

import parsing_mobile_de
import parsing_marktplaats_nl
import parsing_autoscout24_nl


API_TOKEN = os.getenv("botToken")
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Шлях до файлу, де будемо зберігати налаштування користувачів та таймер
settings_file = "user_settings.json"

def get_cars_data(url, user_id):

    with open(settings_file, 'r') as f:
        user_settings = json.load(f)

    if user_settings[user_id]["cars"]:
        user_settings[user_id]["cars"] = []

    new_cars = []

    if url.startswith("https://suchen.mobile.de"): cars = parsing_mobile_de.get_website_data(url)
    elif url.startswith("https://www.marktplaats.nl"): cars = parsing_marktplaats_nl.get_website_data(url)
    elif url.startswith("https://www.autoscout24.nl"): cars = parsing_autoscout24_nl.get_website_data(url)

    for car in cars:
        if url.startswith("https://suchen.mobile.de"): car_data = parsing_mobile_de.get_info(url)
        elif url.startswith("https://www.marktplaats.nl"): car_data = parsing_marktplaats_nl.get_info(url)
        elif url.startswith("https://www.autoscout24.nl"): car_data = parsing_autoscout24_nl.get_info(url)

        if car_data in user_settings[user_id]["cars"]:
             continue
        else:
            new_cars.append(car_data)
            user_settings[user_id]["cars"].append(car_data)
    
    with open(settings_file, 'w') as f:
        json.dump(user_settings, f, indent=4)
    
    return new_cars

async def parse_website(url, user_id):
    new_cars = get_cars_data(url, user_id)

    for car in new_cars:
        name, price, kilometerage, year, acu, link = [car[i] for i in car]
        content = f"Ім'я: {name}\nЦіна: {price}\nПробіг: {kilometerage}\nРік: {year}\nАкулумяток: {acu}\nСилка: {link}"
    await bot.send_message(user_id, content)

# Парсинг сайтів для кожного користувача
async def parse_websites(user_id):
    try:
        with open(settings_file, 'r') as f:
            user_settings = json.load(f)

        urls = user_settings[str(user_id)]['urls']

        for url in urls:
            parse_website(url, user_id)
    except Exception as e:
        print(f"Помилка при парсингу для користувача {user_id}: {e}")


# Функція для виконання парсингу
async def job(user_id):
    print("Job: " + user_id)
    with open(settings_file, 'r') as f:
        user_settings = json.load(f)

    if user_settings[user_id]["interval"] != 0:
        await parse_websites(user_id)

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
                         "Для налаштування інтервалу парсингу, введіть /set_timer <час_в_хвилинах>.")

@dp.message(Command("replace", "Replace"))
async def replace(message: Message):
    with open(settings_file, 'r') as f:
        user_settings = json.load(f)
    
    user_id = str(message.from_user.id)
    if user_id not in user_settings:
        user_settings[user_id] = {
            "urls": [],
            "interval": 0
        }
    
    url = message.text.split(" ")[2]
    index = message.text.split(" ")[1]

    user_settings[user_id]["urls"][index] = url

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
            "interval": 0
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
            "interval": 0
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
            "interval": 0
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
            user_settings[str(user_id)] = {"urls": []}

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
