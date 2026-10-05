"""
Simple Selenium login test - the same example as in our project document,
written in Python.

Steps:
  1. Start the app in one terminal:   python app.py
  2. Run this in another terminal:    python login.py
"""
import time
import urllib.request

from selenium import webdriver
from selenium.webdriver.common.by import By

try:  # first make sure our app is running
    urllib.request.urlopen("http://127.0.0.1:5000", timeout=3)
except OSError:
    raise SystemExit("The Hospital Management System is not running. Start it first:  python app.py")

driver = webdriver.Chrome()                   # opens Google Chrome
driver.get("http://127.0.0.1:5000")            # opens the Hospital Management System

driver.find_element(By.ID, "username").send_keys("admin")      # type the username
driver.find_element(By.ID, "password").send_keys("admin123")   # type the password
driver.find_element(By.ID, "login").click()                    # click the Login button
time.sleep(2)                                                  # wait so we can see the result

assert "/dashboard" in driver.current_url, "Login test FAILED"  # check the expected result
print("Login test PASSED - dashboard opened")

driver.quit()                                  # closes the browser
