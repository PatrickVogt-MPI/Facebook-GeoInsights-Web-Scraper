from bs4 import BeautifulSoup
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import credentials
import shutil
import sys
import tempfile
import time

def clean():
    temp_dir_instance.cleanup()
    driver.close()

def create_dir(path: Path):
    try:
        Path.mkdir(path, parents=True, exist_ok=True)
    except:
        print(f'Unable to create directory "{str(path)}".')
        sys.exit(0)
        
def wait_for_files_to_be_written(path: Path, number_of_files: int):
    counter = 0
    waiting_time = 0
    timeout = 180
    while(counter != number_of_files):
        counter = 0
        if (waiting_time > timeout):
            print('Timed out waiting for files to be written to disc')
            clean()
            sys.exit(0)
        for file in path.iterdir():
            if '.csv' in file.name:
                counter += 1
                time.sleep(1)
                waiting_time += 1
        
if __name__ == "__main__":
    # Loads map download links from 'requests.txt'
    with open('requests.txt') as file:
        requests = [line.strip() for line in file]
    
    # Creates root data directory 'map data'
    storage_dir = credentials.settings['storage_dir']
    if (storage_dir):
        root_dir = Path(storage_dir).resolve() / Path('map data')
    else:
        root_dir = Path(__file__).resolve().with_name('map data')
        
    create_dir(root_dir)
    
    # Initiates webdriver with assigned temporary download directory
    temp_dir_instance = tempfile.TemporaryDirectory()
    temp_dir = Path(temp_dir_instance.name)
    
    options = webdriver.ChromeOptions()
    prefs = {'download.default_directory' : str(temp_dir)}
    options.add_experimental_option('prefs', prefs)
    
    driver = webdriver.Chrome(chrome_options=options)
    
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
        WebDriverWait(driver, 30).until(element_present)
    except TimeoutException:
        print('Timed out waiting for page to load')
        clean()
        sys.exit(0) 
    
    # Downloads and stores map data in custom directory structure
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
            
        wait_for_files_to_be_written(temp_dir, len(download_links))
                
        # Creates map directory within root data directory
        map_title = soup.find_all('a')[5].find_next(string=True)
        map_dir = root_dir / Path(map_title)
        create_dir(map_dir)
        
        # Moves downloaded files from temporary directory to map directory
        data_file_download_paths = [path for path in sorted(temp_dir.glob('*'))]
        for file in data_file_download_paths:
            try:
                (map_dir / file.name).unlink(missing_ok=False)
            except:
                pass
            shutil.move(str(file), str(map_dir))
            
        wait_for_files_to_be_written(map_dir, len(download_links))
        
        print(f'Successfully downloaded "{map_dir.name}" data')
        
    clean()