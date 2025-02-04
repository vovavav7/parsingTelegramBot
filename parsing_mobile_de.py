import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


settings_file = "user_settings.json"

def get_website_data(url, user_id):
    with open(settings_file, 'r') as f:
        user_settings = json.load(f)

    options = Options()
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    driver = webdriver.Chrome(options=options)

    driver.get(url)

    # Використовуємо явне очікування, щоб дочекатися елемента
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="root"]/div/main/div[6]/div[2]/article[1]'))
        )
    except Exception as e:
        print(f"Помилка при завантаженні сторінки: {e}")
        driver.quit()
        return []

    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    time.sleep(5)

    conteiner = driver.find_element(By.XPATH, '//*[@id="root"]/div/main/div[6]/div[2]')
    cars = conteiner.find_elements(By.TAG_NAME, "a")

    new_cars = []

    for car in cars:
        try: 
            price = car.find_element(By.CSS_SELECTOR, '[data-testid="price-label"]').text
        except: 
            price = "Ціна не знайдена"
        try: 
            name = car.find_element(By.TAG_NAME, "h2").text
        except: 
            name = "Ім'я не знайдено"
        try: 
            car_info = car.find_element(By.CSS_SELECTOR, '[data-testid="listing-details-attributes"]').text
        except: 
            car_info = "Інформацію про машину не знайдено"

        try: 
            kilometerage = car_info.split(" • ")[2]
        except: 
            kilometerage = "Не знайдено"
        try: 
            year = car_info.split(" • ")[1]
        except: 
            year = "Не знайдено"
        try: 
            acu = car_info.split(" • ")[3]
        except: 
            acu = "Не знайдено"

        link = car.get_attribute('href')

        car = [name, price, kilometerage, year, acu, link]
        
        for link in list(user_settings[str(user_id)]["cars"]):
            if link[-1].split("&")[0] == car[-1].split("&")[0]:
                break
        else:
           new_cars.append(car)
           user_settings[str(user_id)]['cars'].append(car)
        
           with open(settings_file, 'w') as f:
               json.dump(user_settings, f, indent=4)
    
    driver.quit()
    return new_cars