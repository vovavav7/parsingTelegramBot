from selenium import webdriver
from selenium.webdriver.common.by import By
import time

def get_website_data(url):
    driver = webdriver.Chrome()
    driver.get(url)
    time.sleep(3)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)
    conteiner = driver.find_element(By.XPATH, '//*[@id="content"]/div[4]')
    cars = conteiner.find_elements(By.TAG_NAME, "a")
    driver.quit()

    return cars

def get_info(car):
    try: name = car.find_element(By.TAG_NAME, "h3").text
    except: name = "Ім'я не знайдена"

    try: price = car.find_element(By.TAG_NAME, 'span').text
    except: price = "не знайдена"

    try: kilometerage = car.find_elements(By.CLASS_NAME, 'hz-Attribute hz-Attribute--default')[1].text
    except: kilometerage = "не знайдено"

    try: year = car.find_elements(By.CLASS_NAME, 'hz-Attribute hz-Attribute--default')[0].text
    except: year = "не знайдено"

    try: link = car.get_attribute('href')
    except: link = "не знайдено"

    return name, price, kilometerage, year, "не знайдено", link