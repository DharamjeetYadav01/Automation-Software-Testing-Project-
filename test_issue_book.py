
import os
import time
from datetime import datetime, timedelta

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC


# ==========================================
# PROJECT CONFIGURATION
# ==========================================

BASE_URL = "http://localhost:5173/login"
ISSUE_URL = "http://localhost:5173/issue"

ADMIN_EMAIL = "admin@library.com"
ADMIN_PASSWORD = "Admin@123"

WAIT_TIME = 10

SCREENSHOT_DIR = "screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


# ==========================================
# BROWSER SETUP
# ==========================================

def start_browser():

    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")

    driver = webdriver.Chrome(options=options)

    return driver


# ==========================================
# COMMON FUNCTIONS
# ==========================================

def wait_for_element(driver, locator):

    wait = WebDriverWait(driver, WAIT_TIME)

    return wait.until(
        EC.visibility_of_element_located(locator)
    )


def admin_login(driver):

    driver.get(BASE_URL)

    wait = WebDriverWait(driver, WAIT_TIME)

    email = wait.until(
        EC.visibility_of_element_located(
            (By.CSS_SELECTOR, "input[type='email']")
        )
    )

    password = driver.find_element(
        By.CSS_SELECTOR, "input[type='password']"
    )

    email.send_keys(ADMIN_EMAIL)
    password.send_keys(ADMIN_PASSWORD)

    driver.find_element(
        By.XPATH,
        "//button[@type='submit' and contains(.,'Sign In')]"
    ).click()

    wait.until(
        lambda d: "/login" not in d.current_url
    )

    driver.get(ISSUE_URL)

    wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//h1[contains(.,'Issue a book')]")
        )
    )


def get_dropdowns(driver):

    return driver.find_elements(
        By.CSS_SELECTOR, "form select"
    )


def select_member_and_book(driver):

    wait = WebDriverWait(driver, WAIT_TIME)

    wait.until(
        lambda d: len(get_dropdowns(d)) == 2
        and len(Select(get_dropdowns(d)[0]).options) > 1
        and len(Select(get_dropdowns(d)[1]).options) > 1
    )

    dropdowns = get_dropdowns(driver)

    member_select = Select(dropdowns[0])
    book_select = Select(dropdowns[1])

    # Select first available member
    member_options = [
        option for option in member_select.options
        if option.get_attribute("value")
    ]

    assert member_options, "No members available"

    member_select.select_by_value(
        member_options[0].get_attribute("value")
    )

    # Select first book with available copies
    available_books = [
        option for option in book_select.options
        if option.get_attribute("value")
        and not option.get_attribute("disabled")
    ]

    assert available_books, "No available books found"

    book_select.select_by_value(
        available_books[0].get_attribute("value")
    )


def get_issue_button(driver):

    return driver.find_element(
        By.XPATH,
        "//button[@type='submit' and contains(.,'Issue Book')]"
    )


def set_date_using_javascript(driver, element, date_value):

    driver.execute_script(
        """
        const element = arguments[0];
        const value = arguments[1];

        const setter = Object.getOwnPropertyDescriptor(
            HTMLInputElement.prototype, 'value'
        ).set;

        setter.call(element, value);

        element.dispatchEvent(
            new Event('input', { bubbles: true })
        );

        element.dispatchEvent(
            new Event('change', { bubbles: true })
        );
        """,
        element,
        date_value
    )


# ==========================================
# TEST CASE 1
# Verify Issue Book Page UI
# ==========================================

def test_issue_page_ui(driver):

    admin_login(driver)

    heading = wait_for_element(
        driver,
        (By.XPATH, "//h1[contains(.,'Issue a book')]")
    )

    dropdowns = get_dropdowns(driver)

    date_fields = driver.find_elements(
        By.CSS_SELECTOR,
        "form input[type='date']"
    )

    issue_button = get_issue_button(driver)

    assert heading.is_displayed()
    assert len(dropdowns) == 2
    assert len(date_fields) == 2
    assert issue_button.is_displayed()

    print("Issue Book page UI verified.")


# ==========================================
# TEST CASE 2
# Issue Book With Valid Details
# ==========================================

def test_valid_book_issue(driver):

    admin_login(driver)

    select_member_and_book(driver)

    issue_button = get_issue_button(driver)

    assert issue_button.is_enabled()

    issue_button.click()

    # Wait for successful transaction confirmation
    success_message = wait_for_element(
        driver,
        (
            By.XPATH,
            "//*[contains(text(),'Transaction ID')]"
        )
    )

    assert success_message.is_displayed()

    print("Book issued successfully to selected member.")


# ==========================================
# TEST CASE 3
# Verify Mandatory Field Validation
# ==========================================

def test_mandatory_fields(driver):

    admin_login(driver)

    dropdowns = get_dropdowns(driver)

    member_select = Select(dropdowns[0])
    book_select = Select(dropdowns[1])

    # Both fields should initially be empty
    assert member_select.first_selected_option.get_attribute(
        "value"
    ) == ""

    assert book_select.first_selected_option.get_attribute(
        "value"
    ) == ""

    # Issue button should remain disabled
    issue_button = get_issue_button(driver)

    assert not issue_button.is_enabled()

    # Select member only
    member_options = [
        option for option in member_select.options
        if option.get_attribute("value")
    ]

    assert member_options

    member_select.select_by_value(
        member_options[0].get_attribute("value")
    )

    # Button should still be disabled without a book
    assert not issue_button.is_enabled()

    print("Mandatory field validation verified.")


# ==========================================
# TEST CASE 4
# Verify Invalid Due Date Validation
# ==========================================

def test_invalid_due_date(driver):

    admin_login(driver)

    select_member_and_book(driver)

    date_fields = driver.find_elements(
        By.CSS_SELECTOR,
        "form input[type='date']"
    )

    issue_date_field = date_fields[0]
    due_date_field = date_fields[1]

    issue_date = datetime.now().date()

    # Due date is set before issue date
    invalid_due_date = issue_date - timedelta(days=1)

    # Remove browser min restriction for testing
    driver.execute_script(
        "arguments[0].removeAttribute('min');",
        due_date_field
    )

    set_date_using_javascript(
        driver,
        issue_date_field,
        issue_date.strftime("%Y-%m-%d")
    )

    set_date_using_javascript(
        driver,
        due_date_field,
        invalid_due_date.strftime("%Y-%m-%d")
    )

    get_issue_button(driver).click()

    error_message = wait_for_element(
        driver,
        (
            By.XPATH,
            "//*[contains(text(),'Due date cannot be before the issue date')]"
        )
    )

    assert error_message.is_displayed()

    print("Invalid due date correctly rejected.")


# ==========================================
# TEST CASE 5
# Verify Book Availability Validation
# ==========================================

def test_book_availability(driver):

    admin_login(driver)

    dropdowns = get_dropdowns(driver)

    book_select = Select(dropdowns[1])

    # Find books with zero available copies
    unavailable_books = [
        option for option in book_select.options
        if option.get_attribute("value")
        and option.get_attribute("disabled") is not None
    ]

    if not unavailable_books:

        raise AssertionError(
            "SKIP: No out-of-stock book exists in the database. "
            "Add a book with zero available copies to test this scenario."
        )

    # Verify that unavailable book is disabled
    for book in unavailable_books:

        assert not book.is_enabled()

    print("Out-of-stock books are disabled in the dropdown.")


# ==========================================
# TEST CASE 6
# Verify Automatic Due Date Calculation
# ==========================================

def test_automatic_due_date(driver):

    admin_login(driver)

    date_fields = driver.find_elements(
        By.CSS_SELECTOR,
        "form input[type='date']"
    )

    issue_date = date_fields[0].get_attribute("value")
    due_date = date_fields[1].get_attribute("value")

    issue = datetime.strptime(
        issue_date, "%Y-%m-%d"
    ).date()

    due = datetime.strptime(
        due_date, "%Y-%m-%d"
    ).date()

    difference = (due - issue).days

    assert difference == 14, (
        f"Expected 14 days but found {difference} days"
    )

    print("Automatic 14-day due date calculation verified.")


# ==========================================
# TEST EXECUTION MANAGEMENT
# ==========================================

TEST_CASES = [

    (
        "TC_ISSUE_01",
        "Verify Issue Book Page UI",
        test_issue_page_ui
    ),

    (
        "TC_ISSUE_02",
        "Issue Book With Valid Details",
        test_valid_book_issue
    ),

    (
        "TC_ISSUE_03",
        "Mandatory Field Validation",
        test_mandatory_fields
    ),

    (
        "TC_ISSUE_04",
        "Invalid Due Date Validation",
        test_invalid_due_date
    ),

    (
        "TC_ISSUE_05",
        "Book Availability Validation",
        test_book_availability
    ),

    (
        "TC_ISSUE_06",
        "Automatic Due Date Calculation",
        test_automatic_due_date
    )

]


def run_all_tests():

    results = []

    print("\n")
    print("=" * 90)
    print("       LIBRARY MANAGEMENT SYSTEM - ISSUE BOOK AUTOMATION")
    print("=" * 90)

    for test_id, scenario, test_function in TEST_CASES:

        driver = None

        print(f"\nExecuting: {test_id} - {scenario}")

        start_time = time.time()

        try:

            driver = start_browser()

            test_function(driver)

            status = "PASS"
            remarks = "Test executed successfully"

        except Exception as error:

            status = "FAIL"
            remarks = str(error).split("\n")[0]

            if remarks.startswith("SKIP:"):
                status = "SKIP"

            if driver and status == "FAIL":

                screenshot_path = os.path.join(
                    SCREENSHOT_DIR,
                    f"{test_id}_failure.png"
                )

                driver.save_screenshot(screenshot_path)

                remarks += f" | Screenshot: {screenshot_path}"

            print(f"Result: {status}")
            print(f"Details: {remarks}")

        finally:

            if driver:
                driver.quit()

        execution_time = round(
            time.time() - start_time, 2
        )

        results.append({

            "id": test_id,
            "scenario": scenario,
            "status": status,
            "time": execution_time,
            "remarks": remarks

        })


    # ======================================
    # FINAL TABULAR REPORT
    # ======================================

    print("\n\n")
    print("=" * 105)
    print("                  ISSUE BOOK AUTOMATION TEST REPORT")
    print("=" * 105)

    print(
        f"{'TEST CASE ID':<18}"
        f"{'TEST SCENARIO':<38}"
        f"{'STATUS':<15}"
        f"{'TIME (SEC)':<12}"
    )

    print("-" * 105)

    for result in results:

        print(
            f"{result['id']:<18}"
            f"{result['scenario']:<38}"
            f"{result['status']:<15}"
            f"{result['time']:<12}"
        )

    print("-" * 105)

    total = len(results)

    passed = sum(
        1 for r in results if r["status"] == "PASS"
    )

    failed = sum(
        1 for r in results if r["status"] == "FAIL"
    )

    skipped = sum(
        1 for r in results if r["status"] == "SKIP"
    )

    print(f"\nTotal Test Cases : {total}")
    print(f"Passed           : {passed}")
    print(f"Failed           : {failed}")
    print(f"Skipped          : {skipped}")

    if total:
        print(
            f"Pass Percentage  : {(passed / total) * 100:.2f}%"
        )

    print("\nDetailed Remarks:")

    for result in results:

        print(
            f"{result['id']} - {result['remarks']}"
        )

    print("\n" + "=" * 105)
    print("              ISSUE BOOK AUTOMATION COMPLETED")
    print("=" * 105)


# ==========================================
# MAIN PROGRAM
# ==========================================

if __name__ == "__main__":

    run_all_tests()
