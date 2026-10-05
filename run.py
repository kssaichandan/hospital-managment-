"""
LIVE SELENIUM DEMO - Hospital Management System
===============================================
Watch Selenium WebDriver test our software in a real Chrome window, step by step.

  * Every element Selenium touches is highlighted with an orange box.
  * A caption at the bottom of the browser says what Selenium is doing.
  * The terminal prints every step, the real Selenium command behind it (grey),
    and PASS / FAIL for every test case.
  * At the end, Chrome shows a results page with all test cases.

How to run (two terminals):
    Terminal 1:   python app.py      <- start our Hospital Management System
    Terminal 2:   python run.py      <- Selenium tests it in front of you

Options:
    python run.py TC03 TC11     run only these test cases
    python run.py TC01-TC13     run a range of test cases
    python run.py --type negative   run only one type: positive, negative, boundary, edge, security
    python run.py --step        pause before each test case (press Enter to go on)
    python run.py --fast        no slow typing and no pauses
    python run.py --list        list all test cases
    python run.py --keep        keep the data from earlier runs (no clean start)
    python run.py --reset       only empty the app's data, then stop

Every run starts with a clean app: the old patients, doctors, appointments, records
and bills are deleted first (the 3 sample doctors come back). After the run,
everything Selenium added is still in the app, so you can open it and show the data.
"""
import argparse
import html
import http.cookiejar
import os
import sys
import time
import urllib.parse
import urllib.request
from contextlib import contextmanager
from datetime import date, timedelta

from selenium import webdriver
from selenium.common.exceptions import NoAlertPresentException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

BASE_URL = "http://127.0.0.1:5000"
TYPE_DELAY = 0.06  # seconds between key presses, so the audience can watch the typing
STEP_DELAY = 0.8   # seconds to pause after each step
TOMORROW = (date.today() + timedelta(days=1)).isoformat()
YESTERDAY = (date.today() - timedelta(days=1)).isoformat()
FAILURE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "demo_failures")

os.system("")  # switches on colours in the Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
GREEN, RED, CYAN, YELLOW, GREY, BOLD, RESET = (
    "\033[92m", "\033[91m", "\033[96m", "\033[93m", "\033[90m", "\033[1m", "\033[0m")

driver = None        # the Chrome browser controlled by Selenium
speed = 1            # 1 = presentation speed, 0 = full speed
quiet = False        # True while running "setup" steps
current_test = ""


# =====================================================================
#  Helper steps. Each one uses the normal Selenium commands
#  (find_element, send_keys, click, Select ...) and also shows the
#  audience what is happening.
# =====================================================================
CAPTION_JS = """
var box = document.getElementById('selenium-caption');
if (!box) {
  box = document.createElement('div');
  box.id = 'selenium-caption';
  box.style.cssText = 'position:fixed;left:50%;bottom:28px;transform:translateX(-50%);' +
    'z-index:2147483647;display:flex;align-items:center;gap:12px;max-width:85vw;' +
    'padding:12px 20px 12px 12px;border-radius:14px;color:#fff;pointer-events:none;' +
    'font:600 16px/1.35 "Segoe UI",system-ui,sans-serif;box-shadow:0 14px 34px rgba(0,0,0,.3);';
  box.innerHTML = '<span id="selenium-caption-tag" style="flex-shrink:0;padding:4px 10px;' +
    'border-radius:8px;background:rgba(255,255,255,.18);font-size:13px;letter-spacing:.04em">' +
    '</span><span id="selenium-caption-text"></span>';
  document.body.appendChild(box);
}
box.style.background = arguments[2];
document.getElementById('selenium-caption-tag').textContent = 'SELENIUM \\u00b7 ' + arguments[0];
document.getElementById('selenium-caption-text').textContent = arguments[1];
"""
last_highlighted = None


def pause(seconds=STEP_DELAY):
    time.sleep(seconds * speed)


def caption(text, colour="#0f172a"):
    """Shows a label at the bottom of the browser window (only for the demo)."""
    if not quiet:
        driver.execute_script(CAPTION_JS, current_test, text, colour)


def step(text, selenium_code=None):
    """Prints a step, and in grey the real Selenium command that does it."""
    if not quiet:
        print(f"     {CYAN}>{RESET} {text}")
        if selenium_code:
            print(f"         {GREY}{selenium_code}{RESET}")
        caption(text)


def shorten(text, limit=70):
    text = " ".join(text.split())
    return text if len(text) <= limit else text[:limit - 3] + "..."


def highlight(element):
    """Scrolls to the element and draws an orange box around it."""
    global last_highlighted
    try:
        if last_highlighted is not None:
            driver.execute_script("arguments[0].style.outline = '';", last_highlighted)
    except WebDriverException:
        pass  # the old element is gone because a new page loaded
    driver.execute_script(
        "arguments[0].scrollIntoView({block: 'center'});"
        "arguments[0].style.outline = '3px solid #f59e0b';"
        "arguments[0].style.outlineOffset = '3px';", element)
    last_highlighted = element
    pause(0.4)


def find(element_id):
    """Locate an element by its id - the locator we use in every test."""
    element = driver.find_element(By.ID, element_id)
    highlight(element)
    return element


def open_page(path=""):
    if not quiet:
        print(f"     {CYAN}>{RESET} Open {BASE_URL}{path or '/'}")
        print(f'         {GREY}driver.get("{BASE_URL}{path or "/"}"){RESET}')
    driver.get(BASE_URL + path)
    caption(f"Open {BASE_URL}{path or '/'}")
    pause()


def type_into(element_id, text):
    step(f'Type "{text}" into #{element_id}',
         f'driver.find_element(By.ID, "{element_id}").send_keys("{text}")')
    box = find(element_id)
    box.clear()
    if speed:
        for letter in text:  # type one letter at a time, like a person
            box.send_keys(letter)
            time.sleep(TYPE_DELAY)
    else:
        box.send_keys(text)
    pause()


def choose(element_id, text=None, value=None):
    """Pick an option in a drop-down list using Selenium's Select class."""
    dropdown = driver.find_element(By.ID, element_id)
    if text is None:
        text = dropdown.find_element(By.CSS_SELECTOR, f"option[value='{value}']").text
    how = f'select_by_visible_text("{text}")' if value is None else f'select_by_value("{value}")'
    step(f'Select "{text}" in drop-down #{element_id}',
         f'Select(driver.find_element(By.ID, "{element_id}")).{how}')
    highlight(dropdown)
    if value is None:
        Select(dropdown).select_by_visible_text(text)
    else:
        Select(dropdown).select_by_value(str(value))
    pause()


def set_date(element_id, value):
    step(f"Set the date {value} in #{element_id}",
         f"driver.execute_script(\"arguments[0].value = '{value}'\", date_box)")
    box = find(element_id)
    # Date pickers look different in every country, so we set the value with JavaScript
    driver.execute_script("arguments[0].value = arguments[1];", box, value)
    pause()


def click(element_id, label):
    step(f"Click {label}  (#{element_id})", f'driver.find_element(By.ID, "{element_id}").click()')
    button = find(element_id)
    button.click()
    # Wait until the next page has loaded (the old button disappears)
    wait = WebDriverWait(driver, 10, ignored_exceptions=[WebDriverException])
    wait.until(EC.staleness_of(button))
    pause(0.3)


def check(condition, description):
    """The actual TEST: if the condition is False, the test case FAILS."""
    if not condition:
        raise AssertionError(description)
    print(f"     {GREEN}✔ CHECK PASSED:{RESET} {description}")
    caption("✔ " + description, "#15803d")
    pause()


def read(element_id):
    """Reads the text of an element - this is what the check compares."""
    text = find(element_id).text
    if not quiet:
        print(f'         {GREY}driver.find_element(By.ID, "{element_id}").text  ->  "{shorten(text)}"{RESET}')
    return text


def message(kind):
    """Text of the green ('success') or red ('error') message on the page."""
    if not driver.find_elements(By.ID, f"flash-{kind}"):
        if not quiet:
            print(f'         {GREY}no element with id "flash-{kind}" on the page{RESET}')
        return ""
    return read(f"flash-{kind}")


def current_url():
    if not quiet:
        print(f'         {GREY}driver.current_url  ->  "{driver.current_url}"{RESET}')
    return driver.current_url


def row_ids(table_id, prefix):
    """Reads the id of every table row, e.g. 'patient-row-7' -> 7."""
    rows = driver.find_elements(By.CSS_SELECTOR, f"#{table_id} tr[id^='{prefix}']")
    return [int(row.get_attribute("id").rsplit("-", 1)[1]) for row in rows]


@contextmanager
def setup(text):
    """Runs preparation steps quickly, so the demo stays focused on the real test."""
    global speed, quiet
    print(f"     {GREY}~ Setup: {text}{RESET}")
    caption("Setup: " + text, "#475569")
    old = speed, quiet
    speed, quiet = 0, True
    try:
        yield
    finally:
        speed, quiet = old


# ---------------- steps used by many test cases ----------------
def login(username="admin", password="admin123"):
    driver.delete_all_cookies()  # start logged out
    open_page("/")
    type_into("username", username)
    type_into("password", password)
    click("login", "the Login button")


def submit_patient(name, age="30", gender="Male", phone="9876543210", disease="Fever"):
    """Fills in the Add Patient form and submits it."""
    open_page("/patients")
    type_into("patient-name", name)
    type_into("patient-age", age)
    choose("patient-gender", gender)
    type_into("patient-phone", phone)
    type_into("patient-disease", disease)
    click("add-patient-btn", "Add Patient")


def add_patient(name, age="30", gender="Male", phone="9876543210", disease="Fever"):
    submit_patient(name, age, gender, phone, disease)
    return max(row_ids("patients-table", "patient-row-"))  # ID of the new patient


def submit_doctor(name, specialization, phone="9876501234", fee="400"):
    """Fills in the Add Doctor form and submits it."""
    open_page("/doctors")
    type_into("doctor-name", name)
    type_into("doctor-specialization", specialization)
    type_into("doctor-phone", phone)
    type_into("doctor-fee", fee)
    click("add-doctor-btn", "Add Doctor")


def add_doctor(name, specialization, phone="9876501234", fee="400"):
    submit_doctor(name, specialization, phone, fee)
    return max(row_ids("doctors-table", "doctor-row-"))  # ID of the new doctor


def submit_record(patient_id, diagnosis, treatment, prescription, day=None):
    """Fills in the Add Medical Record form and submits it."""
    open_page("/records")
    choose("record-patient", value=patient_id)
    if day:
        set_date("record-date", day)
    if diagnosis:
        type_into("record-diagnosis", diagnosis)
    else:
        step("Leave Diagnosis empty")
    type_into("record-treatment", treatment)
    type_into("record-prescription", prescription)
    click("add-record-btn", "Save Record")


def submit_bill(patient_id, consultation, treatment):
    """Fills in the Generate Bill form and submits it."""
    open_page("/billing")
    choose("bill-patient", value=patient_id)
    type_into("bill-consultation", consultation)
    type_into("bill-treatment", treatment)
    click("create-bill-btn", "Generate Bill")


def no_history(patient_id):
    """Opens the patient's medical history and checks that it is empty."""
    choose("history-patient", value=patient_id)
    click("history-btn", "View Patient History")
    check("No medical records found" in read("records-table"), "No medical record was saved")


def alert_is_open():
    """True if a JavaScript pop-up (alert) is open - that would mean a script ran."""
    try:
        driver.switch_to.alert
        return True
    except NoAlertPresentException:
        return False


def book_appointment(patient_id, doctor_id, day, slot):
    open_page("/appointments")
    choose("appt-patient", value=patient_id)
    choose("appt-doctor", value=doctor_id)
    set_date("appt-date", day)
    choose("appt-time", slot)
    click("book-btn", "Book Appointment")


# =====================================================================
#  TEST CASES  (TC01 - TC09 are the test cases from our project document)
# =====================================================================
def tc01():
    login("admin", "admin123")
    check("/dashboard" in current_url(), "The dashboard page opened")
    check("Login successful" in message("success"), 'Green message "Login successful." is shown')


def tc02():
    login("admin", "wrongpassword")
    check("Invalid username or password" in message("error"),
          'Red message "Invalid username or password." is shown')
    check("/dashboard" not in current_url(), "The user stays on the login page")


def tc03():
    with setup("log in as admin"):
        login()
    patient_id = add_patient("Ravi Teja", "30", "Male", "9876543210", "Fever")
    check("Patient added successfully" in message("success"),
          'Green message "Patient added successfully." is shown')
    row = read(f"patient-row-{patient_id}")
    check("Ravi Teja" in row, f"Ravi Teja is in the patients table with ID #{patient_id}")


def tc04():
    with setup("log in as admin"):
        login()
    open_page("/patients")
    before = len(row_ids("patients-table", "patient-row-"))
    step("Leave every field of the form empty")
    pause()
    click("add-patient-btn", "Add Patient with an empty form")
    check("Name must have at least 2 characters" in message("error"),
          'Red validation message "Name must have at least 2 characters." is shown')
    check(len(row_ids("patients-table", "patient-row-")) == before, "No empty patient was saved")


def tc05():
    with setup("log in, add a patient and a doctor"):
        login()
        patient_id = add_patient("Meena Kumari", "45", "Female", "9988001122", "Back pain")
        doctor_id = add_doctor("Dr. Suresh Babu", "General Physician", "9876512345", "300")
    book_appointment(patient_id, doctor_id, TOMORROW, "10:00")
    check("Appointment booked successfully" in message("success"),
          'Green message "Appointment booked successfully." is shown')
    row = read(f"appointment-row-{max(row_ids('appointments-table', 'appointment-row-'))}")
    check("Dr. Suresh Babu" in row and TOMORROW in row and "Scheduled" in row,
          f"Appointment with Dr. Suresh Babu on {TOMORROW} is Scheduled")


def tc06():
    with setup("log in, add two patients"):
        login()
        add_patient("Arjun Rao", "52", "Male", "9988776655", "Chest pain")
        patient_id = add_patient("Sita Devi", "28", "Female", "9123456789", "Cough")
    open_page("/patients")
    type_into("search-box", str(patient_id))
    click("search-btn", "Search")
    table = read("patients-table")
    check("Sita Devi" in table and "Cough" in table, f"Patient #{patient_id} Sita Devi is displayed")
    check(row_ids("patients-table", "patient-row-") == [patient_id], "Only that one patient is shown")


def tc07():
    with setup("log in, add a patient with disease Fever"):
        login()
        patient_id = add_patient("Kiran Kumar", "36", "Male", "9876501111", "Fever")
    open_page("/patients")
    click(f"edit-patient-{patient_id}", "Edit")
    type_into("patient-disease", "Typhoid")
    click("update-patient-btn", "Update Patient")
    check("Patient details updated successfully" in message("success"),
          'Green message "Patient details updated successfully." is shown')
    check("Typhoid" in read(f"patient-row-{patient_id}"), "The table now shows Typhoid")


def tc08():
    with setup("log in, add a patient"):
        login()
        patient_id = add_patient("Rahul Verma", "29", "Male", "9876502222", "Fracture")
    open_page("/patients")
    find(f"patient-row-{patient_id}")
    pause()
    click(f"delete-patient-{patient_id}", "Delete")
    check("Patient removed successfully" in message("success"),
          'Green message "Patient removed successfully." is shown')
    check(patient_id not in row_ids("patients-table", "patient-row-"),
          f"Patient #{patient_id} is no longer in the table")


def tc09():
    with setup("log in as admin"):
        login()
    click("nav-logout", "Logout")
    check("You have been logged out" in message("success"), 'Message "You have been logged out." is shown')
    check(find("login").is_displayed(), "The login page is shown again")
    step("Try to open the dashboard again without logging in")
    open_page("/dashboard")
    check("Please log in first" in message("error"),
          'The dashboard is protected: "Please log in first."')


def tc10():
    with setup("log in as admin"):
        login()
    doctor_id = add_doctor("Dr. Anil Reddy", "Orthopedic", "9123456780", "450")
    check("Doctor added successfully" in message("success"), 'Green message "Doctor added successfully." is shown')
    click(f"toggle-doctor-{doctor_id}", "Mark Unavailable")
    check("Not Available" in read(f"doctor-row-{doctor_id}"), "Dr. Anil Reddy now shows Not Available")


def tc11():
    with setup("log in, add two patients and one doctor, book the doctor at 11:00"):
        login()
        first = add_patient("Vijay Anand", "40", "Male", "9876503333", "Fever")
        second = add_patient("Divya Rao", "31", "Female", "9876504444", "Migraine")
        doctor_id = add_doctor("Dr. Neha Gupta", "Dermatologist", "9876505555", "350")
        book_appointment(first, doctor_id, TOMORROW, "11:00")
    step("Now book the SAME doctor, date and time for another patient")
    pause()
    book_appointment(second, doctor_id, TOMORROW, "11:00")
    check("already booked" in message("error"),
          'Double booking is blocked: "This doctor is already booked for that date and time."')


def tc12():
    with setup("log in, add a patient"):
        login()
        patient_id = add_patient("Pooja Hegde", "26", "Female", "9876506666", "Fever")
    open_page("/records")
    choose("record-patient", value=patient_id)
    type_into("record-diagnosis", "Viral fever")
    type_into("record-treatment", "Rest and fluids")
    type_into("record-prescription", "Paracetamol 500mg")
    click("add-record-btn", "Save Record")
    check("Medical record saved successfully" in message("success"),
          'Green message "Medical record saved successfully." is shown')
    choose("history-patient", value=patient_id)
    click("history-btn", "View Patient History")
    check("Viral fever" in read("records-table"), "The record is in Pooja Hegde's history")


def tc13():
    with setup("log in, add a patient"):
        login()
        patient_id = add_patient("Ganesh Iyer", "60", "Male", "9876507777", "Diabetes")
    open_page("/billing")
    choose("bill-patient", value=patient_id)
    type_into("bill-consultation", "500")
    type_into("bill-treatment", "1200")
    click("create-bill-btn", "Generate Bill")
    check("Bill generated successfully" in message("success"), 'Green message "Bill generated successfully." is shown')
    bill_id = max(row_ids("bills-table", "bill-row-"))
    total = read(f"bill-total-{bill_id}")
    check(total == "1700.00", f"Bill total is 500 + 1200 = 1700.00 (page shows {total})")


# =====================================================================
#  TC14 - TC37 : NEGATIVE, BOUNDARY / EDGE and SECURITY test cases
#  (wrong input must show an error and must NOT be saved)
# =====================================================================
def tc14():
    login("doctor", "admin123")
    check("Invalid username or password" in message("error"),
          'Red message "Invalid username or password." is shown')
    check("/dashboard" not in current_url(), "The user stays on the login page")


def tc15():
    driver.delete_all_cookies()
    open_page("/")
    step("Leave username and password empty")
    pause()
    click("login", "the Login button")
    check("Invalid username or password" in message("error"),
          'Red message "Invalid username or password." is shown')
    check("/dashboard" not in current_url(), "The user stays on the login page")


def tc16():
    step("Try a classic SQL injection attack in the login form")
    login("admin' --", "' OR '1'='1")
    check("Invalid username or password" in message("error"), "The attack is refused")
    check("/dashboard" not in current_url(), "The user stays on the login page")


def tc17():
    driver.delete_all_cookies()  # make sure nobody is logged in
    step("Type the address of the Patients page directly, without logging in")
    open_page("/patients")
    check(current_url().rstrip("/") == BASE_URL, "Selenium was sent back to the login page")
    check("Please log in first" in message("error"), 'Red message "Please log in first." is shown')


def tc18():
    with setup("log in as admin"):
        login()
    submit_patient("Nisha Patel", "30", "Female", "12345", "Fever")
    check("Phone number must be exactly 10 digits" in message("error"),
          'Red message "Phone number must be exactly 10 digits." is shown')
    check("Nisha Patel" not in read("patients-table"), "Nisha Patel was NOT saved")


def tc19():
    with setup("log in as admin"):
        login()
    submit_patient("Nisha Patel", "30", "Female", "98765432101", "Fever")
    check("Phone number must be exactly 10 digits" in message("error"),
          "11 digits (one too many) is rejected")
    check("Nisha Patel" not in read("patients-table"), "Nisha Patel was NOT saved")


def tc20():
    with setup("log in as admin"):
        login()
    submit_patient("Ravi123", "30", "Male", "9876543210", "Fever")
    check("Name can only contain letters" in message("error"),
          'Red message "Name can only contain letters ..." is shown')
    check("Ravi123" not in read("patients-table"), "Ravi123 was NOT saved")


def tc21():
    with setup("log in as admin"):
        login()
    submit_patient("Ramaiah Shetty", "121", "Male", "9876543210", "Weakness")
    check("Age must be between 0 and 120" in message("error"),
          "Age 121 (just above the limit) is rejected")
    check("Ramaiah Shetty" not in read("patients-table"), "Ramaiah Shetty was NOT saved")


def cell(row_id, column):
    """Text of one cell in a table row (column 0 is the first column)."""
    return driver.find_element(By.ID, row_id).find_elements(By.TAG_NAME, "td")[column].text


def tc22():
    with setup("log in as admin"):
        login()
    baby = add_patient("Baby Sharma", "0", "Female", "9000000001", "Jaundice")
    check("Patient added successfully" in message("success"), "Age 0 (the lowest limit) is accepted")
    elder = add_patient("Grandpa Rao", "120", "Male", "9000000002", "Weakness")
    check("Patient added successfully" in message("success"), "Age 120 (the highest limit) is accepted")
    check(cell(f"patient-row-{baby}", 2) == "0" and cell(f"patient-row-{elder}", 2) == "120",
          "The table shows ages 0 and 120")


def tc23():
    with setup("log in as admin"):
        login()
    open_page("/patients")
    type_into("search-box", "99999")
    click("search-btn", "Search")
    check("No patients found" in read("patients-table"), 'Patient ID 99999 does not exist: "No patients found."')


def tc24():
    with setup("log in, add a patient with phone 9876508888"):
        login()
        patient_id = add_patient("Lakshmi Iyer", "41", "Female", "9876508888", "Asthma")
    open_page("/patients")
    click(f"edit-patient-{patient_id}", "Edit")
    type_into("patient-phone", "123")
    click("update-patient-btn", "Update Patient")
    check("Phone number must be exactly 10 digits" in message("error"),
          'Red message "Phone number must be exactly 10 digits." is shown')
    open_page("/patients")
    check("9876508888" in read(f"patient-row-{patient_id}"), "The old phone number is still saved")


def tc25():
    with setup("log in as admin"):
        login()
    attack = "<script>alert('hacked')</script>"
    patient_id = add_patient("Hacker Test", "30", "Male", "9876509999", attack)
    check(not alert_is_open(), "The script did NOT run (no pop-up)")
    check(attack in read(f"patient-row-{patient_id}"), "It is shown as plain text in the table")


def tc26():
    with setup("log in as admin"):
        login()
    submit_doctor("Dr. Free Clinic", "General Physician", "9876510000", "0")
    check("Fee must be greater than 0" in message("error"), 'Red message "Fee must be greater than 0." is shown')
    check("Dr. Free Clinic" not in read("doctors-table"), "Dr. Free Clinic was NOT saved")


def tc27():
    with setup("log in as admin"):
        login()
    open_page("/doctors")
    type_into("doctor-search-box", "Veterinarian")
    click("doctor-search-btn", "Search")
    check("No doctors found" in read("doctors-table"), 'No match: "No doctors found."')


def tc28():
    with setup("log in, add a patient and a doctor"):
        login()
        patient_id = add_patient("Farhan Ali", "33", "Male", "9876511111", "Fever")
        doctor_id = add_doctor("Dr. Kavya Nair", "Dermatologist", "9876511112", "350")
    book_appointment(patient_id, doctor_id, YESTERDAY, "10:00")
    check("Appointment date cannot be in the past" in message("error"),
          'Red message "Appointment date cannot be in the past." is shown')
    check("Dr. Kavya Nair" not in read("appointments-table"), "No appointment was booked")


def tc29():
    with setup("log in, add a doctor"):
        login()
        doctor_id = add_doctor("Dr. Mohan Das", "ENT Specialist", "9876511113", "300")
    open_page("/appointments")
    step('Leave the patient as "Select patient"')
    choose("appt-doctor", value=doctor_id)
    set_date("appt-date", TOMORROW)
    click("book-btn", "Book Appointment")
    check("Please select a valid patient" in message("error"),
          'Red message "Please select a valid patient." is shown')
    check("Dr. Mohan Das" not in read("appointments-table"), "No appointment was booked")


def tc30():
    with setup("log in, add a patient and a doctor, mark the doctor Unavailable"):
        login()
        patient_id = add_patient("Sneha Reddy", "27", "Female", "9876511114", "Allergy")
        doctor_id = add_doctor("Dr. Ravi Shankar", "Cardiologist", "9876511115", "600")
        click(f"toggle-doctor-{doctor_id}", "Mark Unavailable")
    book_appointment(patient_id, doctor_id, TOMORROW, "14:00")
    check("This doctor is not available" in message("error"),
          'Red message "This doctor is not available right now." is shown')
    check("Dr. Ravi Shankar" not in read("appointments-table"), "No appointment was booked")


def tc31():
    with setup("log in, add a patient and two doctors, book the first doctor at 15:00"):
        login()
        patient_id = add_patient("Manoj Kumar", "48", "Male", "9876511116", "Back pain")
        first = add_doctor("Dr. Asha Menon", "Orthopedic", "9876511117", "450")
        second = add_doctor("Dr. Imran Khan", "Neurologist", "9876511118", "700")
        book_appointment(patient_id, first, TOMORROW, "15:00")
    step("Now book the SAME patient with ANOTHER doctor at the same date and time")
    pause()
    book_appointment(patient_id, second, TOMORROW, "15:00")
    check("This patient already has an appointment" in message("error"),
          "A patient cannot be in two places at once - booking refused")


def tc32():
    with setup("log in, add a patient and a doctor, book 16:00"):
        login()
        patient_id = add_patient("Rekha Singh", "55", "Female", "9876511119", "Diabetes")
        doctor_id = add_doctor("Dr. Vikram Joshi", "General Physician", "9876511120", "300")
        book_appointment(patient_id, doctor_id, TOMORROW, "16:00")
        first = max(row_ids("appointments-table", "appointment-row-"))
    click(f"cancel-appointment-{first}", "Cancel")
    step("Book the SAME doctor, date and time again")
    book_appointment(patient_id, doctor_id, TOMORROW, "16:00")
    check("Appointment booked successfully" in message("success"),
          "The cancelled slot can be booked again")
    check("Cancelled" in read(f"appointment-row-{first}"), "The old appointment is shown as Cancelled")


def tc33():
    with setup("log in, add a patient"):
        login()
        patient_id = add_patient("Kavitha Rao", "38", "Female", "9876511121", "Headache")
    submit_record(patient_id, "", "Rest", "Paracetamol")
    check("Diagnosis is required" in message("error"), 'Red message "Diagnosis is required." is shown')
    no_history(patient_id)


def tc34():
    with setup("log in, add a patient"):
        login()
        patient_id = add_patient("Suresh Gowda", "62", "Male", "9876511122", "Fever")
    submit_record(patient_id, "Viral fever", "Rest", "Paracetamol", day=TOMORROW)
    check("Visit date cannot be in the future" in message("error"),
          'Red message "Visit date cannot be in the future." is shown')
    no_history(patient_id)


def tc35():
    with setup("log in, add a patient"):
        login()
        patient_id = add_patient("Anita Das", "29", "Female", "9876511123", "Checkup")
    submit_bill(patient_id, "0", "0")
    check("Total amount must be greater than 0" in message("error"),
          'Red message "Total amount must be greater than 0." is shown')
    check("Anita Das" not in read("bills-table"), "No bill was saved for Anita Das")


def tc36():
    with setup("log in, add a patient"):
        login()
        patient_id = add_patient("Prakash Jain", "50", "Male", "9876511124", "Fracture")
    submit_bill(patient_id, "-100", "500")
    check("Consultation charge cannot be negative" in message("error"),
          'Red message "Consultation charge cannot be negative." is shown')
    check("Prakash Jain" not in read("bills-table"), "No bill was saved for Prakash Jain")


def tc37():
    with setup("log in, add a patient"):
        login()
        patient_id = add_patient("Deepa Nair", "35", "Female", "9876511125", "Migraine")
    submit_bill(patient_id, "499.50", "0.25")
    check("Bill generated successfully" in message("success"), 'Green message "Bill generated successfully." is shown')
    bill_id = max(row_ids("bills-table", "bill-row-"))
    total = read(f"bill-total-{bill_id}")
    check(total == "499.75", f"Bill total is 499.50 + 0.25 = 499.75 (page shows {total})")


TEST_CASES = [
    # id,   type,       test case,                    input,                          expected result,                 function
    ("TC01", "Positive", "Login with valid details", "Correct username/password", "Login successful", tc01),
    ("TC02", "Negative", "Login with invalid details", "Wrong password", "Error message displayed", tc02),
    ("TC03", "Positive", "Add patient", "Valid patient details", "Patient added", tc03),
    ("TC04", "Negative", "Empty patient form", "Empty fields", "Validation message", tc04),
    ("TC05", "Positive", "Book appointment", "Valid doctor/date", "Appointment booked", tc05),
    ("TC06", "Positive", "Search patient", "Patient ID", "Patient details displayed", tc06),
    ("TC07", "Positive", "Update patient", "Modified details", "Details updated", tc07),
    ("TC08", "Positive", "Delete patient", "Existing patient", "Patient removed", tc08),
    ("TC09", "Positive", "Logout", "Click Logout", "User returned to login page", tc09),
    ("TC10", "Positive", "Doctor availability", "Mark doctor unavailable", 'Shows "Not Available"', tc10),
    ("TC11", "Negative", "Double booking", "Same doctor, date and time", 'Error "already booked"', tc11),
    ("TC12", "Positive", "Medical record", "Diagnosis, treatment, prescription", "Record saved", tc12),
    ("TC13", "Positive", "Billing total", "500 + 1200", "Total = 1700.00", tc13),
    ("TC14", "Negative", "Login with wrong username", "Username doctor", "Error message displayed", tc14),
    ("TC15", "Negative", "Login with empty fields", "Empty username/password", "Error message displayed", tc15),
    ("TC16", "Security", "SQL injection in login", "admin' --  /  ' OR '1'='1", "Login refused", tc16),
    ("TC17", "Security", "Page without login", "Open /patients directly", "Sent to login page", tc17),
    ("TC18", "Negative", "Phone too short", "Phone 12345", "Error, not saved", tc18),
    ("TC19", "Boundary", "Phone one digit too long", "Phone with 11 digits", "Error, not saved", tc19),
    ("TC20", "Negative", "Name with numbers", "Name Ravi123", "Error, not saved", tc20),
    ("TC21", "Boundary", "Age just above limit", "Age 121", "Error, not saved", tc21),
    ("TC22", "Boundary", "Age at the limits", "Age 0 and age 120", "Both accepted", tc22),
    ("TC23", "Negative", "Search unknown patient", "Patient ID 99999", '"No patients found"', tc23),
    ("TC24", "Negative", "Invalid patient update", "Phone 123", "Error, old data kept", tc24),
    ("TC25", "Security", "Script injection (XSS)", "<script> in disease", "Shown as text, not run", tc25),
    ("TC26", "Boundary", "Doctor fee 0", "Fee 0", "Error, not saved", tc26),
    ("TC27", "Negative", "Search unknown doctor", "Veterinarian", '"No doctors found"', tc27),
    ("TC28", "Negative", "Appointment in the past", "Yesterday's date", "Error, not booked", tc28),
    ("TC29", "Negative", "Appointment without patient", "No patient selected", "Error, not booked", tc29),
    ("TC30", "Negative", "Unavailable doctor", "Doctor marked unavailable", "Error, not booked", tc30),
    ("TC31", "Negative", "Patient double booking", "Same patient, 2 doctors, same time", "Error, not booked", tc31),
    ("TC32", "Edge", "Re-book cancelled slot", "Cancel, then book again", "Booked again", tc32),
    ("TC33", "Negative", "Record without diagnosis", "Empty diagnosis", "Error, not saved", tc33),
    ("TC34", "Negative", "Record with future date", "Tomorrow's date", "Error, not saved", tc34),
    ("TC35", "Boundary", "Bill total 0", "0 + 0", "Error, not saved", tc35),
    ("TC36", "Negative", "Negative charge", "-100 + 500", "Error, not saved", tc36),
    ("TC37", "Edge", "Decimal amounts", "499.50 + 0.25", "Total = 499.75", tc37),
]
TEST_TYPES = ("positive", "negative", "boundary", "edge", "security")


# =====================================================================
#  Runner: runs the test cases one by one and prints the results
# =====================================================================
def open_browser():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    # Stop Chrome's "save password?" pop-ups from covering the page during the demo
    options.add_experimental_option("prefs", {
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
        "profile.password_manager_leak_detection": False,
    })
    browser = webdriver.Chrome(options=options)  # Selenium finds the right ChromeDriver itself
    browser.implicitly_wait(3)  # wait up to 3 s for elements to appear
    return browser


def browser_is_open():
    """False if someone closed the Chrome window that Selenium controls."""
    try:
        handles = driver.window_handles
    except WebDriverException:
        return False
    if not handles:
        return False
    try:
        driver.current_window_handle
    except WebDriverException:  # our tab was closed, but another one is still open
        driver.switch_to.window(handles[0])
    return True


def make_sure_browser_is_open():
    global driver
    if browser_is_open():
        return
    print(f"\n{YELLOW}The Selenium Chrome window was closed - opening a new one ...{RESET}")
    try:
        driver.quit()
    except WebDriverException:
        pass
    driver = open_browser()


def write_page(page):
    driver.get("about:blank")
    driver.execute_script("document.open(); document.write(arguments[0]); document.close();", page)


def show_start_page(first_test):
    """Tells the audience (and us) that this window belongs to Selenium."""
    write_page(f"""<!doctype html><html><head><meta charset="utf-8"><title>Selenium is ready</title>
<style>
 body{{margin:0;min-height:100vh;display:grid;place-items:center;font:17px/1.5 "Segoe UI",system-ui,sans-serif;
      color:#e2e8f0;background:linear-gradient(160deg,#0b1726,#0f2a3d 55%,#0b3b3a)}}
 .box{{max-width:640px;padding:40px;text-align:center}}
 small{{color:#5eead4;font-weight:700;letter-spacing:.1em}}
 h1{{margin:8px 0 14px;font-size:44px;color:#fff}}
 .warn{{margin:22px 0;padding:14px 18px;border-radius:12px;background:rgba(245,158,11,.14);color:#fcd34d}}
 kbd{{padding:2px 10px;border-radius:6px;background:#fff;color:#0f172a;font-weight:700}}
</style></head><body><div class="box">
 <small>SELENIUM WEBDRIVER</small>
 <h1>Selenium is ready</h1>
 <p>This Chrome window is controlled by Selenium. It will open our Hospital Management System
    and test it by itself.</p>
 <p class="warn">Please do not close this window or type in it.</p>
 <p>Press <kbd>Enter</kbd> in the terminal to start <b>{html.escape(first_test)}</b>.</p>
</div></body></html>""")


def run_test(test_id, kind, name, given, expected, function):
    global current_test
    current_test = f"{test_id} {name}"
    line = "=" * 64
    print(f"\n{BOLD}{line}\n {test_id}  {name}{RESET}  {GREY}[{kind} test]{RESET}")
    print(f"       Input: {given}   |   Expected: {expected}\n{BOLD}{line}{RESET}")
    started = time.time()
    try:
        function()
        seconds = time.time() - started
        print(f"   {GREEN}{BOLD}RESULT: PASS{RESET} {GREY}({seconds:.1f} s){RESET}")
        return "PASS", seconds, ""
    except Exception as error:  # an AssertionError means the check failed
        seconds = time.time() - started
        reason = str(error).splitlines()[0] if str(error) else type(error).__name__
        if any(text in reason for text in ("invalid session id", "no such window", "target window already closed")):
            reason = "The Selenium Chrome window was closed during the test"
        os.makedirs(FAILURE_DIR, exist_ok=True)
        picture = os.path.join(FAILURE_DIR, f"{test_id}.png")
        try:
            caption("✘ FAILED: " + reason, "#b91c1c")
            driver.save_screenshot(picture)  # proof of what the page looked like
        except WebDriverException:
            picture = "(not saved)"
        print(f"     {RED}✘ CHECK FAILED:{RESET} {reason}")
        print(f"   {RED}{BOLD}RESULT: FAIL{RESET} {GREY}({seconds:.1f} s)  screenshot: {picture}{RESET}")
        pause(2)
        return "FAIL", seconds, reason


def show_results_page(results, total_seconds):
    passed = sum(1 for r in results if r[3] == "PASS")
    failed = len(results) - passed
    rows = "".join(
        f"<tr><td class='id'>{tid}</td><td class='t'>{kind}</td><td>{html.escape(name)}"
        f"{f'<div class=why>{html.escape(reason)}</div>' if reason else ''}</td>"
        f"<td>{html.escape(given)}</td><td>{html.escape(expected)}</td>"
        f"<td><span class='pill {status.lower()}'>{status}</span></td><td class='t'>{secs:.1f} s</td></tr>"
        for tid, kind, name, status, secs, given, expected, reason in results)
    page = f"""<!doctype html><html><head><meta charset="utf-8"><title>Selenium Test Results</title>
<style>
 body{{margin:0;font:15px/1.5 "Segoe UI",system-ui,sans-serif;background:#f4f6fa;color:#0f172a}}
 header{{padding:36px 56px;color:#fff;background:linear-gradient(135deg,#0b1726,#0f2a3d 60%,#0b3b3a)}}
 header small{{color:#5eead4;font-weight:700;letter-spacing:.08em}}
 h1{{margin:6px 0 0;font-size:30px}} .wrap{{padding:28px 56px}}
 .cards{{display:flex;gap:16px;margin-bottom:22px}}
 .card{{flex:1;background:#fff;border:1px solid #e6eaf0;border-radius:14px;padding:18px 22px}}
 .card b{{display:block;font-size:34px;line-height:1.2}} .card span{{color:#64748b}}
 .ok b{{color:#15803d}} .bad b{{color:{'#dc2626' if failed else '#94a3b8'}}}
 table{{width:100%;border-collapse:collapse;background:#fff;border:1px solid #e6eaf0;border-radius:14px;overflow:hidden}}
 th{{text-align:left;padding:11px 16px;background:#f8fafc;color:#64748b;font-size:12px;text-transform:uppercase;letter-spacing:.06em}}
 td{{padding:11px 16px;border-top:1px solid #eef1f5}} .id{{font-weight:700}} .t{{color:#64748b}}
 .pill{{padding:3px 12px;border-radius:999px;font-weight:700;font-size:13px}}
 .why{{color:#b91c1c;font-size:13px}}
 .pill.pass{{background:#dcfce7;color:#15803d}} .pill.fail{{background:#fee2e2;color:#b91c1c}}
</style></head><body>
<header><small>SELENIUM WEBDRIVER &middot; LIVE TEST RUN</small><h1>City Hospital HMS &mdash; Test Results</h1></header>
<div class="wrap">
 <div class="cards">
  <div class="card"><b>{len(results)}</b><span>Test cases run</span></div>
  <div class="card ok"><b>{passed}</b><span>Passed</span></div>
  <div class="card bad"><b>{failed}</b><span>Failed</span></div>
  <div class="card"><b>{total_seconds:.0f} s</b><span>Total time</span></div>
 </div>
 <table><tr><th>ID</th><th>Type</th><th>Test case</th><th>Input</th><th>Expected result</th><th>Result</th><th>Time</th></tr>{rows}</table>
</div></body></html>"""
    write_page(page)


def wait_for_enter(prompt):
    try:
        input(f"\n{YELLOW}{prompt}{RESET}")
    except EOFError:  # not started from a terminal
        time.sleep(3)


def app_is_running():
    try:
        urllib.request.urlopen(BASE_URL, timeout=3)
        return True
    except OSError:
        return False


def reset_app_data():
    """Clean start: logs in to the app and asks it to delete the old patients, doctors,
    appointments, records and bills (the 3 sample doctors are added again)."""
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    login_form = urllib.parse.urlencode({"username": "admin", "password": "admin123"}).encode()
    try:
        opener.open(BASE_URL + "/", login_form, timeout=10)
        page = opener.open(BASE_URL + "/reset-demo-data", b"", timeout=10).read().decode("utf-8", "replace")
    except OSError as error:
        page = str(error)
    if "Demo data reset" not in page:
        print(f"{YELLOW}Could not empty the old data - it stays in the app. "
              f"Restart the app (python app.py) and try again.{RESET}")
        return False
    print(f"{GREEN}Clean start:{RESET} old patients, doctors, appointments, records and bills deleted "
          f"{GREY}(3 sample doctors added again){RESET}")
    return True


def main():
    global driver, speed, BASE_URL
    parser = argparse.ArgumentParser(description="Live Selenium demo for the Hospital Management System")
    parser.add_argument("tests", nargs="*",
                        help="test case IDs to run, e.g. TC01 TC05 or a range TC01-TC13 (default: all)")
    parser.add_argument("--type", choices=TEST_TYPES,
                        help="run only one type of test case, e.g. --type negative")
    parser.add_argument("--step", action="store_true", help="pause before each test case")
    parser.add_argument("--fast", action="store_true", help="no slow typing and no pauses")
    parser.add_argument("--list", action="store_true", help="list the test cases and exit")
    parser.add_argument("--url", default=BASE_URL, help=f"address of the app (default {BASE_URL})")
    parser.add_argument("--keep", action="store_true", help="keep the data from earlier runs (no clean start)")
    parser.add_argument("--reset", action="store_true", help="only empty the app's data, then stop")
    args = parser.parse_args()
    BASE_URL = args.url.rstrip("/")

    if args.list:
        for tid, kind, name, given, expected, _ in TEST_CASES:
            print(f"{tid}  {kind:<9} {name:<28} {given:<36} -> {expected}")
        return 0

    wanted = set()
    for item in args.tests:
        first, _, last = item.upper().partition("-")  # "TC01-TC13" is a range
        ids = [tc[0] for tc in TEST_CASES]
        if last and first in ids and last in ids:
            wanted.update(ids[ids.index(first):ids.index(last) + 1])
        else:
            wanted.add(item.upper())
    selected = [tc for tc in TEST_CASES
                if (not wanted or tc[0] in wanted) and (not args.type or tc[1].lower() == args.type)]
    if not selected:
        asked = " ".join(args.tests + ([f"--type {args.type}"] if args.type else []))
        print(f"{RED}No test case matches {asked}. Use --list to see them.{RESET}")
        return 1
    if not app_is_running():
        print(f"{RED}The Hospital Management System is not running at {BASE_URL}.{RESET}")
        print(f"Start it first in another terminal:   {BOLD}python app.py{RESET}")
        return 1
    if args.reset:
        return 0 if reset_app_data() else 1

    speed = 0 if args.fast else 1
    print(f"{BOLD}Selenium WebDriver live demo{RESET} - testing {BASE_URL}")
    if not args.keep:
        reset_app_data()
    print(f"{GREY}Launch the browser:  driver = webdriver.Chrome(){RESET}")
    driver = open_browser()
    print(f"{YELLOW}A new Chrome window opened. Selenium controls it - do not close it.{RESET}")
    if args.step:
        show_start_page(f"{selected[0][0]} {selected[0][2]}")
    results = []
    started = time.time()
    try:
        for tid, kind, name, given, expected, function in selected:
            if args.step:
                wait_for_enter(f"Press Enter to run {tid} - {name} ...")
            make_sure_browser_is_open()
            status, seconds, reason = run_test(tid, kind, name, given, expected, function)
            results.append((tid, kind, name, status, seconds, given, expected, reason))
        total = time.time() - started

        passed = sum(1 for r in results if r[3] == "PASS")
        failed = len(results) - passed
        colour = GREEN if not failed else RED
        print(f"\n{BOLD}{'=' * 64}\n SUMMARY{RESET}")
        for tid, kind, name, status, seconds, *_ in results:
            mark = f"{GREEN}PASS{RESET}" if status == "PASS" else f"{RED}FAIL{RESET}"
            print(f"   {tid}  {name:<30} {mark}  {GREY}{seconds:5.1f} s{RESET}")
        print(f"{colour}{BOLD}\n   {passed} passed, {failed} failed  in {total:.0f} s{RESET}")
        make_sure_browser_is_open()
        show_results_page(results, total)
        wait_for_enter("Press Enter to close the browser ...")
        return 0 if not failed else 1
    finally:
        print(f"{GREY}Close the browser:   driver.quit(){RESET}")
        try:
            driver.quit()  # last step: close the browser
        except WebDriverException:
            pass  # it was already closed


if __name__ == "__main__":
    sys.exit(main())
