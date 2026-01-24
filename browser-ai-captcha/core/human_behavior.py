import random
import math
import asyncio
from playwright.async_api import Page
from utils.logger import log


async def human_type(page: Page, selector: str, text: str, min_delay: int = 60, max_delay: int = 220):
    """Type text with human-like variable speed and occasional typos."""
    element = page.locator(selector)
    await element.click()
    await asyncio.sleep(random.uniform(0.3, 0.8))

    for i, char in enumerate(text):
        # Occasional typo (3% chance)
        if random.random() < 0.03 and char.isalpha():
            nearby_keys = _get_nearby_keys(char)
            if nearby_keys:
                wrong_char = random.choice(nearby_keys)
                await page.keyboard.type(wrong_char, delay=random.randint(min_delay, max_delay))
                await asyncio.sleep(random.uniform(0.1, 0.3))
                await page.keyboard.press("Backspace")
                await asyncio.sleep(random.uniform(0.05, 0.15))

        delay = random.randint(min_delay, max_delay)

        # Occasional pause (simulating thinking)
        if random.random() < 0.05:
            await asyncio.sleep(random.uniform(0.5, 2.0))

        # Speed up for common sequences
        if i > 0 and text[i - 1:i + 1] in ("th", "he", "in", "er", "an", "re", "on"):
            delay = int(delay * 0.6)

        await page.keyboard.type(char, delay=delay)


async def human_click(page: Page, selector: str):
    """Click an element with realistic mouse movement."""
    element = page.locator(selector)
    box = await element.bounding_box()
    if not box:
        await element.click()
        return

    # Click at a random position within the element (not dead center)
    x = box["x"] + box["width"] * random.uniform(0.2, 0.8)
    y = box["y"] + box["height"] * random.uniform(0.2, 0.8)

    # Move to element with curve
    await _bezier_move(page, x, y)
    await asyncio.sleep(random.uniform(0.05, 0.15))
    await page.mouse.click(x, y)


async def human_scroll(page: Page, direction: str = "down", amount: int = 300):
    """Scroll with natural speed variation."""
    steps = random.randint(3, 6)
    per_step = amount // steps
    multiplier = -1 if direction == "down" else 1

    for _ in range(steps):
        delta = per_step + random.randint(-30, 30)
        await page.mouse.wheel(0, delta * multiplier * -1)
        await asyncio.sleep(random.uniform(0.1, 0.4))


async def random_mouse_movement(page: Page, count: int = 3):
    """Make random mouse movements to build reCAPTCHA v3 score."""
    viewport = page.viewport_size or {"width": 1280, "height": 720}

    for _ in range(count):
        x = random.randint(100, viewport["width"] - 100)
        y = random.randint(100, viewport["height"] - 100)
        await _bezier_move(page, x, y)
        await asyncio.sleep(random.uniform(0.3, 1.5))


async def random_idle(min_sec: float = 1.0, max_sec: float = 5.0):
    """Wait a random amount of time (simulating reading/thinking)."""
    await asyncio.sleep(random.uniform(min_sec, max_sec))


async def _bezier_move(page: Page, target_x: float, target_y: float, steps: int = 20):
    """Move mouse along a bezier curve to target position."""
    # Get current position (approximate from viewport center if unknown)
    viewport = page.viewport_size or {"width": 1280, "height": 720}
    start_x = random.randint(viewport["width"] // 4, viewport["width"] * 3 // 4)
    start_y = random.randint(viewport["height"] // 4, viewport["height"] * 3 // 4)

    # Control points for bezier curve
    cp1_x = start_x + (target_x - start_x) * random.uniform(0.2, 0.5) + random.randint(-50, 50)
    cp1_y = start_y + (target_y - start_y) * random.uniform(0.0, 0.3) + random.randint(-50, 50)
    cp2_x = start_x + (target_x - start_x) * random.uniform(0.5, 0.8) + random.randint(-30, 30)
    cp2_y = start_y + (target_y - start_y) * random.uniform(0.7, 1.0) + random.randint(-30, 30)

    for i in range(steps + 1):
        t = i / steps
        x = _cubic_bezier(t, start_x, cp1_x, cp2_x, target_x)
        y = _cubic_bezier(t, start_y, cp1_y, cp2_y, target_y)
        await page.mouse.move(x, y)
        await asyncio.sleep(random.uniform(0.005, 0.025))


def _cubic_bezier(t: float, p0: float, p1: float, p2: float, p3: float) -> float:
    return (
        (1 - t) ** 3 * p0
        + 3 * (1 - t) ** 2 * t * p1
        + 3 * (1 - t) * t ** 2 * p2
        + t ** 3 * p3
    )


KEYBOARD_LAYOUT = {
    "q": ["w", "a"], "w": ["q", "e", "s"], "e": ["w", "r", "d"],
    "r": ["e", "t", "f"], "t": ["r", "y", "g"], "y": ["t", "u", "h"],
    "u": ["y", "i", "j"], "i": ["u", "o", "k"], "o": ["i", "p", "l"],
    "p": ["o", "l"], "a": ["q", "s", "z"], "s": ["a", "w", "d", "x"],
    "d": ["s", "e", "f", "c"], "f": ["d", "r", "g", "v"],
    "g": ["f", "t", "h", "b"], "h": ["g", "y", "j", "n"],
    "j": ["h", "u", "k", "m"], "k": ["j", "i", "l"],
    "l": ["k", "o", "p"], "z": ["a", "x"], "x": ["z", "s", "c"],
    "c": ["x", "d", "v"], "v": ["c", "f", "b"], "b": ["v", "g", "n"],
    "n": ["b", "h", "m"], "m": ["n", "j"],
}


def _get_nearby_keys(char: str) -> list[str]:
    return KEYBOARD_LAYOUT.get(char.lower(), [])
