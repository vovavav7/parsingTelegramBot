from selenium import webdriver
from selenium.webdriver.common.by import By
import time

driver = webdriver.Chrome()

def get_website_data(url):
    driver.get(url)
    time.sleep(3)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)
    conteiner = driver.find_element(By.TAG_NAME, 'main')
    cars = conteiner.find_elements(By.TAG_NAME, "article")
    driver.quit()

    return cars

def get_info(car):
    try: name = car.find_element(By.TAG_NAME, "h2").text
    except: name = "Ім'я не знайдена"

    try: price = car.find_element(By.CSS_SELECTOR, '[data-testid="regular-price"]').text
    except: price = "не знайдена"

    try: kilometerage = car.find_element(By.CSS_SELECTOR, '[data-testid="VehicleDetails-mileage_road"]').text
    except: kilometerage = "не знайдено"

    try: year = car.find_element(By.CSS_SELECTOR, '[data-testid="VehicleDetails-calendar"]').text
    except: year = "не знайдено"

    try: acu = car.find_element(By.CSS_SELECTOR, '[data-testid="VehicleDetails-speedometer"]').text
    except: acu = "не знайдено"

    try: link = car.find_element(By.TAG_NAME, "a").get_attribute('href')
    except: link = "не знайдено"

    return name, price, kilometerage, year, acu, link