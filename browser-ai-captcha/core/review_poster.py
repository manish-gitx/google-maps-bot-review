import asyncio
import random
from playwright.async_api import Page
from core.human_behavior import (
    human_type, human_click, human_scroll,
    random_mouse_movement, random_idle,
)
from utils.logger import log
import config


class ReviewPoster:
    def __init__(self, page: Page):
        self.page = page

    async def post_review(self, place_url: str, review_text: str, rating: int = 5) -> bool:
        """Navigate to a Google Maps place and post a review."""
        rating = max(1, min(5, rating))

        log.info(f"Posting review (rating={rating}) to: {place_url}")

        # Step 1: Navigate to the place
        if not await self._navigate_to_place(place_url):
            return False

        # Step 2: Build reCAPTCHA v3 score with natural behavior
        await self._simulate_browsing()

        # Step 3: Click "Write a review"
        if not await self._open_review_form():
            return False

        # Step 4: Set star rating
        if not await self._set_rating(rating):
            return False

        # Step 5: Type the review
        if not await self._type_review(review_text):
            return False

        # Step 6: Submit
        return await self._submit_review()

    async def _navigate_to_place(self, place_url: str) -> bool:
        try:
            await self.page.goto(place_url, wait_until="domcontentloaded",
                                 timeout=config.PAGE_LOAD_TIMEOUT)
            await asyncio.sleep(random.uniform(2, 5))

            # Wait for place details to load
            await self.page.wait_for_selector(
                'h1, [data-item-id="title"]',
                timeout=15000,
            )
            log.info("Place page loaded successfully")
            return True
        except Exception as e:
            log.error(f"Failed to navigate to place: {e}")
            return False

    async def _simulate_browsing(self):
        """Simulate natural browsing behavior to build reCAPTCHA v3 trust."""
        log.info("Simulating natural browsing behavior...")

        # Random mouse movements
        await random_mouse_movement(self.page, count=random.randint(3, 6))

        # Scroll down to see the place details
        for _ in range(random.randint(2, 4)):
            await human_scroll(self.page, "down", random.randint(200, 500))
            await random_idle(0.5, 2.0)

        # Scroll back up a bit
        await human_scroll(self.page, "up", random.randint(100, 300))
        await random_idle(1.0, 3.0)

        # More mouse movements
        await random_mouse_movement(self.page, count=random.randint(2, 4))

    async def _open_review_form(self) -> bool:
        """Find and click the 'Write a review' button."""
        selectors = [
            'button[aria-label*="Write a review"]',
            'button[data-value="Write a review"]',
            'button:has-text("Write a review")',
            '[jsaction*="review"]',
            'span:text("Write a review")',
        ]

        for selector in selectors:
            try:
                element = self.page.locator(selector).first
                if await element.is_visible(timeout=3000):
                    await human_click(self.page, selector)
                    await asyncio.sleep(random.uniform(1, 3))
                    log.info("Review form opened")
                    return True
            except Exception:
                continue

        # Try scrolling down to find the review button
        log.info("Review button not found, scrolling to find it...")
        for _ in range(5):
            await human_scroll(self.page, "down", 400)
            await asyncio.sleep(1)

            for selector in selectors:
                try:
                    element = self.page.locator(selector).first
                    if await element.is_visible(timeout=1000):
                        await human_click(self.page, selector)
                        await asyncio.sleep(random.uniform(1, 3))
                        log.info("Review form opened (after scrolling)")
                        return True
                except Exception:
                    continue

        log.error("Could not find 'Write a review' button")
        return False

    async def _set_rating(self, rating: int) -> bool:
        """Click the appropriate star rating."""
        try:
            # Google Maps uses aria-label like "1 star", "2 stars", etc.
            star_selectors = [
                f'[aria-label="{rating} star{"s" if rating != 1 else ""}"]',
                f'[data-rating="{rating}"]',
                f'div[aria-label*="star"] >> nth={rating - 1}',
            ]

            for selector in star_selectors:
                try:
                    element = self.page.locator(selector).first
                    if await element.is_visible(timeout=3000):
                        await element.click()
                        await random_idle(0.5, 1.5)
                        log.info(f"Rating set to {rating} stars")
                        return True
                except Exception:
                    continue

            # Fallback: try clicking star by index
            stars = self.page.locator('[role="radio"], [data-rating]')
            count = await stars.count()
            if count >= rating:
                await stars.nth(rating - 1).click()
                await random_idle(0.5, 1.5)
                log.info(f"Rating set to {rating} stars (fallback)")
                return True

            log.error("Could not set star rating")
            return False

        except Exception as e:
            log.error(f"Error setting rating: {e}")
            return False

    async def _type_review(self, review_text: str) -> bool:
        """Type the review text in the review textarea."""
        try:
            textarea_selectors = [
                'textarea[aria-label*="review"]',
                'textarea[aria-label*="Share details"]',
                'textarea[jsname]',
                'textarea',
                '[contenteditable="true"]',
            ]

            for selector in textarea_selectors:
                try:
                    element = self.page.locator(selector).first
                    if await element.is_visible(timeout=3000):
                        await human_type(
                            self.page, selector, review_text,
                            min_delay=config.TYPING_MIN_DELAY,
                            max_delay=config.TYPING_MAX_DELAY,
                        )
                        await random_idle(0.5, 2.0)
                        log.info("Review text typed")
                        return True
                except Exception:
                    continue

            log.error("Could not find review textarea")
            return False

        except Exception as e:
            log.error(f"Error typing review: {e}")
            return False

    async def _submit_review(self) -> bool:
        """Click the Post/Submit button."""
        try:
            submit_selectors = [
                'button[aria-label="Post"]',
                'button:has-text("Post")',
                'button[jsname]:has-text("Post")',
                'button[data-value="Post"]',
            ]

            for selector in submit_selectors:
                try:
                    element = self.page.locator(selector).first
                    if await element.is_visible(timeout=3000):
                        await random_idle(0.5, 1.5)
                        await element.click()
                        await asyncio.sleep(3)

                        # Check for success indicators
                        page_content = await self.page.content()
                        if any(indicator in page_content.lower() for indicator in
                               ["your review", "review posted", "thanks for"]):
                            log.info("Review posted successfully!")
                            return True

                        # If no error appeared, assume success
                        log.info("Review submitted (no error detected)")
                        return True
                except Exception:
                    continue

            log.error("Could not find submit button")
            return False

        except Exception as e:
            log.error(f"Error submitting review: {e}")
            return False

    async def screenshot(self, path: str):
        """Take a screenshot for debugging/proof."""
        try:
            await self.page.screenshot(path=path, full_page=False)
            log.info(f"Screenshot saved: {path}")
        except Exception as e:
            log.error(f"Screenshot failed: {e}")
