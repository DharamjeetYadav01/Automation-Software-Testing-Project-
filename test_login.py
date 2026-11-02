print("LOGIN AUTOMATION SCRIPT STARTED")
import os
import time
import traceback

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# ==========================================
# PROJECT CONFIGURATION
# ==========================================

BASE_URL = "http://localhost:5173/login"

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

    driver.get(BASE_URL)

    return driver


# ==========================================
# COMMON FUNCTIONS
# ==========================================

def wait_for_element(driver, locator):

    wait = WebDriverWait(driver, WAIT_TIME)

    return wait.until(
        EC.visibility_of_element_located(locator)
    )


def get_error_message(driver):

    error = wait_for_element(
        driver,
        (
            By.XPATH,
            "//*[contains(@class,'border-rose-200') "
            "and contains(@class,'bg-rose-50')]"
        )
    )

    return error.text.strip()


def enter_credentials(driver, email, password):

    email_field = driver.find_element(
        By.CSS_SELECTOR,
        "input[type='email']"
    )

    password_field = driver.find_element(
        By.CSS_SELECTOR,
        "input[type='password']"
    )

    email_field.clear()
    email_field.send_keys(email)

    password_field.clear()
    password_field.send_keys(password)


def click_sign_in(driver):

    sign_in_button = driver.find_element(
        By.XPATH,
        "//button[@type='submit' and contains(., 'Sign In')]"
    )

    sign_in_button.click()


# ==========================================
# TEST CASE 1
# Verify Login Page UI
# ==========================================

def test_login_page_ui(driver):

    driver.get(BASE_URL)

    heading = wait_for_element(
        driver,
        (
            By.XPATH,
            "//h2[contains(text(),'Sign in to your library')]"
        )
    )

    email = driver.find_element(
        By.CSS_SELECTOR,
        "input[type='email']"
    )

    password = driver.find_element(
        By.CSS_SELECTOR,
        "input[type='password']"
    )

    sign_in = driver.find_element(
        By.XPATH,
        "//button[@type='submit' and contains(.,'Sign In')]"
    )

    assert heading.is_displayed()
    assert email.is_displayed()
    assert password.is_displayed()
    assert sign_in.is_displayed()


# ==========================================
# TEST CASE 2
# Login with Valid Admin Credentials
# ==========================================

def test_valid_admin_login(driver):

    driver.get(BASE_URL)

    enter_credentials(
        driver,
        ADMIN_EMAIL,
        ADMIN_PASSWORD
    )

    click_sign_in(driver)

    wait = WebDriverWait(driver, WAIT_TIME)

    wait.until(
        lambda d: "/login" not in d.current_url
    )

    assert "/login" not in driver.current_url

    print("Admin login successful.")


# ==========================================
# TEST CASE 3
# Login with Invalid Credentials
# ==========================================

def test_invalid_admin_login(driver):

    driver.get(BASE_URL)

    enter_credentials(
        driver,
        ADMIN_EMAIL,
        "WrongPassword123"
    )

    click_sign_in(driver)

    error_message = get_error_message(driver)

    assert error_message != ""

    assert "/login" in driver.current_url

    print("Invalid login correctly rejected.")


# ==========================================
# TEST CASE 4
# Login with Empty Fields
# ==========================================

def test_empty_login_fields(driver):

    driver.get(BASE_URL)

    click_sign_in(driver)

    error_message = get_error_message(driver)

    assert "Please enter your email and password" in error_message

    assert "/login" in driver.current_url

    print("Empty field validation working correctly.")


# ==========================================
# TEST CASE 5
# Verify Password Masking
# ==========================================

def test_password_masking(driver):

    driver.get(BASE_URL)

    password_field = driver.find_element(
        By.CSS_SELECTOR,
        "input[type='password']"
    )

    password_field.send_keys("Admin@123")

    assert password_field.get_attribute("type") == "password"

    assert password_field.get_attribute("value") == "Admin@123"

    print("Password masking verified.")


# ==========================================
# TEST CASE 6
# Verify Admin Demo Credentials
# ==========================================

def test_admin_demo_credentials(driver):

    driver.get(BASE_URL)

    admin_demo_button = driver.find_element(
        By.XPATH,
        "//button[contains(.,'Librarian / Admin')]"
    )

    admin_demo_button.click()

    email_field = driver.find_element(
        By.CSS_SELECTOR,
        "input[type='email']"
    )

    password_field = driver.find_element(
        By.CSS_SELECTOR,
        "input[type='password']"
    )

    assert email_field.get_attribute("value") == ADMIN_EMAIL

    assert password_field.get_attribute("value") == ADMIN_PASSWORD

    print("Admin demo credentials populated correctly.")


# ==========================================
# TEST EXECUTION AND RESULT MANAGEMENT
# ==========================================

TEST_CASES = [

    (
        "TC_LOGIN_01",
        "Verify Login Page UI",
        test_login_page_ui
    ),

    (
        "TC_LOGIN_02",
        "Valid Admin Login",
        test_valid_admin_login
    ),

    (
        "TC_LOGIN_03",
        "Invalid Admin Login",
        test_invalid_admin_login
    ),

    (
        "TC_LOGIN_04",
        "Empty Login Fields",
        test_empty_login_fields
    ),

    (
        "TC_LOGIN_05",
        "Password Masking",
        test_password_masking
    ),

    (
        "TC_LOGIN_06",
        "Admin Demo Credentials",
        test_admin_demo_credentials
    )

]


def run_all_tests():

    results = []

    print("\n")
    print("=" * 85)
    print("       LIBRARY MANAGEMENT SYSTEM - LOGIN AUTOMATION TESTING")
    print("=" * 85)

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

            if driver:
                screenshot_path = os.path.join(
                    SCREENSHOT_DIR,
                    f"{test_id}_failure.png"
                )

                driver.save_screenshot(screenshot_path)

                remarks = f"{remarks} | Screenshot: {screenshot_path}"

            print(f"Error: {error}")

        finally:

            if driver:
                driver.quit()

        execution_time = round(time.time() - start_time, 2)

        results.append({

            "id": test_id,
            "scenario": scenario,
            "status": status,
            "time": execution_time,
            "remarks": remarks

        })

        print(f"Result: {status}")


    # ======================================
    # DISPLAY FINAL TABULAR REPORT
    # ======================================

    print("\n\n")
    print("=" * 110)
    print("                         AUTOMATION TEST EXECUTION REPORT")
    print("=" * 110)

    headers = [
        "TEST CASE ID",
        "TEST SCENARIO",
        "STATUS",
        "TIME (SEC)"
    ]

    print(
        f"{headers[0]:<18}"
        f"{headers[1]:<38}"
        f"{headers[2]:<15}"
        f"{headers[3]:<12}"
    )

    print("-" * 110)

    for result in results:

        print(
            f"{result['id']:<18}"
            f"{result['scenario']:<38}"
            f"{result['status']:<15}"
            f"{result['time']:<12}"
        )

    print("-" * 110)

    total = len(results)

    passed = sum(
        1 for result in results
        if result["status"] == "PASS"
    )

    failed = total - passed

    print(f"\nTotal Test Cases : {total}")
    print(f"Passed           : {passed}")
    print(f"Failed           : {failed}")

    if total:
        pass_percentage = (passed / total) * 100
        print(f"Pass Percentage  : {pass_percentage:.2f}%")

    print("\nDetailed Remarks:")

    for result in results:

        print(
            f"{result['id']} - {result['remarks']}"
        )

    print("\n" + "=" * 110)
    print("                  LOGIN AUTOMATION TESTING COMPLETED")
    print("=" * 110)


# ==========================================
# MAIN PROGRAM
# ==========================================

if __name__ == "__main__":

    run_all_tests()
