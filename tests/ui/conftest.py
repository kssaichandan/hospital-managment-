"""
Selenium fixtures.

- live_server : starts the Flask app in the background with a fresh empty database
- driver      : opens Google Chrome controlled by Selenium WebDriver

Optional settings (environment variables):
  HEADLESS=1          run Chrome without a window (for servers / CI)
  DEMO_DELAY=1.5      wait this many seconds after each step-heavy test (nice for class demos)
  CHROME_BINARY=...   path to a specific Chrome/Chromium
  CHROMEDRIVER_PATH=... path to a specific chromedriver (normally Selenium finds it by itself)
"""
import os
import threading
import time

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from werkzeug.serving import make_server

from app import create_app

SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "screenshots")


@pytest.fixture
def live_server(tmp_path):
    app = create_app(str(tmp_path / "selenium_test.db"))
    server = make_server("127.0.0.1", 0, app)  # port 0 = pick any free port
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()


@pytest.fixture(scope="session")
def browser():
    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1366,800")
    # Stop Chrome's "save password?" pop-ups from covering the page
    options.add_experimental_option("prefs", {
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
        "profile.password_manager_leak_detection": False,
    })
    if os.environ.get("HEADLESS") == "1":
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
    if os.environ.get("CHROME_BINARY"):
        options.binary_location = os.environ["CHROME_BINARY"]
    service = Service(os.environ["CHROMEDRIVER_PATH"]) if os.environ.get("CHROMEDRIVER_PATH") else None
    driver = webdriver.Chrome(options=options, service=service)
    driver.implicitly_wait(3)  # wait up to 3 s for elements to appear
    yield driver
    driver.quit()


@pytest.fixture
def driver(browser, request):
    browser.delete_all_cookies()  # every test starts logged out
    yield browser
    time.sleep(float(os.environ.get("DEMO_DELAY", "0")))
    # Save a screenshot of the final screen of every test (used in the report / PPT)
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    browser.save_screenshot(os.path.join(SCREENSHOT_DIR, f"{request.node.name}.png"))
