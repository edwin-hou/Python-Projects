from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class Login():
    def __init__(self, driver, username=None, password=None):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)
        if username != None:
            self.username = username
            self.password = password
        else:
            file = open('data.txt', 'r')
            data = eval(file.read())
            self.username = data['username']
            self.password = data['password']

    def login(self):
        # if "google" in self.driver.current_url.lower():
        # self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[type=email]'))) # input[name=email],input[type=email]
        while True:
            try:
                email = self.driver.find_element(By.CSS_SELECTOR, 'input[type=email]')
                # print(email, self.username)
                email.click()
                email.clear()
                for i in self.username:
                    email.send_keys(i)

                if self.driver.execute_script(
                        "return document.querySelector('input[type=email]').getAttribute('data-initial-value')") == self.username:
                    # print('username entered')
                    break

            except:
                pass
        # for i in self.username:
        #     email.send_keys(i)
        # time.sleep(0.01)
        # time.sleep(2)

        email.send_keys(Keys.ENTER)
        # else:
        #     raise Exception('not valid website')

        # if "discord" in self.driver.current_url.lower():
        #     self.wait.until(EC.element_to_be_clickable(
        #         (By.CSS_SELECTOR, 'input[name=email]')))  # input[name=email],input[type=email]
        #     email = self.driver.find_element(By.CSS_SELECTOR, 'input[name=email]')
        #     for i in self.username:
        #         email.send_keys(i)
        #     # time.sleep(2)
        #     email.send_keys(Keys.ENTER)
        # # self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[type=password]')))

        while True:
            try:
                password = self.driver.find_element(By.CSS_SELECTOR, 'input[type=password]')
                password.click()
                password.clear()
                for i in self.password:
                    password.send_keys(i)
                # print(self.driver.execute_script(
                #         "return document.querySelector('input[type=password]').getAttribute('data-initial-value')"))
                if self.driver.execute_script(
                        "return document.querySelector('input[type=password]').getAttribute('data-initial-value')") == self.password:
                    # print('password entered')
                    break
            except Exception as e:
                # self.driver.save_screenshot('error.png')
                # print(e)
                pass
        while True:
            # time.sleep(0.5)
            try:
                password.send_keys(Keys.ENTER)
            except:
                break


if __name__ == '__main__':
    chrome_options = Options()
    chrome_options.add_argument("maximize")
    chrome_options.add_argument("--incognito")
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(
        'https://accounts.google.com/signin/v2/identifier?hl=en&passive=true&continue=https%3A%2F%2Fwww.google.com%2F%3Fgws_rd%3Dssl&ec=GAVAAQ&flowName=GlifWebSignIn&flowEntry=ServiceLogin')
    l = Login(driver=driver)
    l.login()
