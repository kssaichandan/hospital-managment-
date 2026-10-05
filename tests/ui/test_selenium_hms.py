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

TC14 - TC37 are NEGATIVE, BOUNDARY / EDGE and SECURITY test cases:
  Negative  - wrong or missing input: the app must show an error and save nothing
  Boundary  - values exactly at or just outside a limit (age 0 / 120 / 121, phone 10 / 11 digits)
  Edge      - unusual but valid situations (decimal amounts, re-booking a cancelled slot)
  Security  - SQL injection, script injection (XSS), opening pages without logging in

Summary of all 37: 10 positive, 17 negative, 7 boundary / edge, 3 security.

Every test follows the Selenium workflow from the document:
Launch browser -> Open HMS -> Locate elements -> Perform actions -> Submit -> Verify result
"""
from datetime import date, timedelta

from selenium.common.exceptions import NoAlertPresentException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

TOMORROW = (date.today() + timedelta(days=1)).isoformat()
YESTERDAY = (date.today() - timedelta(days=1)).isoformat()


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


def add_doctor(driver, base_url, name="Dr. Priya Sharma", specialization="Pediatrician",
               phone="9876501234", fee="400"):
    driver.get(base_url + "/doctors")
    driver.find_element(By.ID, "doctor-name").send_keys(name)
    driver.find_element(By.ID, "doctor-specialization").send_keys(specialization)
    driver.find_element(By.ID, "doctor-phone").send_keys(phone)
    driver.find_element(By.ID, "doctor-fee").send_keys(fee)
    click_and_wait(driver, "add-doctor-btn")


def book_appointment(driver, base_url, patient, doctor_index=1, day=TOMORROW, time="10:00"):
    driver.get(base_url + "/appointments")
    Select(driver.find_element(By.ID, "appt-patient")).select_by_visible_text(patient)
    Select(driver.find_element(By.ID, "appt-doctor")).select_by_index(doctor_index)
    set_date(driver, "appt-date", day)
    Select(driver.find_element(By.ID, "appt-time")).select_by_visible_text(time)
    click_and_wait(driver, "book-btn")


def set_date(driver, element_id, day):
    # Date pickers look different in every country, so we set the value directly
    date_box = driver.find_element(By.ID, element_id)
    driver.execute_script("arguments[0].value = arguments[1];", date_box, day)


def add_bill(driver, base_url, patient, consultation, treatment):
    driver.get(base_url + "/billing")
    Select(driver.find_element(By.ID, "bill-patient")).select_by_visible_text(patient)
    driver.find_element(By.ID, "bill-consultation").send_keys(consultation)
    driver.find_element(By.ID, "bill-treatment").send_keys(treatment)
    click_and_wait(driver, "create-bill-btn")


def add_record(driver, base_url, patient, diagnosis, treatment, prescription, day=None):
    driver.get(base_url + "/records")
    Select(driver.find_element(By.ID, "record-patient")).select_by_visible_text(patient)
    if day:
        set_date(driver, "record-date", day)
    driver.find_element(By.ID, "record-diagnosis").send_keys(diagnosis)
    driver.find_element(By.ID, "record-treatment").send_keys(treatment)
    driver.find_element(By.ID, "record-prescription").send_keys(prescription)
    click_and_wait(driver, "add-record-btn")


def cell_text(driver, row_id, column):
    """Text of one cell in a table row (column 0 is the first column)."""
    row = driver.find_element(By.ID, row_id)
    return row.find_elements(By.TAG_NAME, "td")[column].text


def alert_is_open(driver):
    """True if a JavaScript pop-up (alert) is open - that would mean a script ran."""
    try:
        driver.switch_to.alert
        return True
    except NoAlertPresentException:
        return False


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


# =====================================================================
#  TC14 - TC37 : NEGATIVE, BOUNDARY / EDGE and SECURITY test cases
# =====================================================================

# ---------------- Login ----------------
def test_TC14_login_with_wrong_username(driver, live_server):  # Negative
    login(driver, live_server, "doctor", "admin123")
    assert "Invalid username or password" in error_message(driver)
    assert "/dashboard" not in driver.current_url


def test_TC15_login_with_empty_fields(driver, live_server):  # Negative
    login(driver, live_server, "", "")
    assert "Invalid username or password" in error_message(driver)
    assert "/dashboard" not in driver.current_url


def test_TC16_sql_injection_in_login_is_blocked(driver, live_server):  # Security
    # A classic attack: these inputs log in on a badly written website
    login(driver, live_server, "admin' --", "' OR '1'='1")
    assert "Invalid username or password" in error_message(driver)
    assert "/dashboard" not in driver.current_url


def test_TC17_pages_cannot_be_opened_without_login(driver, live_server):  # Security
    driver.get(live_server + "/patients")  # type the address directly, without logging in
    assert driver.current_url == live_server + "/"  # sent back to the login page
    assert "Please log in first" in error_message(driver)
    assert not driver.find_elements(By.ID, "patients-table")


# ---------------- Patients ----------------
def test_TC18_patient_phone_with_5_digits_is_rejected(driver, live_server):  # Negative
    login(driver, live_server)
    add_patient(driver, live_server, name="Ravi Teja", phone="12345")
    assert "Phone number must be exactly 10 digits" in error_message(driver)
    assert "No patients found" in table_text(driver, "patients-table")


def test_TC19_patient_phone_with_11_digits_is_rejected(driver, live_server):  # Boundary
    login(driver, live_server)
    add_patient(driver, live_server, name="Ravi Teja", phone="98765432101")  # one digit too many
    assert "Phone number must be exactly 10 digits" in error_message(driver)
    assert "No patients found" in table_text(driver, "patients-table")


def test_TC20_patient_name_with_numbers_is_rejected(driver, live_server):  # Negative
    login(driver, live_server)
    add_patient(driver, live_server, name="Ravi123")
    assert "Name can only contain letters" in error_message(driver)
    assert "No patients found" in table_text(driver, "patients-table")


def test_TC21_patient_age_121_is_rejected(driver, live_server):  # Boundary (just above 120)
    login(driver, live_server)
    add_patient(driver, live_server, name="Ravi Teja", age="121")
    assert "Age must be between 0 and 120" in error_message(driver)
    assert "No patients found" in table_text(driver, "patients-table")


def test_TC22_patient_age_0_and_120_are_accepted(driver, live_server):  # Boundary (the limits)
    login(driver, live_server)
    add_patient(driver, live_server, name="Baby Sharma", age="0", phone="9000000001")
    assert "Patient added successfully" in success_message(driver)
    add_patient(driver, live_server, name="Grandpa Rao", age="120", phone="9000000002")
    assert "Patient added successfully" in success_message(driver)
    assert cell_text(driver, "patient-row-1", column=2) == "0"    # Age column
    assert cell_text(driver, "patient-row-2", column=2) == "120"


def test_TC23_search_patient_id_that_does_not_exist(driver, live_server):  # Negative
    login(driver, live_server)
    add_patient(driver, live_server, name="Ravi Teja")
    driver.find_element(By.ID, "search-box").send_keys("99999")
    click_and_wait(driver, "search-btn")
    table = table_text(driver, "patients-table")
    assert "No patients found" in table
    assert "Ravi Teja" not in table


def test_TC24_invalid_update_keeps_old_patient_details(driver, live_server):  # Negative
    login(driver, live_server)
    add_patient(driver, live_server, name="Ravi Teja", phone="9876543210")
    click_and_wait(driver, "edit-patient-1")
    phone_box = driver.find_element(By.ID, "patient-phone")
    phone_box.clear()
    phone_box.send_keys("123")
    click_and_wait(driver, "update-patient-btn")
    assert "Phone number must be exactly 10 digits" in error_message(driver)
    driver.get(live_server + "/patients")
    assert "9876543210" in driver.find_element(By.ID, "patient-row-1").text  # old phone kept


def test_TC25_script_in_patient_form_is_shown_as_plain_text(driver, live_server):  # Security (XSS)
    login(driver, live_server)
    attack = "<script>alert('hacked')</script>"
    add_patient(driver, live_server, name="Ravi Teja", disease=attack)
    assert not alert_is_open(driver)  # the script did NOT run
    assert attack in table_text(driver, "patients-table")  # it is shown as normal text


# ---------------- Doctors ----------------
def test_TC26_doctor_fee_0_is_rejected(driver, live_server):  # Boundary
    login(driver, live_server)
    add_doctor(driver, live_server, fee="0")
    assert "Fee must be greater than 0" in error_message(driver)
    assert "No doctors found" in table_text(driver, "doctors-table")


def test_TC27_search_doctor_with_no_match(driver, live_server):  # Negative
    login(driver, live_server)
    add_doctor(driver, live_server, name="Dr. Priya Sharma", specialization="Pediatrician")
    driver.find_element(By.ID, "doctor-search-box").send_keys("Veterinarian")
    click_and_wait(driver, "doctor-search-btn")
    table = table_text(driver, "doctors-table")
    assert "No doctors found" in table
    assert "Dr. Priya Sharma" not in table


# ---------------- Appointments ----------------
def test_TC28_appointment_in_the_past_is_rejected(driver, live_server):  # Negative
    login(driver, live_server)
    add_patient(driver, live_server, name="Ravi Teja")
    add_doctor(driver, live_server)
    book_appointment(driver, live_server, patient="Ravi Teja", day=YESTERDAY)
    assert "Appointment date cannot be in the past" in error_message(driver)
    assert "No appointments yet" in table_text(driver, "appointments-table")


def test_TC29_appointment_without_patient_is_rejected(driver, live_server):  # Negative
    login(driver, live_server)
    add_doctor(driver, live_server)
    driver.get(live_server + "/appointments")
    # Patient is left as "Select patient"
    Select(driver.find_element(By.ID, "appt-doctor")).select_by_index(1)
    set_date(driver, "appt-date", TOMORROW)
    click_and_wait(driver, "book-btn")
    assert "Please select a valid patient" in error_message(driver)
    assert "No appointments yet" in table_text(driver, "appointments-table")


def test_TC30_unavailable_doctor_cannot_be_booked(driver, live_server):  # Negative
    login(driver, live_server)
    add_patient(driver, live_server, name="Ravi Teja")
    add_doctor(driver, live_server)
    click_and_wait(driver, "toggle-doctor-1")  # Mark Unavailable
    book_appointment(driver, live_server, patient="Ravi Teja")
    assert "This doctor is not available" in error_message(driver)
    assert "No appointments yet" in table_text(driver, "appointments-table")


def test_TC31_patient_cannot_see_two_doctors_at_same_time(driver, live_server):  # Negative
    login(driver, live_server)
    add_patient(driver, live_server, name="Ravi Teja")
    add_doctor(driver, live_server, name="Dr. Priya Sharma", specialization="Pediatrician")
    add_doctor(driver, live_server, name="Dr. Anil Reddy", specialization="Orthopedic",
               phone="9123456780")
    book_appointment(driver, live_server, patient="Ravi Teja", doctor_index=1, time="10:00")
    book_appointment(driver, live_server, patient="Ravi Teja", doctor_index=2, time="10:00")
    assert "This patient already has an appointment" in error_message(driver)


def test_TC32_cancelled_slot_can_be_booked_again(driver, live_server):  # Edge
    login(driver, live_server)
    add_patient(driver, live_server, name="Ravi Teja")
    add_doctor(driver, live_server)
    book_appointment(driver, live_server, patient="Ravi Teja", time="10:00")
    click_and_wait(driver, "cancel-appointment-1")
    book_appointment(driver, live_server, patient="Ravi Teja", time="10:00")  # same slot again
    assert "Appointment booked successfully" in success_message(driver)
    assert "Cancelled" in driver.find_element(By.ID, "appointment-row-1").text
    assert "Scheduled" in driver.find_element(By.ID, "appointment-row-2").text


# ---------------- Medical Records ----------------
def test_TC33_medical_record_without_diagnosis_is_rejected(driver, live_server):  # Negative
    login(driver, live_server)
    add_patient(driver, live_server, name="Ravi Teja")
    add_record(driver, live_server, "Ravi Teja", "", "Rest", "Paracetamol")
    assert "Diagnosis is required" in error_message(driver)
    assert "No medical records found" in table_text(driver, "records-table")


def test_TC34_medical_record_with_future_date_is_rejected(driver, live_server):  # Negative
    login(driver, live_server)
    add_patient(driver, live_server, name="Ravi Teja")
    add_record(driver, live_server, "Ravi Teja", "Viral fever", "Rest", "Paracetamol",
               day=TOMORROW)
    assert "Visit date cannot be in the future" in error_message(driver)
    assert "No medical records found" in table_text(driver, "records-table")


# ---------------- Billing ----------------
def test_TC35_bill_with_total_0_is_rejected(driver, live_server):  # Boundary
    login(driver, live_server)
    add_patient(driver, live_server, name="Ravi Teja")
    add_bill(driver, live_server, "Ravi Teja", "0", "0")
    assert "Total amount must be greater than 0" in error_message(driver)
    assert "No bills yet" in table_text(driver, "bills-table")


def test_TC36_negative_charge_is_rejected(driver, live_server):  # Negative
    login(driver, live_server)
    add_patient(driver, live_server, name="Ravi Teja")
    add_bill(driver, live_server, "Ravi Teja", "-100", "500")
    assert "Consultation charge cannot be negative" in error_message(driver)
    assert "No bills yet" in table_text(driver, "bills-table")


def test_TC37_bill_with_decimal_amounts(driver, live_server):  # Edge
    login(driver, live_server)
    add_patient(driver, live_server, name="Ravi Teja")
    add_bill(driver, live_server, "Ravi Teja", "499.50", "0.25")
    assert "Bill generated successfully" in success_message(driver)
    assert driver.find_element(By.ID, "bill-total-1").text == "499.75"  # 499.50 + 0.25
