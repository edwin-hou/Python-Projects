import pyautogui
import keyboard
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
from selenium.webdriver.chrome.options import Options

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By


class TypeRacer:
    def __init__(self, driver):
        self.driver = driver
        self.driver.get('https://play.typeracer.com?rt=1309kwrg97')

    def auto_login(self):
        wait = WebDriverWait(driver, 10)
        wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'td[align="left"] a.gwt-Anchor')))
        login = self.driver.find_element_by_css_selector('td[align="left"] a.gwt-Anchor')
        login.click()
        self.driver.find_element_by_css_selector('input[name="username"]').send_keys('gudanews_com')
        self.driver.find_element_by_css_selector(
            'input[type="password"].gwt-PasswordTextBox[name="password"]').send_keys('Stopguessing1567')
        self.driver.find_element_by_css_selector(
            'input[type="password"].gwt-PasswordTextBox[name="password"]').send_keys(Keys.ENTER)
        time.sleep(0.5)

    def enter_match(self):
        wait = WebDriverWait(driver, 10)
        button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[title="Keyboard shortcut: Ctrl+Alt+K"]')))  # Ctrl+Alt+K
        button.click()

    def get_race_text(self):
        time.sleep(1)
        wait = WebDriverWait(driver, 100)
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'span[unselectable="on"]')))
        text = self.driver.find_elements_by_css_selector('span[unselectable="on"]')
        # for i in range(len(text)):
        try:
            if text[1][0] != ' ':
                ret = text[0].text + text[1].text + text[2].text
            else:
                ret = text[0].text + text[1].text + " " + text[2].text
        except:
            ret = text[0].text + text[1].text
        print(ret)
        return ret

    def send_key(self, text):
        body = self.driver.find_element_by_css_selector('input[type=text][class="txtInput"]')
        # body.send_keys(text)
        print(text)
        for i in text.split(' '):
            body.send_keys(i)
            # print(i)
            body.send_keys(' ')
            # time.sleep(0.01)

    def wait_for_match(self):
        wait = WebDriverWait(driver, 100)

        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'span[class="time"][title]')))

    def find_input(self):
        inp = self.driver.find_element_by_css_selector('input[type=text][class="txtInput"]')
        return inp


if __name__ == '__main__':
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=chrome_options)
    tr = TypeRacer(driver)
    # tr.auto_login()
    tr.enter_match()
    txt = tr.get_race_text()
    # print(txt)
    # time.sleep(1)
    tr.wait_for_match()
    tr.send_key(txt)
