"""
Runs ALL 122 automated tests and opens the HTML test report in the browser.

    python report.py

  85 PyTest tests  (unit, integration, functional - no browser)
+ 37 Selenium tests (Chrome opens and runs them)

It is the same as:  python -m pytest --html=report.html --self-contained-html
You do not need the app running: the tests start their own copy with an empty database.
"""
import pathlib
import sys
import webbrowser

import pytest

REPORT = pathlib.Path(__file__).resolve().with_name("report.html")

exit_code = pytest.main(["--html", str(REPORT), "--self-contained-html"])
print(f"\nTest report: {REPORT}")
webbrowser.open(REPORT.as_uri())
sys.exit(exit_code)
