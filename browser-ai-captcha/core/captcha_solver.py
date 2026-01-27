import base64
import json
import time
from io import BytesIO
from pathlib import Path

import httpx
from openai import OpenAI
from utils.logger import log
import config


class CaptchaSolver:
    """Solves reCAPTCHA challenges using OpenAI Vision API or 2Captcha as fallback."""

    def __init__(self):
        self.solver_type = config.CAPTCHA_SOLVER  # "openai" or "2captcha"

        if self.solver_type == "openai":
            if not config.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY required for OpenAI CAPTCHA solver")
            self.client = OpenAI(api_key=config.OPENAI_API_KEY)
            log.info("CAPTCHA solver: OpenAI Vision")
        elif self.solver_type == "2captcha":
            if not config.CAPTCHA_2CAPTCHA_KEY:
                raise ValueError("CAPTCHA_2CAPTCHA_KEY required for 2Captcha solver")
            self.api_key_2captcha = config.CAPTCHA_2CAPTCHA_KEY
            log.info("CAPTCHA solver: 2Captcha")

    # ------------------------------------------------------------------ #
    #                     OpenAI Vision CAPTCHA Solving                    #
    # ------------------------------------------------------------------ #

    def solve_image_captcha(self, screenshot_bytes: bytes, challenge_text: str = "") -> dict:
        """Use OpenAI Vision to analyze a CAPTCHA image and return which tiles to click.

        Args:
            screenshot_bytes: PNG screenshot of the CAPTCHA challenge
            challenge_text: The challenge instruction (e.g., "Select all images with traffic lights")

        Returns:
            dict with keys:
                "tiles": list of tile indices (0-based) to click, e.g. [0, 3, 6]
                "confidence": float 0-1
                "reasoning": str explanation
        """
        if self.solver_type != "openai":
            log.warning("Image CAPTCHA solving requires OpenAI solver")
            return {"tiles": [], "confidence": 0, "reasoning": "wrong solver type"}

        b64_image = base64.b64encode(screenshot_bytes).decode("utf-8")

        prompt = f"""You are analyzing a reCAPTCHA image challenge.

The challenge instruction is: "{challenge_text or 'Select all matching images'}"

The image shows a grid of tiles (typically 3x3 or 4x4).
Tiles are numbered left-to-right, top-to-bottom starting from 0:
  3x3 grid: [0,1,2 / 3,4,5 / 6,7,8]
  4x4 grid: [0,1,2,3 / 4,5,6,7 / 8,9,10,11 / 12,13,14,15]

Analyze each tile and determine which ones match the challenge.

Respond ONLY with valid JSON:
{{
  "grid_size": "3x3" or "4x4",
  "tiles": [list of matching tile indices],
  "confidence": 0.0 to 1.0,
  "reasoning": "brief explanation"
}}"""

        try:
            response = self.client.chat.completions.create(
                model=config.OPENAI_VISION_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{b64_image}",
                                    "detail": "high",
                                },
                            },
                        ],
                    }
                ],
                max_tokens=300,
                temperature=0.1,
            )

            raw = response.choices[0].message.content.strip()
            # Extract JSON from the response
            if "```json" in raw:
                raw = raw.split("```json")[1].split("```")[0].strip()
            elif "```" in raw:
                raw = raw.split("```")[1].split("```")[0].strip()

            result = json.loads(raw)
            log.info(f"OpenAI CAPTCHA analysis: tiles={result.get('tiles')}, "
                     f"confidence={result.get('confidence')}")
            return result

        except Exception as e:
            log.error(f"OpenAI vision CAPTCHA solve failed: {e}")
            return {"tiles": [], "confidence": 0, "reasoning": str(e)}

    def analyze_captcha_type(self, screenshot_bytes: bytes) -> dict:
        """Use OpenAI Vision to identify what type of CAPTCHA is shown.

        Returns:
            dict with keys:
                "type": "recaptcha_v2_checkbox" | "recaptcha_v2_image" | "text_captcha" | "none"
                "challenge_text": str (the instruction text if visible)
                "sitekey": str | None
        """
        if self.solver_type != "openai":
            return {"type": "unknown", "challenge_text": "", "sitekey": None}

        b64_image = base64.b64encode(screenshot_bytes).decode("utf-8")

        try:
            response = self.client.chat.completions.create(
                model=config.OPENAI_VISION_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """Analyze this screenshot and identify any CAPTCHA present.

Respond ONLY with valid JSON:
{
  "type": "recaptcha_v2_checkbox" | "recaptcha_v2_image" | "text_captcha" | "none",
  "challenge_text": "the instruction text if visible, e.g. Select all images with traffic lights",
  "has_checkbox": true/false,
  "grid_visible": true/false,
  "grid_size": "3x3" or "4x4" or null
}""",
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{b64_image}",
                                    "detail": "high",
                                },
                            },
                        ],
                    }
                ],
                max_tokens=200,
                temperature=0.1,
            )

            raw = response.choices[0].message.content.strip()
            if "```json" in raw:
                raw = raw.split("```json")[1].split("```")[0].strip()
            elif "```" in raw:
                raw = raw.split("```")[1].split("```")[0].strip()

            result = json.loads(raw)
            log.info(f"CAPTCHA type detected: {result.get('type')}")
            return result

        except Exception as e:
            log.error(f"CAPTCHA type analysis failed: {e}")
            return {"type": "unknown", "challenge_text": "", "sitekey": None}

    # ------------------------------------------------------------------ #
    #                     2Captcha Token-Based Solving                     #
    # ------------------------------------------------------------------ #

    def solve_recaptcha_v2_token(self, sitekey: str, page_url: str, timeout: int = 120) -> str | None:
        """Solve reCAPTCHA v2 via 2Captcha API and return g-recaptcha-response token."""
        if self.solver_type == "2captcha":
            return self._2captcha_solve_v2(sitekey, page_url, timeout)

        log.warning("Token-based solving only available with 2Captcha")
        return None

    def _2captcha_solve_v2(self, sitekey: str, page_url: str, timeout: int) -> str | None:
        base_url = "http://2captcha.com"

        # Submit task
        try:
            resp = httpx.get(f"{base_url}/in.php", params={
                "key": self.api_key_2captcha,
                "method": "userrecaptcha",
                "googlekey": sitekey,
                "pageurl": page_url,
                "json": 1,
            }, timeout=30)
            data = resp.json()
            if data.get("status") != 1:
                log.error(f"2Captcha submit failed: {data}")
                return None
            task_id = data["request"]
            log.info(f"2Captcha task: {task_id}")
        except Exception as e:
            log.error(f"2Captcha submit error: {e}")
            return None

        # Poll for result
        start = time.time()
        while time.time() - start < timeout:
            time.sleep(5)
            try:
                resp = httpx.get(f"{base_url}/res.php", params={
                    "key": self.api_key_2captcha,
                    "action": "get",
                    "id": task_id,
                    "json": 1,
                }, timeout=30)
                data = resp.json()
                if data.get("status") == 1:
                    log.info("reCAPTCHA v2 token received")
                    return data["request"]
                elif data.get("request") != "CAPCHA_NOT_READY":
                    log.error(f"2Captcha failed: {data}")
                    return None
            except Exception:
                continue

        log.error("2Captcha timed out")
        return None
