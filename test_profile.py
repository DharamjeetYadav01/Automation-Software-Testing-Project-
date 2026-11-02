
import os
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# ==========================================
# PROJECT CONFIGURATION
# ==========================================

BASE_URL = "http://localhost:5173/login"
PROFILE_URL = "http://localhost:5173/profile"

ADMIN_EMAIL = "admin@library.com"
ADMIN_PASSWORD = "Admin@123"

TEMP_PASSWORD = "Admin@12345"

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
        By.CSS_SELECTOR,
        "input[type='password']"
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

    driver.get(PROFILE_URL)

    wait_for_element(
        driver,
        (By.XPATH, "//h1[contains(.,'Your profile')]")
    )


def get_password_fields(driver):

    return driver.find_elements(
        By.CSS_SELECTOR,
        "form input[type='password']"
    )


def get_update_button(driver):

    return driver.find_element(
        By.XPATH,
        "//button[@type='submit' and contains(.,'Update Password')]"
    )


def wait_for_toast(driver, message):

    return wait_for_element(
        driver,
        (
            By.XPATH,
            f"//*[normalize-space()='{message}']"
        )
    )


def fill_password_fields(driver, current, new):

    fields = get_password_fields(driver)

    assert len(fields) == 2, (
        "Expected two password fields"
    )

    fields[0].clear()
    fields[0].send_keys(current)

    fields[1].clear()
    fields[1].send_keys(new)


# ==========================================
# TEST CASE 1
# Verify Profile Page UI
# ==========================================

def test_profile_page_ui(driver):

    admin_login(driver)

    heading = wait_for_element(
        driver,
        (By.XPATH, "//h1[contains(.,'Your profile')]")
    )

    password_heading = driver.find_element(
        By.XPATH,
        "//*[contains(text(),'Change Password')]"
    )

    security_heading = driver.find_element(
        By.XPATH,
        "//*[contains(text(),'Account Security')]"
    )

    fields = get_password_fields(driver)

    update_button = get_update_button(driver)

    assert heading.is_displayed()
    assert password_heading.is_displayed()
    assert security_heading.is_displayed()

    assert len(fields) == 2

    assert update_button.is_displayed()

    print("Profile page UI verified successfully.")


# ==========================================
# TEST CASE 2
# Verify Profile Information
# ==========================================

def test_profile_information(driver):

    admin_login(driver)

    page_text = driver.find_element(
        By.TAG_NAME,
        "body"
    ).text

    assert "Library Admin" in page_text

    assert ADMIN_EMAIL in page_text

    assert "Administrator" in page_text

    assert "Password protected (bcrypt)" in page_text

    print("Admin profile information verified.")


# ==========================================
# TEST CASE 3
# Verify Account Statistics
# ==========================================

def test_account_statistics(driver):

    admin_login(driver)

    page_text = driver.find_element(
        By.TAG_NAME,
        "body"
    ).text

    assert "Total Books" in page_text

    assert "Total Members" in page_text

    assert "Outstanding Fines" in page_text

    # Verify that the statistics have loaded
    stat_values = driver.find_elements(
        By.XPATH,
        "//*[contains(text(),'Total Books') "
        "or contains(text(),'Total Members') "
        "or contains(text(),'Outstanding Fines')]"
    )

    assert len(stat_values) == 3

    print("Account statistics displayed successfully.")


# ==========================================
# TEST CASE 4
# Change Password with Valid Credentials
# ==========================================

def test_valid_password_change(driver):

    admin_login(driver)

    password_changed = False

    try:

        # Enter current and new password
        fill_password_fields(
            driver,
            ADMIN_PASSWORD,
            TEMP_PASSWORD
        )

        get_update_button(driver).click()

        # Verify successful password update
        success_message = wait_for_toast(
            driver,
            "Password updated successfully"
        )

        assert success_message.is_displayed()

        password_changed = True

        print("Password changed successfully.")

        # Restore original Admin password
        fill_password_fields(
            driver,
            TEMP_PASSWORD,
            ADMIN_PASSWORD
        )

        get_update_button(driver).click()

        restored_message = wait_for_toast(
            driver,
            "Password updated successfully"
        )

        assert restored_message.is_displayed()

        password_changed = False

        print("Original Admin password restored.")

    finally:

        # Safety recovery if the restoration step fails
        if password_changed:

            try:

                fill_password_fields(
                    driver,
                    TEMP_PASSWORD,
                    ADMIN_PASSWORD
                )

                get_update_button(driver).click()

                wait_for_toast(
                    driver,
                    "Password updated successfully"
                )

                print("Admin password restored through recovery.")

            except Exception:

                print(
                    "CRITICAL: Password restoration failed. "
                    "Check the Admin account before running "
                    "other automation tests."
                )

                raise


# ==========================================
# TEST CASE 5
# Change Password with Incorrect Current Password
# ==========================================

def test_invalid_current_password(driver):

    admin_login(driver)

    fill_password_fields(
        driver,
        "WrongCurrentPassword",
        "NewPassword123"
    )

    get_update_button(driver).click()

    error_message = wait_for_toast(
        driver,
        "Current password is incorrect"
    )

    assert error_message.is_displayed()

    print("Incorrect current password rejected successfully.")


# ==========================================
# TEST CASE 6
# Verify Quick Navigation Links
# ==========================================

def test_quick_navigation(driver):

    admin_login(driver)

    navigation_links = [

        ("Browse Books", "/books"),

        ("My Transactions", "/transactions"),

        ("Issue a Book", "/issue")

    ]

    for link_name, expected_path in navigation_links:

        link = wait_for_element(
            driver,
            (
                By.XPATH,
                f"//a[@href='{expected_path}' "
                f"and contains(.,'{link_name}')]"
            )
        )

        link.click()

        WebDriverWait(driver, WAIT_TIME).until(
            lambda d: d.current_url.endswith(expected_path)
        )

        assert driver.current_url.endswith(expected_path)

        print(f"{link_name} navigation verified.")

        # Return to Profile for the next link
        driver.get(PROFILE_URL)

        wait_for_element(
            driver,
            (By.XPATH, "//h1[contains(.,'Your profile')]")
        )


# ==========================================
# TEST EXECUTION MANAGEMENT
# ==========================================

TEST_CASES = [

    (
        "TC_PROFILE_01",
        "Verify Profile Page UI",
        test_profile_page_ui
    ),

    (
        "TC_PROFILE_02",
        "Verify Profile Information",
        test_profile_information
    ),

    (
        "TC_PROFILE_03",
        "Verify Account Statistics",
        test_account_statistics
    ),

    (
        "TC_PROFILE_04",
        "Valid Password Change",
        test_valid_password_change
    ),

    (
        "TC_PROFILE_05",
        "Invalid Current Password",
        test_invalid_current_password
    ),

    (
        "TC_PROFILE_06",
        "Quick Navigation Links",
        test_quick_navigation
    )

]


# ==========================================
# RUN ALL TEST CASES
# ==========================================

def run_all_tests():

    results = []

    print("\n")
    print("=" * 90)
    print("       LIBRARY MANAGEMENT SYSTEM - PROFILE AUTOMATION")
    print("=" * 90)

    # Run password update last to avoid affecting
    # subsequent login tests if restoration fails.
    execution_order = [
        TEST_CASES[0],
        TEST_CASES[1],
        TEST_CASES[2],
        TEST_CASES[4],
        TEST_CASES[5],
        TEST_CASES[3]
    ]

    for test_id, scenario, test_function in execution_order:

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

                remarks += (
                    f" | Screenshot: {screenshot_path}"
                )

            print(f"Error: {error}")

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

        print(f"Result: {status}")


    # ======================================
    # FINAL TABULAR REPORT
    # ======================================

    print("\n\n")

    print("=" * 105)

    print(
        "                 PROFILE AUTOMATION TEST EXECUTION REPORT"
    )

    print("=" * 105)

    print(
        f"{'TEST CASE ID':<20}"
        f"{'TEST SCENARIO':<38}"
        f"{'STATUS':<15}"
        f"{'TIME (SEC)':<12}"
    )

    print("-" * 105)

    # Display in original test case order
    results.sort(key=lambda x: x["id"])

    for result in results:

        print(
            f"{result['id']:<20}"
            f"{result['scenario']:<38}"
            f"{result['status']:<15}"
            f"{result['time']:<12}"
        )

    print("-" * 105)

    total = len(results)

    passed = sum(
        1 for r in results
        if r["status"] == "PASS"
    )

    failed = sum(
        1 for r in results
        if r["status"] == "FAIL"
    )

    print(f"\nTotal Test Cases : {total}")

    print(f"Passed           : {passed}")

    print(f"Failed           : {failed}")

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

    print(
        "                PROFILE AUTOMATION TESTING COMPLETED"
    )

    print("=" * 105)


# ==========================================
# MAIN PROGRAM
# ==========================================

if __name__ == "__main__":

    run_all_tests()
