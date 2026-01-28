import asyncio
import random
from playwright.async_api import Page
from core.captcha_solver import CaptchaSolver
from core.human_behavior import human_type, human_click, random_mouse_movement, random_idle
from utils.logger import log
import config


class GoogleAuth:
    def __init__(self, page: Page, captcha_solver: CaptchaSolver):
        self.page = page
        self.solver = captcha_solver

    async def login(self, email: str, password: str) -> bool:
        """Log into Google account. Returns True on success."""
        log.info(f"Logging into Google: {email}")

        try:
            await self.page.goto(config.GOOGLE_LOGIN_URL, wait_until="networkidle",
                                 timeout=config.PAGE_LOAD_TIMEOUT)
        except Exception as e:
            log.error(f"Failed to load login page: {e}")
            return False

        # Build reCAPTCHA v3 score with natural behavior
        await random_mouse_movement(self.page, count=random.randint(2, 4))
        await random_idle(1.0, 3.0)

        # --- Enter Email ---
        if not await self._enter_email(email):
            return False
        await random_idle(1.5, 3.5)

        # --- Enter Password ---
        if not await self._enter_password(password):
            return False
        await random_idle(2.0, 4.0)

        # --- Handle post-login challenges ---
        success = await self._handle_post_login()
        if success:
            log.info(f"Successfully logged in: {email}")
        return success

    async def _enter_email(self, email: str) -> bool:
        try:
            email_selector = 'input[type="email"]'
            await self.page.wait_for_selector(email_selector, timeout=10000)
            await human_type(self.page, email_selector, email)
            await random_idle(0.3, 0.8)

            next_btn = self.page.locator("#identifierNext")
            await next_btn.click()
            await self.page.wait_for_load_state("networkidle", timeout=10000)
            return True
        except Exception as e:
            log.error(f"Failed to enter email: {e}")
            if await self._check_and_solve_captcha():
                return await self._enter_email(email)
            return False

    async def _enter_password(self, password: str) -> bool:
        try:
            password_selector = 'input[type="password"]'
            await self.page.wait_for_selector(password_selector, state="visible", timeout=10000)
            await random_idle(0.5, 1.5)
            await human_type(self.page, password_selector, password)
            await random_idle(0.3, 0.8)

            next_btn = self.page.locator("#passwordNext")
            await next_btn.click()
            await self.page.wait_for_load_state("networkidle", timeout=15000)
            return True
        except Exception as e:
            log.error(f"Failed to enter password: {e}")
            if await self._check_and_solve_captcha():
                return await self._enter_password(password)
            return False

    async def _handle_post_login(self) -> bool:
        """Handle various post-login challenges."""
        await asyncio.sleep(3)
        current_url = self.page.url

        # Success — landed on a non-login Google page
        if "myaccount.google.com" in current_url or (
            "google.com" in current_url
            and "signin" not in current_url
            and "challenge" not in current_url
        ):
            return True

        # Challenge page
        if "challenge" in current_url:
            log.warning("Google is requesting additional verification (2FA/phone)")
            return await self._handle_challenge()

        # Phone verification
        page_content = await self.page.content()
        if "verify" in page_content.lower() and "phone" in page_content.lower():
            log.warning("Phone verification requested — cannot proceed without phone access")
            return False

        # CAPTCHA
        if await self._check_and_solve_captcha():
            await asyncio.sleep(3)
            return await self._handle_post_login()

        # Wrong password
        if "wrong password" in page_content.lower() or "couldn't sign you in" in page_content.lower():
            log.error("Wrong password")
            return False

        if "google.com" in current_url and "signin" not in current_url:
            return True

        log.warning(f"Unknown post-login state. URL: {current_url}")
        return False

    async def _handle_challenge(self) -> bool:
        page_content = await self.page.content()

        if "phone" in page_content.lower() or "sms" in page_content.lower():
            log.warning("SMS verification required — not automated in this version")
            return False

        try:
            another_way = self.page.locator("text=Try another way")
            if await another_way.is_visible():
                await another_way.click()
                await asyncio.sleep(2)
        except Exception:
            pass

        log.warning("Cannot handle this challenge type automatically")
        return False

    async def _check_and_solve_captcha(self) -> bool:
        """Screenshot the page, use OpenAI Vision to detect & solve CAPTCHA."""
        try:
            # Take a screenshot of the current page
            screenshot = await self.page.screenshot(type="png")

            # Step 1: Detect CAPTCHA type via OpenAI Vision
            analysis = self.solver.analyze_captcha_type(screenshot)
            captcha_type = analysis.get("type", "none")

            if captcha_type == "none":
                return False

            log.info(f"CAPTCHA detected: {captcha_type}")

            if captcha_type == "recaptcha_v2_checkbox":
                return await self._solve_v2_checkbox()

            elif captcha_type == "recaptcha_v2_image":
                return await self._solve_v2_image(analysis.get("challenge_text", ""))

            else:
                log.warning(f"Unsupported CAPTCHA type: {captcha_type}")
                return False

        except Exception as e:
            log.error(f"CAPTCHA check failed: {e}")
            return False

    async def _solve_v2_checkbox(self) -> bool:
        """Click the reCAPTCHA checkbox, then solve image challenge if it appears."""
        try:
            # Click the checkbox inside the reCAPTCHA iframe
            captcha_frame = self.page.frame_locator("iframe[src*='recaptcha']")
            checkbox = captcha_frame.locator(".recaptcha-checkbox-border")

            if await checkbox.is_visible(timeout=3000):
                await checkbox.click()
                await asyncio.sleep(3)

                # Check if image challenge appeared
                screenshot = await self.page.screenshot(type="png")
                analysis = self.solver.analyze_captcha_type(screenshot)

                if analysis.get("type") == "recaptcha_v2_image":
                    return await self._solve_v2_image(analysis.get("challenge_text", ""))

                return True  # Checkbox passed without image challenge
        except Exception as e:
            log.error(f"Checkbox solve failed: {e}")

        # Fallback to 2Captcha token injection if available
        return await self._try_token_injection()

    async def _solve_v2_image(self, challenge_text: str) -> bool:
        """Solve reCAPTCHA v2 image grid using OpenAI Vision."""
        max_attempts = 3

        for attempt in range(max_attempts):
            log.info(f"Solving image CAPTCHA (attempt {attempt + 1}/{max_attempts})")

            try:
                # Find the CAPTCHA challenge iframe/popup
                # Take a screenshot focused on the challenge area
                screenshot = await self.page.screenshot(type="png")

                # Ask OpenAI Vision which tiles to click
                result = self.solver.solve_image_captcha(screenshot, challenge_text)
                tiles = result.get("tiles", [])
                confidence = result.get("confidence", 0)

                if not tiles:
                    log.warning("No tiles identified by OpenAI")
                    continue

                log.info(f"OpenAI says click tiles: {tiles} (confidence: {confidence})")

                # Click the identified tiles in the challenge iframe
                challenge_frame = self.page.frame_locator(
                    "iframe[src*='recaptcha'][title*='challenge']"
                )

                # Get all tile elements
                tile_elements = challenge_frame.locator("table td")
                tile_count = await tile_elements.count()

                for tile_idx in tiles:
                    if tile_idx < tile_count:
                        await tile_elements.nth(tile_idx).click()
                        await asyncio.sleep(random.uniform(0.3, 0.8))

                # Click "Verify" button
                verify_btn = challenge_frame.locator("#recaptcha-verify-button")
                if await verify_btn.is_visible(timeout=2000):
                    await verify_btn.click()
                    await asyncio.sleep(3)

                # Check if challenge is solved (iframe disappeared or new challenge)
                screenshot_after = await self.page.screenshot(type="png")
                after_analysis = self.solver.analyze_captcha_type(screenshot_after)

                if after_analysis.get("type") == "none":
                    log.info("Image CAPTCHA solved!")
                    return True
                elif after_analysis.get("type") == "recaptcha_v2_image":
                    challenge_text = after_analysis.get("challenge_text", challenge_text)
                    log.info("New image challenge appeared, retrying...")
                    continue

            except Exception as e:
                log.error(f"Image CAPTCHA attempt {attempt + 1} failed: {e}")

        log.error("Failed to solve image CAPTCHA after all attempts")
        return await self._try_token_injection()

    async def _try_token_injection(self) -> bool:
        """Last resort: try 2Captcha token injection if configured."""
        if self.solver.solver_type == "2captcha" or config.CAPTCHA_2CAPTCHA_KEY:
            try:
                sitekey = await self.page.evaluate("""
                    () => {
                        const el = document.querySelector('[data-sitekey]');
                        if (el) return el.getAttribute('data-sitekey');
                        const iframe = document.querySelector('iframe[src*="recaptcha"]');
                        if (iframe) {
                            const url = new URL(iframe.src);
                            return url.searchParams.get('k');
                        }
                        return null;
                    }
                """)

                if not sitekey:
                    return False

                token = self.solver.solve_recaptcha_v2_token(sitekey, self.page.url)
                if not token:
                    return False

                await self.page.evaluate(f"""
                    (token) => {{
                        const el = document.getElementById('g-recaptcha-response');
                        if (el) el.value = token;
                        const form = document.querySelector('form');
                        if (form) form.submit();
                    }}
                """, token)

                log.info("2Captcha token injected as fallback")
                await asyncio.sleep(3)
                return True

            except Exception as e:
                log.error(f"Token injection fallback failed: {e}")

        return False
