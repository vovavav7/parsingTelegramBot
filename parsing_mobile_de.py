from selenium import webdriver
from selenium.webdriver.common.by import By
import time

driver = webdriver.Chrome()

def get_website_data(url):
    driver.get(url)
    time.sleep(3)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)
    conteiner = driver.find_element(By.XPATH, '//*[@id="root"]/div/main/div[6]/div[2]/article[1]')
    cars = conteiner.find_elements(By.TAG_NAME, "a")
    driver.quit()
    
    return cars

def get_info(car):
    try: price = car.find_element(By.CSS_SELECTOR, '[data-testid="price-label"]').text
    except: price = "Ціна не знайдена"

    try: name = car.find_element(By.TAG_NAME, "h2").text
    except: name = "Ім'я не знайдена"

    try: car_info = car.find_element(By.CSS_SELECTOR, '[data-testid="listing-details-attributes"]').text
    except: car_info = "інформацію про машину не знайдена"
    
    try: kilometerage = car_info.split(" • ")[2]
    except: kilometerage = "не знайдено"
    try: year = car_info.split(" • ")[1]
    except: year = "не знайдено"
    try: acu = car_info.split(" • ")[3]
    except: acu = "не знайдено"
    link = car.get_attribute('href')

    return name, price, kilometerage, year, acu, link