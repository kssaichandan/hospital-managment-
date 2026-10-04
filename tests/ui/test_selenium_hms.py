"""
SELENIUM WEBDRIVER TESTS - Hospital Management System

TC01 - TC09 are exactly the test cases listed in the project document:

  Test Case                   Input                       Expected Result
  TC01 Login valid details    Correct username/password   Login successful
  TC02 Login invalid details  Wrong password              Error message displayed
  TC03 Add patient            Valid patient details       Patient added
  TC04 Empty patient form     Empty fields                Validation message
  TC05 Book appointment       Valid doctor/date           Appointment booked
  TC06 Search patient         Patient ID                  Patient details displayed
  TC07 Update patient         Modified details            Details updated
  TC08 Delete patient         Existing patient            Patient removed
  TC09 Logout                 Click Logout                User returned to login page

TC10 - TC13 are extra tests for the other modules.

Every test follows the Selenium workflow from the document:
Launch browser -> Open HMS -> Locate elements -> Perform actions -> Submit -> Verify result
"""
from datetime import date, timedelta

from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

TOMORROW = (date.today() + timedelta(days=1)).isoformat()


# ---------------- helper steps (re-used by many tests) ----------------
def click_and_wait(driver, element_id):
    """Click a submit button and wait until the next page has loaded."""
    button = driver.find_element(By.ID, element_id)
    button.click()
    # While the page is changing, Chrome can briefly report odd errors - just check again
    wait = WebDriverWait(driver, 10, ignored_exceptions=[WebDriverException])
    wait.until(EC.staleness_of(button))


def login(driver, base_url, username="admin", password="admin123"):
    driver.get(base_url)
    driver.find_element(By.ID, "username").send_keys(username)
    driver.find_element(By.ID, "password").send_keys(password)
    click_and_wait(driver, "login")


def add_patient(driver, base_url, name="Ravi Teja", age="30", phone="9876543210",
                disease="Fever"):
    driver.get(base_url + "/patients")
    driver.find_element(By.ID, "patient-name").send_keys(name)
    driver.find_element(By.ID, "patient-age").send_keys(age)
    Select(driver.find_element(By.ID, "patient-gender")).select_by_visible_text("Male")
    driver.find_element(By.ID, "patient-phone").send_keys(phone)
    driver.find_element(By.ID, "patient-disease").send_keys(disease)
    click_and_wait(driver, "add-patient-btn")


def add_doctor(driver, base_url, name="Dr. Priya Sharma", specialization="Pediatrician"):
    driver.get(base_url + "/doctors")
    driver.find_element(By.ID, "doctor-name").send_keys(name)
    driver.find_element(By.ID, "doctor-specialization").send_keys(specialization)
    driver.find_element(By.ID, "doctor-phone").send_keys("9876501234")
    driver.find_element(By.ID, "doctor-fee").send_keys("400")
    click_and_wait(driver, "add-doctor-btn")


def book_appointment(driver, base_url, patient, doctor_index=1, day=TOMORROW, time="10:00"):
    driver.get(base_url + "/appointments")
    Select(driver.find_element(By.ID, "appt-patient")).select_by_visible_text(patient)
    Select(driver.find_element(By.ID, "appt-doctor")).select_by_index(doctor_index)
    # Date pickers look different in every country, so we set the value directly
    date_box = driver.find_element(By.ID, "appt-date")
    driver.execute_script("arguments[0].value = arguments[1];", date_box, day)
    Select(driver.find_element(By.ID, "appt-time")).select_by_visible_text(time)
    click_and_wait(driver, "book-btn")


def success_message(driver):
    return driver.find_element(By.ID, "flash-success").text


def error_message(driver):
    return driver.find_element(By.ID, "flash-error").text


def table_text(driver, table_id):
    return driver.find_element(By.ID, table_id).text


# ---------------- TC01 - TC09 : test cases from the project document ----------------
def test_TC01_login_with_valid_details(driver, live_server):
    login(driver, live_server, "admin", "admin123")
    assert "/dashboard" in driver.current_url
    assert "Login successful" in success_message(driver)
    assert driver.find_element(By.TAG_NAME, "h1").text == "Dashboard"


def test_TC02_login_with_invalid_details(driver, live_server):
    login(driver, live_server, "admin", "wrongpassword")
    assert "Invalid username or password" in error_message(driver)
    assert "/dashboard" not in driver.current_url


def test_TC03_add_patient_with_valid_details(driver, live_server):
    login(driver, live_server)
    add_patient(driver, live_server, name="Ravi Teja")
    assert "Patient added successfully" in success_message(driver)
    assert "Ravi Teja" in table_text(driver, "patients-table")


def test_TC04_empty_patient_form_shows_validation_message(driver, live_server):
    login(driver, live_server)
    driver.get(live_server + "/patients")
    click_and_wait(driver, "add-patient-btn")  # submit with every field empty
    assert "Name must have at least 2 characters" in error_message(driver)
    assert "No patients found" in table_text(driver, "patients-table")


def test_TC05_book_appointment_with_valid_doctor_and_date(driver, live_server):
    login(driver, live_server)
    add_patient(driver, live_server, name="Ravi Teja")
    add_doctor(driver, live_server, name="Dr. Priya Sharma")
    book_appointment(driver, live_server, patient="Ravi Teja", day=TOMORROW, time="10:00")
    assert "Appointment booked successfully" in success_message(driver)
    table = table_text(driver, "appointments-table")
    assert "Dr. Priya Sharma" in table and TOMORROW in table and "Scheduled" in table


def test_TC06_search_patient_by_id(driver, live_server):
    login(driver, live_server)
    add_patient(driver, live_server, name="Ravi Teja")
    add_patient(driver, live_server, name="Sita Devi", phone="9123456789", disease="Cough")
    driver.find_element(By.ID, "search-box").send_keys("2")  # Patient ID of Sita Devi
    click_and_wait(driver, "search-btn")
    table = table_text(driver, "patients-table")
    assert "Sita Devi" in table and "Cough" in table
    assert "Ravi Teja" not in table


def test_TC07_update_patient_details(driver, live_server):
    login(driver, live_server)
    add_patient(driver, live_server, name="Ravi Teja", disease="Fever")
    click_and_wait(driver, "edit-patient-1")
    disease_box = driver.find_element(By.ID, "patient-disease")
    disease_box.clear()
    disease_box.send_keys("Typhoid")
    click_and_wait(driver, "update-patient-btn")
    assert "Patient details updated successfully" in success_message(driver)
    assert "Typhoid" in table_text(driver, "patients-table")


def test_TC08_delete_existing_patient(driver, live_server):
    login(driver, live_server)
    add_patient(driver, live_server, name="Ravi Teja")
    click_and_wait(driver, "delete-patient-1")
    assert "Patient removed successfully" in success_message(driver)
    assert "Ravi Teja" not in table_text(driver, "patients-table")


def test_TC09_logout_returns_to_login_page(driver, live_server):
    login(driver, live_server)
    click_and_wait(driver, "nav-logout")
    assert "You have been logged out" in success_message(driver)
    assert driver.find_element(By.ID, "login").is_displayed()
    # After logout the dashboard must not open without logging in again
    driver.get(live_server + "/dashboard")
    assert "Please log in first" in error_message(driver)


# ---------------- TC10 - TC13 : extra tests for other modules ----------------
def test_TC10_add_doctor_and_mark_unavailable(driver, live_server):
    login(driver, live_server)
    add_doctor(driver, live_server, name="Dr. Anil Reddy", specialization="Orthopedic")
    assert "Doctor added successfully" in success_message(driver)
    click_and_wait(driver, "toggle-doctor-1")
    assert "Not Available" in table_text(driver, "doctors-table")


def test_TC11_doctor_cannot_be_double_booked(driver, live_server):
    login(driver, live_server)
    add_patient(driver, live_server, name="Ravi Teja")
    add_patient(driver, live_server, name="Sita Devi", phone="9123456789")
    add_doctor(driver, live_server)
    book_appointment(driver, live_server, patient="Ravi Teja", time="11:00")
    book_appointment(driver, live_server, patient="Sita Devi", time="11:00")  # same slot
    assert "already booked" in error_message(driver)


def test_TC12_add_medical_record(driver, live_server):
    login(driver, live_server)
    add_patient(driver, live_server, name="Ravi Teja")
    driver.get(live_server + "/records")
    Select(driver.find_element(By.ID, "record-patient")).select_by_visible_text("Ravi Teja")
    driver.find_element(By.ID, "record-diagnosis").send_keys("Viral fever")
    driver.find_element(By.ID, "record-treatment").send_keys("Rest and fluids")
    driver.find_element(By.ID, "record-prescription").send_keys("Paracetamol 500mg")
    click_and_wait(driver, "add-record-btn")
    assert "Medical record saved successfully" in success_message(driver)
    assert "Viral fever" in table_text(driver, "records-table")


def test_TC13_generate_bill_calculates_total(driver, live_server):
    login(driver, live_server)
    add_patient(driver, live_server, name="Ravi Teja")
    driver.get(live_server + "/billing")
    Select(driver.find_element(By.ID, "bill-patient")).select_by_visible_text("Ravi Teja")
    driver.find_element(By.ID, "bill-consultation").send_keys("500")
    driver.find_element(By.ID, "bill-treatment").send_keys("1200")
    click_and_wait(driver, "create-bill-btn")
    assert "Bill generated successfully" in success_message(driver)
    assert driver.find_element(By.ID, "bill-total-1").text == "1700.00"  # 500 + 1200
