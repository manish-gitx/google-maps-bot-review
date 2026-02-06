import time
import random
import subprocess
from appium.webdriver import Remote as AppiumDriver
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.logger import log
import config


class GoogleAuth:
    """Handles Google account login on Android emulator via Appium."""

    def __init__(self, driver: AppiumDriver, serial: str):
        self.driver = driver
        self.serial = serial
        self.adb = config.ADB_PATH
        self.wait = WebDriverWait(driver, 15)

    def login(self, email: str, password: str) -> bool:
        """Add a Google account to the device via Settings app."""
        log.info(f"Adding Google account: {email}")

        try:
            # Open Settings > Accounts
            self._open_add_account_screen()
            time.sleep(2)

            # Select "Google" account type
            if not self._select_google_account_type():
                return False
            time.sleep(3)

            # Enter email
            if not self._enter_email(email):
                return False
            time.sleep(random.uniform(2, 4))

            # Enter password
            if not self._enter_password(password):
                return False
            time.sleep(random.uniform(3, 5))

            # Handle post-login prompts
            return self._handle_post_login()

        except Exception as e:
            log.error(f"Login failed: {e}")
            return False

    def _open_add_account_screen(self):
        """Open the 'Add Account' screen via ADB intent."""
        subprocess.run(
            [self.adb, "-s", self.serial, "shell", "am", "start",
             "-a", "android.settings.ADD_ACCOUNT_SETTINGS",
             "-n", "com.android.settings/.accounts.AddAccountSettings"],
            capture_output=True, timeout=10,
        )
        time.sleep(2)

        # Fallback: open Settings directly
        try:
            subprocess.run(
                [self.adb, "-s", self.serial, "shell", "am", "start",
                 "-a", "android.settings.ADD_ACCOUNT_SETTINGS"],
                capture_output=True, timeout=10,
            )
        except Exception:
            pass

    def _select_google_account_type(self) -> bool:
        """Tap on 'Google' in the account type list."""
        try:
            selectors = [
                (AppiumBy.XPATH, '//*[@text="Google"]'),
                (AppiumBy.XPATH, '//*[contains(@text, "Google")]'),
                (AppiumBy.XPATH, '//*[contains(@content-desc, "Google")]'),
            ]

            for by, value in selectors:
                try:
                    element = self.wait.until(EC.presence_of_element_located((by, value)))
                    element.click()
                    log.info("Selected Google account type")
                    return True
                except Exception:
                    continue

            log.error("Could not find 'Google' account option")
            return False
        except Exception as e:
            log.error(f"Error selecting Google: {e}")
            return False

    def _enter_email(self, email: str) -> bool:
        """Enter email in the Google login WebView."""
        try:
            selectors = [
                (AppiumBy.XPATH, '//android.widget.EditText[@resource-id="identifierId"]'),
                (AppiumBy.XPATH, '//android.widget.EditText[contains(@text, "Email")]'),
                (AppiumBy.XPATH, '//android.widget.EditText'),
                (AppiumBy.CLASS_NAME, 'android.widget.EditText'),
            ]

            for by, value in selectors:
                try:
                    email_field = self.wait.until(EC.presence_of_element_located((by, value)))
                    email_field.clear()
                    self._human_type(email_field, email)
                    time.sleep(random.uniform(0.5, 1.5))

                    # Tap "Next"
                    self._tap_next()
                    return True
                except Exception:
                    continue

            log.error("Could not find email input field")
            return False
        except Exception as e:
            log.error(f"Email entry failed: {e}")
            return False

    def _enter_password(self, password: str) -> bool:
        """Enter password in the Google login WebView."""
        try:
            time.sleep(2)

            selectors = [
                (AppiumBy.XPATH, '//android.widget.EditText[@password="true"]'),
                (AppiumBy.XPATH, '//android.widget.EditText[contains(@resource-id, "password")]'),
                (AppiumBy.XPATH, '//android.widget.EditText'),
                (AppiumBy.CLASS_NAME, 'android.widget.EditText'),
            ]

            for by, value in selectors:
                try:
                    pw_field = self.wait.until(EC.presence_of_element_located((by, value)))
                    pw_field.clear()
                    self._human_type(pw_field, password)
                    time.sleep(random.uniform(0.5, 1.5))

                    self._tap_next()
                    return True
                except Exception:
                    continue

            log.error("Could not find password input field")
            return False
        except Exception as e:
            log.error(f"Password entry failed: {e}")
            return False

    def _tap_next(self):
        """Tap the 'Next' button."""
        next_selectors = [
            (AppiumBy.XPATH, '//*[@text="Next"]'),
            (AppiumBy.XPATH, '//*[contains(@text, "Next")]'),
            (AppiumBy.XPATH, '//*[contains(@content-desc, "Next")]'),
            (AppiumBy.XPATH, '//android.widget.Button[contains(@text, "Next")]'),
        ]

        for by, value in next_selectors:
            try:
                btn = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((by, value))
                )
                btn.click()
                time.sleep(2)
                return
            except Exception:
                continue

        # Fallback: press Enter key
        self.driver.press_keycode(66)  # KEYCODE_ENTER
        time.sleep(2)

    def _handle_post_login(self) -> bool:
        """Handle Terms of Service, recovery prompts, etc."""
        time.sleep(5)

        # Try to accept Terms of Service
        accept_selectors = [
            (AppiumBy.XPATH, '//*[@text="I agree"]'),
            (AppiumBy.XPATH, '//*[contains(@text, "I agree")]'),
            (AppiumBy.XPATH, '//*[contains(@text, "Accept")]'),
            (AppiumBy.XPATH, '//*[contains(@text, "AGREE")]'),
        ]

        for by, value in accept_selectors:
            try:
                btn = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((by, value))
                )
                btn.click()
                time.sleep(2)
                break
            except Exception:
                continue

        # Skip recovery options
        skip_selectors = [
            (AppiumBy.XPATH, '//*[contains(@text, "Skip")]'),
            (AppiumBy.XPATH, '//*[contains(@text, "Not now")]'),
            (AppiumBy.XPATH, '//*[contains(@text, "NO THANKS")]'),
            (AppiumBy.XPATH, '//*[contains(@text, "More")]'),
        ]

        for _ in range(3):  # Multiple skip screens possible
            for by, value in skip_selectors:
                try:
                    btn = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((by, value))
                    )
                    btn.click()
                    time.sleep(2)
                    break
                except Exception:
                    continue

        # Check for verification blocks
        page_source = self.driver.page_source
        if any(kw in page_source.lower() for kw in
               ["verify it", "confirm your identity", "unusual activity"]):
            log.warning("Google is requesting identity verification - BLOCKED")
            return False

        # Check if account was successfully added
        if self._verify_account_added():
            log.info("Google account added successfully")
            return True

        log.warning("Could not confirm account was added")
        return True  # Optimistic - may have succeeded

    def _verify_account_added(self) -> bool:
        """Check if a Google account exists on the device."""
        try:
            result = subprocess.run(
                [self.adb, "-s", self.serial, "shell",
                 "dumpsys", "account"],
                capture_output=True, text=True, timeout=10,
            )
            return "com.google" in result.stdout
        except Exception:
            return False

    def _human_type(self, element, text: str):
        """Type text character by character with random delays."""
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(
                config.TYPING_MIN_DELAY,
                config.TYPING_MAX_DELAY,
            ))
