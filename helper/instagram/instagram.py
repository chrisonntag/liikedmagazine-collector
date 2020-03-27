import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from settings import settings
from .endpoints import *


class InstagramBot:
    def __init__(self, username: str, password: str, user_agent: str):
        self.username = username
        self.password = password

        self.browser_profile = webdriver.ChromeOptions()
        self.browser_profile.add_argument('--user-agent=' + user_agent)
        self.browser_profile.add_experimental_option('prefs', {'intl.accept_languages': 'en,en_US'})
        self.browser_profile.add_experimental_option('mobileEmulation', {"deviceName": "Pixel 2"})
        self.browser = webdriver.Chrome(chrome_options=self.browser_profile)

    def login(self):
        self.browser.get(LOGIN)
        time.sleep(2)

        username_input = self.browser.find_elements_by_css_selector('form input')[0]
        password_input = self.browser.find_elements_by_css_selector('form input')[1]

        username_input.send_keys(self.username)
        password_input.send_keys(self.password)
        password_input.send_keys(Keys.ENTER)
        time.sleep(3)

    def follow(self, username: str):
        self.browser.get(USER % username)
        time.sleep(1)

        follow_button = self.browser.find_element_by_css_selector('main header button')
        if follow_button.text != 'Following':
            follow_button.click()
        else:
            print("You are already following this user")

    def unfollow(self, username: str):
        self.browser.get(USER % username)
        time.sleep(1)

        follow_button = self.browser.find_element_by_css_selector('main header button')
        if follow_button.text == 'Following':
            follow_button.click()
            time.sleep(2)
            confirm_button = self.browser.find_element_by_xpath('//button[text() = "Unfollow"]')
            confirm_button.click()
        else:
            print("You are not following this user")

    def get_user_followers(self, username: str, num: int):
        self.browser.get(USER % username)
        time.sleep(1)

        followers_link = self.browser.find_element_by_css_selector('ul li a')
        followers_link.click()
        time.sleep(2)
        followers_list = self.browser.find_element_by_css_selector('div[role=\'dialog\'] ul')
        number_of_followers_in_list = len(followers_list.find_elements_by_css_selector('li'))

        followers_list.click()
        action_chain = webdriver.ActionChains(self.browser)
        while number_of_followers_in_list < num:
            action_chain.key_down(Keys.SPACE).key_up(Keys.SPACE).perform()
            time.sleep(0.2)
            action_chain.key_down(Keys.SPACE).key_up(Keys.SPACE).perform()
            number_of_followers_in_list = len(followers_list.find_elements_by_css_selector('li'))
            time.sleep(0.8)
            followers_list.click()

        followers = []
        for user in followers_list.find_elements_by_css_selector('li'):
            user_link = user.find_element_by_css_selector('a').get_attribute('href')
            followers.append(user_link)
            if len(followers) == num:
                break
        return followers

    def post(self, absoulte_path, caption):
        self.browser.get(USER % self.username)
        time.sleep(1)

        file_input = self.browser.find_element_by_css_selector('input[type=\'file\']')
        file_input.send_keys(absoulte_path)
        file_input.submit()

    def close(self):
        self.browser.close()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.browser.close()
