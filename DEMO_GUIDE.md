# Classroom Demo Guide

What to **do** and what to **say**, step by step. Total time: about 14 minutes.

## The 4 commands you need

| Command | What it does |
|---|---|
| `python app.py` | Starts our Hospital Management System (the software we test) |
| `python login.py` | Our first Selenium test: logs in by itself (10 lines of code) |
| `python run.py --step TC01-TC13` | Selenium tests the 13 main test cases, one by one, in front of the class |
| `python report.py` | Runs all 122 tests automatically and opens the test report |

Extra options for `run.py`:
`python run.py TC13` (only one test) · `python run.py TC14-TC20` (a range) ·
`python run.py --type negative` (only one type: positive, negative, boundary, edge, security) ·
`python run.py --fast` (no slow typing) · `python run.py --list` (list all 37 tests with their type)

---

## Before the class (10 minutes before)

1. Install once: `pip install -r requirements.txt`
2. **Do one practice run with internet on** (the first time, Selenium downloads ChromeDriver):
   `python app.py` in one terminal, `python run.py --fast` in another. All 37 must say PASS (about 1.5 minutes).
3. Stop the app (**Ctrl + C**) and **delete `hospital.db`**, so the app starts clean in class
   (it starts again with only 3 sample doctors).
4. Open the project in VS Code. Open `login.py` and `run.py` in tabs.
5. Open **two terminals side by side** in VS Code (Terminal → Split Terminal):
   - **Left = Terminal 1**: the app runs here. You will show its log.
   - **Right = Terminal 2**: the tests run here.
6. Make the text big so the class can read it: **Ctrl + =** in VS Code, **Ctrl + +** in Chrome.
7. Close other windows and turn off notifications.

---

## How it works behind (learn this, draw it on the board)

```
  run.py / login.py            our test code (Python)
        |
        |  Selenium commands: find_element, send_keys, click
        v
  ChromeDriver                 small program that Selenium starts by itself
        |
        |  WebDriver protocol (commands like "click this element")
        v
  Google Chrome                shows "Chrome is being controlled by automated test software"
        |
        |  normal web requests: GET (open a page), POST (submit a form)
        v
  Our HMS: app.py (Flask)  ->  validators.py (checks input)  ->  database.py  ->  hospital.db
        |
        |  page with a green (success) or red (error) message
        v
  Selenium reads the page  ->  check: is it what we expected?  ->  PASS / FAIL
```

**Where the class can SEE each part during the demo:**

| Part | Where you show it |
|---|---|
| Our test code | VS Code (`login.py`, `run.py`) |
| The Selenium commands that run | Terminal 2: the **grey lines** under every step |
| Chrome controlled by Selenium | The bar at the top of Chrome: *"Chrome is being controlled by automated test software"* |
| What Selenium found on the page | The **orange box** around the element |
| Requests reaching our app | Terminal 1: lines like `"GET /patients" 200` and `"POST /patients" 302` |
| Data saved in the database | Open the Patients page after the demo: Selenium's patients are still there |
| The result | Terminal 2: `CHECK PASSED` and `RESULT: PASS` |

Small words to know: **GET** = open a page. **POST** = submit a form. **200** = OK. **302** = "saved, now go to another page".

---

## The demo, step by step

### Step 1: Introduction (30 seconds)

**Say:**
> "Our project is a Hospital Management System. The main focus is software testing.
> First we will show the software. Then we will show how Selenium tests it automatically,
> just like a real user, and how it decides PASS or FAIL."

### Step 2: Show our software by hand (2 minutes)

**Do:**
1. Terminal 1: `python app.py`
2. Open Chrome: **http://127.0.0.1:5000**
3. Log in with `admin` / `admin123`. Show the Dashboard.
4. Patients: type a patient with phone `12345` and click **Add Patient**. A **red** message appears.
   Fix the phone to 10 digits (e.g. `9876543210`), fill the other fields again, add it: **green** message, patient in the table.
5. Click quickly through Doctors, Appointments, Medical Records, Billing
   (in Billing, type 500 and 1200: the total updates while you type).

**Say:**
> "This is our software. It has six modules. It checks every input: for example the phone
> must be exactly 10 digits, otherwise we get a red error message.
> Testing all of this by hand after every change takes a long time and people make mistakes.
> So we automate it with Selenium."

### Step 3: How Selenium works behind (2 minutes)

**Do:** Show the diagram above (draw it, or use slide 4).

**Say:**
> "Selenium is an open-source tool that controls a web browser from code.
> Our Python test calls Selenium commands like find_element, send_keys and click.
> Selenium sends these commands to ChromeDriver, a small helper program, and ChromeDriver
> controls Google Chrome. Chrome then talks to our app exactly like a normal user would:
> it opens pages and submits forms. At the end Selenium reads the page and our test
> checks if the result is what we expected. If yes: PASS. If not: FAIL."

### Step 4: How Selenium finds things on the page (1 minute)

**Do:** Log out. On the login page, right-click the **Username** box → **Inspect**.
Point at `id="username"`. Then point at the Login button: `id="login"`.

**Say:**
> "Every box and button in our app has an id. Selenium finds elements by this id,
> for example find_element(By.ID, "username"). This is called a locator.
> Selenium can also find elements by name, CSS selector or XPath, but id is the most reliable."

### Step 5: Our first Selenium test: `login.py` (2 minutes)

**Do:** Open `login.py` in VS Code and explain the lines:

| Line | Say |
|---|---|
| `driver = webdriver.Chrome()` | "This opens a new Chrome window that Selenium controls." |
| `driver.get("http://127.0.0.1:5000")` | "This opens our app." |
| `find_element(By.ID, "username").send_keys("admin")` | "Find the username box by its id and type admin." |
| `find_element(By.ID, "password").send_keys("admin123")` | "Same for the password." |
| `find_element(By.ID, "login").click()` | "Click the Login button." |
| `assert "/dashboard" in driver.current_url` | "**This is the actual test.** If the dashboard did not open, the test fails." |
| `driver.quit()` | "Close the browser." |

Then Terminal 2: `python login.py`

**Point at 3 things:**
1. Chrome opens and logs in **by itself**.
2. The bar *"Chrome is being controlled by automated test software"*.
3. **Terminal 1**: new lines appeared: `GET /`, then `POST /` with `302`, then `GET /dashboard`.

**Say:**
> "Look at Terminal 1: our app received a real login request. The app does not know it is
> Selenium. For the app it is just a user. That is why this is real system testing.
> Terminal 2 says Login test PASSED, because the assert was true."

### Step 6: Selenium tests every module: `run.py` (4 minutes)

**Do:** Terminal 2: `python run.py --step TC01-TC13`. It waits for **Enter** before each test case.

> **Two Chrome windows:** your own Chrome (from Step 2) stays open, and Selenium opens a **second,
> separate** Chrome window that says **"Selenium is ready"** and *"Chrome is being controlled by automated
> test software"*. That window belongs to Selenium: **do not close it and do not type in it.**
> Click on the terminal and press Enter; Selenium does everything in its own window.

**Explain what the class sees (do this during TC01):**
- **Orange box** in Chrome = the element Selenium just found.
- **Dark caption** at the bottom of Chrome = what Selenium is doing now.
- Terminal 2, white line with `>` = the step. **Grey line under it = the real Selenium command** that does it.
- Grey line with `->` = what Selenium **read** from the page, e.g. `.text -> "Login successful."`
- Green `✔ CHECK PASSED` = the expected result matched. Then `RESULT: PASS`.
- Grey `~ Setup:` lines = preparation (like logging in) done quickly, because it is not the point of that test.

**What to say for each test case (press Enter, then say the line):**

| Test | Say |
|---|---|
| TC01 Login valid | "Correct username and password. Expected: the dashboard opens with a green message." |
| TC02 Login invalid | "A **negative test**: wrong password. Expected: a red error, and we stay on the login page." |
| TC03 Add patient | "Selenium fills the patient form like a receptionist. It checks the green message and that Ravi Teja is in the table." |
| TC04 Empty form | "Negative test: submit an empty form. Expected: a validation message and nothing saved." |
| TC05 Book appointment | "Setup quickly adds a patient and a doctor. Then Selenium books tomorrow at 10:00 and checks it is Scheduled." |
| TC06 Search | "Search by Patient ID. Only that one patient must be shown." |
| TC07 Update | "Edit the disease from Fever to Typhoid, then check the table shows Typhoid." |
| TC08 Delete | "Delete the patient, then check the row is gone." |
| TC09 Logout | "Log out, then try to open the dashboard directly. It must be blocked: a security check." |
| TC10 Doctor availability | "Add a doctor, mark the doctor unavailable, check it shows Not Available." |
| TC11 Double booking | "A **business rule**: the same doctor at the same date and time for a second patient. The app must refuse." |
| TC12 Medical record | "Save a diagnosis, then open the patient's history and check it is there." |
| TC13 Billing | "500 + 1200. The app must calculate 1700.00. Selenium reads the total and compares it." |

At the end Chrome shows a **results page**: 13 passed, 0 failed. Press **Enter** to close Chrome.

**Short on time?** Run only the best ones: `python run.py TC01 TC02 TC04 TC11 TC13`

**Say at the end:**
> "13 test cases, all passed, and nobody touched the keyboard. Look at Terminal 1: every
> request Selenium made is there. And if we open the Patients page now, the patients Selenium
> added are saved in our database."

### Step 6b: Negative, boundary and security tests (2 minutes)

**Say first:**
> "Testing only valid input is not enough. Real users make mistakes and attackers try to break
> in. So we also have 17 **negative**, 7 **boundary / edge** and 3 **security** test cases,
> 37 in total. Here are the most interesting ones."

**Do:** Terminal 2: `python run.py --step TC16 TC21 TC22 TC25` (slide 7 shows all 24 of these tests)

| Test | Say |
|---|---|
| TC16 SQL injection | "A **security test**: a classic attack, `admin' --` as the username. On a badly written website this logs in without a password. Our app refuses it." |
| TC21 Age 121 | "**Boundary value analysis**: the limit is 120, so we test just above it. 121 must be rejected and not saved." |
| TC22 Age 0 and 120 | "And exactly at the limits: 0 and 120 must be accepted. Bugs often hide at the edges, like writing `<` instead of `<=`." |
| TC25 Script injection | "We type a `<script>` into the disease field. If the app were unsafe, a pop-up would appear. Selenium checks there is no pop-up and the text is shown as plain text." |

**Say at the end:**
> "For every negative test we check two things: the red error message is shown, **and** nothing
> was saved. An error message alone is not enough: the data must not reach the database."

Extra time? `python run.py TC31`: one patient cannot see two doctors at the same time. This was a real bug our testing found.
To show all negative tests: `python run.py --type negative` (17 tests, about 3 to 4 minutes).

### Step 7: Show a test that FAILS (1 minute)

**Do:**
1. In `run.py`, press **Ctrl + F** and search `total == "1700.00"` (inside `def tc13`).
2. Change **only** that `"1700.00"` to `"1800.00"`. Save (**Ctrl + S**).
3. Terminal 2: `python run.py TC13`
4. The caption turns **red**, Terminal 2 shows `✘ CHECK FAILED` and `RESULT: FAIL`.
   A screenshot is saved in the `demo_failures` folder; open it.
5. **Change it back to `"1700.00"` and save.**

**Say:**
> "Now we told the test to expect 1800, but the app correctly shows 1700. The test fails
> and saves a screenshot as proof. In real projects this is how automated tests catch bugs:
> when the result is different from what we expect, we know immediately."

### Step 8: Run everything automatically: `report.py` (2 minutes)

**Do:** Terminal 2: `python report.py`. Chrome opens and runs the 37 Selenium tests quickly.
After about 1.5 minutes, the **test report** opens in the browser: 122 passed.

**Say:**
> "In a real project nobody watches the tests slowly. One command runs all 122 tests in about
> 1.5 minutes and produces this report. We test at four levels:"

| Level | File | What it checks |
|---|---|---|
| Unit | `tests/test_validators.py` | Each input rule alone (phone, age, dates, amounts) |
| Integration | `tests/test_database.py` | Validation and database together |
| Functional | `tests/test_routes.py` | Every page through HTTP requests, without a browser |
| System / UI | `tests/ui/test_selenium_hms.py` | The full app in a real Chrome, with Selenium |

> "We run them again after every change. That is called **regression testing**."

### Step 9: Conclusion (30 seconds)

**Say:**
> "We built a Hospital Management System and tested it with Selenium WebDriver.
> All test cases from our document pass, for valid and invalid inputs. Our testing also found
> 9 real defects, for example typing 'nan' as a doctor's fee crashed the server. We fixed them
> and added a test for each one. Thank you. Any questions?"

---

## Questions the teacher may ask

**What is Selenium?**
An open-source tool to automate web browsers. We use Selenium WebDriver to control Chrome from Python code.

**What is ChromeDriver?**
A small program between Selenium and Chrome. Selenium sends a command ("click this button"), ChromeDriver makes Chrome do it. Selenium 4 downloads the right ChromeDriver by itself.

**What is a locator?**
How Selenium finds an element: `By.ID`, `By.NAME`, `By.CSS_SELECTOR`, `By.XPATH`, `By.CLASS_NAME`, `By.LINK_TEXT`. We use `By.ID` because ids are unique and do not change when the design changes.

**What is an assertion?**
The line that checks the expected result, e.g. `assert total == "1700.00"`. True = PASS, false = FAIL.

**What is the difference between `run.py` and the PyTest Selenium tests?**
Same 37 test cases. `run.py` is slow and shows every step, for a demo. `tests/ui/test_selenium_hms.py` is the real automated suite: fast, run by PyTest, uses its own empty database, makes the report.

**Why do you wait after clicking?**
After a click, the next page needs time to load. If Selenium checks too early, the test fails randomly (a **flaky test**). We use `WebDriverWait` to wait until the new page has loaded. This was defect #9 we found.

**Can it test other browsers?**
Yes: `webdriver.Firefox()` or `webdriver.Edge()`. Selenium Grid runs tests on many browsers and machines at once.

**Manual vs automated testing?**
Manual: a person clicks; slow, can make mistakes. Automated: code clicks; fast, same every time, can run after every change.

**Is this black-box or white-box testing?**
Selenium tests are **black-box**: they only use the screen, like a user, without looking at the code. Our unit tests are closer to white-box.

**Positive and negative tests?**
Positive: valid input, expect success (TC01, TC03). Negative: invalid input, expect an error **and nothing saved** (TC02, TC04, TC11, TC14–TC36). We have 10 positive, 17 negative, 7 boundary / edge and 3 security test cases.

**What is boundary value analysis?**
Bugs often hide at the limits. Age must be 0–120, so we test 0 and 120 (must pass) and 121 (must fail): TC21, TC22. Phone must be 10 digits, so we test 11 digits: TC19. A bill total of exactly 0 must fail: TC35.

**What is an edge case?**
An unusual but valid situation: booking a slot again after it was cancelled (TC32), or amounts with decimals like 499.50 + 0.25 (TC37).

**What security tests did you do?**
SQL injection in the login (TC16), script injection / XSS in a form (TC25), and opening pages without logging in (TC17, TC09).

**How do you know your tests really catch bugs?**
**Mutation testing**: we put 6 bugs into a copy of the app on purpose (for example, allow age 121 or make the login open to SQL injection). Every bug made its test fail. A test that never fails is useless.

**Why Python and not Java like in the document?**
The commands are the same: Java `findElement`/`sendKeys`, Python `find_element`/`send_keys`. Python is shorter to read.

---

## If something goes wrong

| Problem | Fix |
|---|---|
| `The Hospital Management System is not running` | Start `python app.py` in Terminal 1 first. |
| `invalid session id` / `The Selenium Chrome window was closed` | The Selenium window was closed. `run.py` opens a new one by itself for the next test. Don't close the window that says "Selenium is ready". |
| Port 5000 already in use | The app is already running in another terminal. Use that one, or close it with Ctrl + C. |
| Chrome does not open / driver error | The first run needs internet (Selenium downloads ChromeDriver). Do the practice run before class. |
| A test fails unexpectedly | Read the red line in Terminal 2 and open the screenshot in `demo_failures/`. Run it again with `python run.py TC05` (your test id). |
| Too much old data in the app | Ctrl + C in Terminal 1, delete `hospital.db`, run `python app.py` again. |
| Want to stop anything | **Ctrl + C** in that terminal. |
