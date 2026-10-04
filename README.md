# Hospital Management System – Software Testing using Selenium WebDriver

**M.Tech Software Engineering, SCORE (VIT) · Course: Software Testing**

| Name | Reg No |
|---|---|
| Arun C | 23MIS0445 |
| Sai Chandan K S | 23MIS0115 |

A simple web-based Hospital Management System (HMS), tested automatically with **Selenium WebDriver**.

- Presentation (9 slides, with speaker notes): [`presentation/Hospital_Management_System_Selenium_Testing.pptx`](presentation/Hospital_Management_System_Selenium_Testing.pptx)
- Test report: [`docs/test-report.html`](docs/test-report.html) (open it in a browser)
- Screenshots: [`docs/screenshots/`](docs/screenshots/)

---

## 1. Modules

| Module | Features |
|---|---|
| Login | Username/password, invalid-login message, logout, pages protected until you log in |
| Patient Management | Add, view, **update**, delete, **search by Patient ID or name** |
| Doctor Management | Add, view, update, search, **Available / Not Available** |
| Appointments | Select patient, doctor, date and time; book or cancel. A doctor **cannot be double-booked** |
| Medical Records | Diagnosis, treatment, prescription; full history for each patient |
| Billing | Consultation charge + treatment charge → **total calculated automatically**; Paid / Unpaid |

Demo login: **admin / admin123**

## 2. How to run (Windows / Mac / Linux)

You need **Python 3.9+** and **Google Chrome**.

```bash
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000 and log in with `admin` / `admin123`.
Three sample doctors are added automatically the first time you run it. Data is saved in `hospital.db`; delete that file to start fresh.

## 3. How to run the tests

```bash
# All 81 tests (13 Selenium + 68 PyTest). Chrome opens and runs the UI tests in front of you.
python -m pytest

# Only the Selenium tests (best for the live demo)
python -m pytest tests/ui

# Slow the Selenium tests down so the class can follow (1.5 s pause after each test)
#   Windows (PowerShell):  $env:DEMO_DELAY="1.5"; python -m pytest tests/ui
#   Mac / Linux:           DEMO_DELAY=1.5 python -m pytest tests/ui

# Generate the HTML test report
python -m pytest --html=docs/test-report.html --self-contained-html
```

You do **not** need the app running for `pytest`: the tests start their own copy of the app with an empty database.
Selenium 4 downloads the correct ChromeDriver automatically.

**The simple Selenium example from our document** (needs the app running in another terminal):

```bash
python app.py                    # terminal 1
python selenium_login_demo.py    # terminal 2  ->  "Login test PASSED - dashboard opened"
```

## 4. Selenium test cases

TC01–TC09 are exactly the test cases in our project document. File: `tests/ui/test_selenium_hms.py`

| ID | Test Case | Input | Expected Result | Result |
|---|---|---|---|---|
| TC01 | Login with valid details | Correct username/password | Login successful | PASS |
| TC02 | Login with invalid details | Wrong password | Error message displayed | PASS |
| TC03 | Add patient | Valid patient details | Patient added | PASS |
| TC04 | Empty patient form | Empty fields | Validation message | PASS |
| TC05 | Book appointment | Valid doctor/date | Appointment booked | PASS |
| TC06 | Search patient | Patient ID | Patient details displayed | PASS |
| TC07 | Update patient | Modified details | Details updated | PASS |
| TC08 | Delete patient | Existing patient | Patient removed | PASS |
| TC09 | Logout | Click Logout | User returned to login page | PASS |
| TC10 | Doctor availability | Mark doctor unavailable | Shows "Not Available" | PASS |
| TC11 | Double booking | Same doctor, date and time | Error "already booked" | PASS |
| TC12 | Medical record | Diagnosis, treatment, prescription | Record saved | PASS |
| TC13 | Billing total | 500 + 1200 | Total = 1700.00 | PASS |

Every Selenium test follows the workflow from our document:
**Launch browser → Open HMS → Locate elements → Perform actions → Submit → Verify result → Record result**

Besides Selenium, the project also has 68 PyTest tests at other testing levels:

| File | Level | What it checks |
|---|---|---|
| `tests/test_validators.py` | Unit | Each input rule on its own (phone 10 digits, age 0–120, dates, amounts…) |
| `tests/test_database.py` | Integration | Validation + SQLite database together |
| `tests/test_routes.py` | Functional | HTTP requests to every page, without a browser |
| `tests/ui/test_selenium_hms.py` | System / UI | Real Chrome browser controlled by Selenium |

## 5. Project structure

```
app.py                  Flask web app: all pages and routes
database.py             SQLite database: all create / read / update / delete operations
validators.py           Input validation rules (raise an error message when input is wrong)
templates/              HTML pages
static/style.css        Styling
selenium_login_demo.py  Simple Selenium login example (same as in our document)
tests/
  conftest.py           PyTest setup: fresh test database for every test
  test_validators.py    Unit tests
  test_database.py      Integration tests
  test_routes.py        Functional tests
  ui/conftest.py        Selenium setup: starts the app and opens Chrome
  ui/test_selenium_hms.py  Selenium test cases TC01–TC13
docs/                   Test report and screenshots
presentation/           PowerPoint presentation
```

## 6. Explaining the code (quick guide)

1. **User opens a page** → `app.py` has a function for every URL (`@app.route("/patients")`).
2. **User submits a form** → `app.py` calls `database.py`, e.g. `db.add_patient(...)`.
3. **Before saving**, `database.py` calls `validators.py`. If the phone is not 10 digits, a `ValueError("Phone number must be exactly 10 digits.")` is raised.
4. `app.py` catches the error and shows it in **red**; a success is shown in **green** (`run_action` function).
5. **Selenium** fills the same forms in Chrome, using each element's `id` (e.g. `By.ID, "patient-name"`), and **asserts** that the green or red message and the table show the expected result.

> Note: the example in our document is written in Java (`new ChromeDriver()`, `findElement`, `sendKeys`).
> We used **Python** Selenium. The commands are the same: `webdriver.Chrome()`, `find_element`, `send_keys`, `click`, `quit`.
