import time
import random
from appium.webdriver import Remote as AppiumDriver
from appium.webdriver.common.appiumby import AppiumBy
from appium.webdriver.common.touch_action import TouchAction
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.logger import log
import config


class MapsAutomation:
    """Automates Google Maps app interactions via Appium."""

    def __init__(self, driver: AppiumDriver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 15)
        self.screen = driver.get_window_size()

    def open_maps(self) -> bool:
        """Launch Google Maps app."""
        try:
            self.driver.activate_app(config.MAPS_PACKAGE)
            time.sleep(random.uniform(3, 6))

            # Dismiss first-launch popups
            self._dismiss_popups()

            log.info("Google Maps opened")
            return True
        except Exception as e:
            log.error(f"Failed to open Maps: {e}")
            return False

    def search_place(self, place_name: str) -> bool:
        """Search for a place by name."""
        log.info(f"Searching for: {place_name}")

        try:
            # Tap search bar
            search_selectors = [
                (AppiumBy.XPATH, '//*[contains(@text, "Search here")]'),
                (AppiumBy.XPATH, '//*[contains(@content-desc, "Search")]'),
                (AppiumBy.XPATH, '//android.widget.EditText'),
                (AppiumBy.ID, f'{config.MAPS_PACKAGE}:id/search_omnibox_text_box'),
            ]

            search_field = None
            for by, value in search_selectors:
                try:
                    search_field = self.wait.until(
                        EC.presence_of_element_located((by, value))
                    )
                    search_field.click()
                    time.sleep(random.uniform(1, 2))
                    break
                except Exception:
                    continue

            if search_field is None:
                log.error("Could not find search bar")
                return False

            # Find the actual text input after clicking
            try:
                input_field = self.wait.until(
                    EC.presence_of_element_located(
                        (AppiumBy.CLASS_NAME, "android.widget.EditText")
                    )
                )
            except Exception:
                input_field = search_field

            # Type place name with human-like speed
            input_field.clear()
            self._human_type(input_field, place_name)
            time.sleep(random.uniform(1.5, 3))

            # Tap first search result
            return self._tap_search_result()

        except Exception as e:
            log.error(f"Search failed: {e}")
            return False

    def _tap_search_result(self) -> bool:
        """Tap on the first search suggestion/result."""
        result_selectors = [
            (AppiumBy.XPATH, '(//android.widget.LinearLayout[contains(@content-desc, "")])[1]'),
            (AppiumBy.XPATH, '//androidx.recyclerview.widget.RecyclerView//android.widget.LinearLayout[1]'),
            (AppiumBy.XPATH, '//android.widget.ListView//android.widget.LinearLayout[1]'),
        ]

        for by, value in result_selectors:
            try:
                result = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((by, value))
                )
                result.click()
                time.sleep(random.uniform(2, 4))
                log.info("Search result selected")
                return True
            except Exception:
                continue

        # Fallback: press Enter to search
        self.driver.press_keycode(66)  # KEYCODE_ENTER
        time.sleep(random.uniform(3, 5))

        log.info("Search submitted via Enter key")
        return True

    def post_review(self, review_text: str, rating: int = 5) -> bool:
        """Submit a review for the currently viewed place."""
        log.info(f"Posting review (rating={rating})")

        # Step 1: Scroll down to find review section
        if not self._scroll_to_review_section():
            return False

        # Step 2: Tap star rating
        if not self._set_rating(rating):
            return False

        # Step 3: Type review text
        if not self._type_review(review_text):
            return False

        # Step 4: Tap Post button
        return self._tap_post()

    def _scroll_to_review_section(self) -> bool:
        """Scroll down the place details to find the review section."""
        log.info("Scrolling to review section...")

        for attempt in range(8):
            # Check if we can see review-related elements
            review_indicators = [
                '//*[contains(@text, "Rate and review")]',
                '//*[contains(@text, "rate this")]',
                '//*[contains(@text, "Write a review")]',
                '//*[contains(@content-desc, "star")]',
                '//*[contains(@content-desc, "Rate")]',
            ]

            for xpath in review_indicators:
                try:
                    element = WebDriverWait(self.driver, 2).until(
                        EC.presence_of_element_located((AppiumBy.XPATH, xpath))
                    )
                    if element.is_displayed():
                        log.info("Found review section")
                        return True
                except Exception:
                    continue

            # Swipe up (scroll down)
            self._swipe_up()
            time.sleep(random.uniform(0.8, 1.5))

        log.error("Could not find review section after scrolling")
        return False

    def _set_rating(self, rating: int) -> bool:
        """Tap the appropriate star rating."""
        try:
            # Try various star selectors
            star_selectors = [
                (AppiumBy.XPATH, f'//*[contains(@content-desc, "{rating} star")]'),
                (AppiumBy.XPATH, f'(//*[contains(@class, "ImageView") and contains(@content-desc, "star")])[{rating}]'),
                (AppiumBy.XPATH, f'(//*[@clickable="true" and contains(@content-desc, "star")])[{rating}]'),
            ]

            for by, value in star_selectors:
                try:
                    star = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((by, value))
                    )
                    star.click()
                    time.sleep(random.uniform(1, 2))
                    log.info(f"Rating set to {rating} stars")
                    return True
                except Exception:
                    continue

            # Fallback: find all star-like elements and tap the Nth one
            stars = self.driver.find_elements(
                AppiumBy.XPATH, '//*[contains(@content-desc, "star")]'
            )
            if len(stars) >= rating:
                stars[rating - 1].click()
                time.sleep(random.uniform(1, 2))
                log.info(f"Rating set to {rating} stars (fallback)")
                return True

            log.error("Could not find star rating elements")
            return False

        except Exception as e:
            log.error(f"Rating failed: {e}")
            return False

    def _type_review(self, review_text: str) -> bool:
        """Type the review text."""
        try:
            time.sleep(random.uniform(1, 2))

            text_selectors = [
                (AppiumBy.XPATH, '//*[contains(@text, "Share details")]'),
                (AppiumBy.XPATH, '//*[contains(@text, "Describe your experience")]'),
                (AppiumBy.XPATH, '//*[contains(@text, "Write a review")]'),
                (AppiumBy.CLASS_NAME, "android.widget.EditText"),
            ]

            for by, value in text_selectors:
                try:
                    text_field = self.wait.until(
                        EC.presence_of_element_located((by, value))
                    )
                    text_field.click()
                    time.sleep(random.uniform(0.5, 1.5))

                    # Find actual EditText if we clicked a container
                    try:
                        edit_text = self.driver.find_element(
                            AppiumBy.CLASS_NAME, "android.widget.EditText"
                        )
                        text_field = edit_text
                    except Exception:
                        pass

                    self._human_type(text_field, review_text)
                    time.sleep(random.uniform(0.5, 2))
                    log.info("Review text typed")
                    return True
                except Exception:
                    continue

            log.error("Could not find review text field")
            return False

        except Exception as e:
            log.error(f"Typing review failed: {e}")
            return False

    def _tap_post(self) -> bool:
        """Tap the Post/Submit button."""
        try:
            post_selectors = [
                (AppiumBy.XPATH, '//*[@text="Post"]'),
                (AppiumBy.XPATH, '//*[contains(@text, "Post")]'),
                (AppiumBy.XPATH, '//*[contains(@content-desc, "Post")]'),
                (AppiumBy.XPATH, '//android.widget.Button[@text="Post"]'),
            ]

            for by, value in post_selectors:
                try:
                    btn = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((by, value))
                    )
                    time.sleep(random.uniform(0.5, 1.5))
                    btn.click()
                    time.sleep(random.uniform(3, 5))

                    # Check for success
                    page_source = self.driver.page_source
                    if any(kw in page_source.lower() for kw in
                           ["your review", "posted", "thanks"]):
                        log.info("Review posted successfully!")
                        return True

                    log.info("Review submitted (no error detected)")
                    return True
                except Exception:
                    continue

            log.error("Could not find Post button")
            return False

        except Exception as e:
            log.error(f"Post failed: {e}")
            return False

    def _dismiss_popups(self):
        """Dismiss common first-launch popups."""
        dismiss_texts = [
            "GOT IT", "Got it", "SKIP", "Skip",
            "OK", "ACCEPT", "NO THANKS", "Not now",
            "MAYBE LATER", "Maybe later",
        ]

        for _ in range(3):
            for text in dismiss_texts:
                try:
                    btn = WebDriverWait(self.driver, 2).until(
                        EC.element_to_be_clickable(
                            (AppiumBy.XPATH, f'//*[@text="{text}"]')
                        )
                    )
                    btn.click()
                    time.sleep(1)
                except Exception:
                    continue

        # Handle location permission
        try:
            allow_btn = WebDriverWait(self.driver, 3).until(
                EC.element_to_be_clickable(
                    (AppiumBy.ID, "com.android.permissioncontroller:id/permission_allow_foreground_only_button")
                )
            )
            allow_btn.click()
            time.sleep(1)
        except Exception:
            pass

    def _swipe_up(self):
        """Perform a natural swipe up gesture."""
        w = self.screen["width"]
        h = self.screen["height"]

        start_x = w // 2 + random.randint(-30, 30)
        start_y = int(h * 0.7) + random.randint(-20, 20)
        end_x = start_x + random.randint(-15, 15)
        end_y = int(h * 0.3) + random.randint(-20, 20)
        duration = random.randint(400, 700)

        self.driver.swipe(start_x, start_y, end_x, end_y, duration)

    def simulate_browsing(self, duration: int = 10):
        """Simulate natural browsing behavior before reviewing."""
        log.info("Simulating natural browsing...")
        start = time.time()

        while time.time() - start < duration:
            action = random.choice(["scroll", "wait", "tap_random"])

            if action == "scroll":
                self._swipe_up()
                time.sleep(random.uniform(1, 3))
            elif action == "wait":
                time.sleep(random.uniform(2, 5))
            elif action == "tap_random":
                # Tap a random safe area (middle of screen)
                x = random.randint(self.screen["width"] // 4, self.screen["width"] * 3 // 4)
                y = random.randint(self.screen["height"] // 3, self.screen["height"] * 2 // 3)
                try:
                    TouchAction(self.driver).tap(x=x, y=y).perform()
                except Exception:
                    pass
                time.sleep(random.uniform(1, 2))

    def _human_type(self, element, text: str):
        """Type text character by character with human-like delays."""
        for i, char in enumerate(text):
            element.send_keys(char)
            delay = random.uniform(config.TYPING_MIN_DELAY, config.TYPING_MAX_DELAY)

            # Occasional pause (thinking)
            if random.random() < 0.05:
                delay += random.uniform(0.5, 1.5)

            time.sleep(delay)
