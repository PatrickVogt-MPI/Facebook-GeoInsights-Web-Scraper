from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import credentials
import sys
import time
        
if __name__ == "__main__":
    # Loads map download links from 'requests.txt'
    with open('requests.txt') as file:
        requests = [line.strip() for line in file]
    
    driver = webdriver.Chrome()
    
    # Automated sign-in into GeoInsights
    driver.get('https://www.facebook.com/geoinsights-portal')
    
    login_button = driver.find_element_by_xpath('/html/body/div[1]/div[2]/div[2]/a[2]')
    login_button.click()
    
    id = credentials.settings['user-id']
    pw = credentials.settings['password']
    
    id_form = driver.find_element_by_xpath('//*[@id="email"]')
    id_form.clear()
    id_form.send_keys(id)
    
    pw_form = driver.find_element_by_xpath('//*[@id="pass"]')
    pw_form.clear()
    pw_form.send_keys(pw)
    
    pw_form.send_keys(Keys.RETURN)
    
    # Waits for page to load
    try:
        element_present = EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div[2]/div/div[3]/div/div[2]/div[2]/div[1]/span[1]'))
        WebDriverWait(driver, 120).until(element_present)
    except TimeoutException:
        print('Timed out waiting for page to load')
        sys.exit(0) 
    
    # Downloads map data
    for map in requests:
        # Assembles download links for data files 
        driver.get(map)
        soup = BeautifulSoup(driver.page_source, features='html.parser')
          
        base_url = 'https://www.facebook.com'
        endpoints = [tag.get('href') for tag in soup.find_all('a', class_='_8-sf')]   
        download_links = [base_url + endpoint for endpoint in endpoints]
        
        # Downloads data files
        for download_link in download_links:
            driver.get(download_link)
        
        map_title = soup.find_all('a')[5].find_next(string=True)
        
        print(f'Successfully downloaded "{map_title}" data')