import random
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from playwright_stealth import stealth_async
from utils.logger import log
import config

# Realistic viewport sizes
VIEWPORTS = [
    {"width": 1920, "height": 1080},
    {"width": 1366, "height": 768},
    {"width": 1536, "height": 864},
    {"width": 1440, "height": 900},
    {"width": 1280, "height": 720},
]

LOCALES = ["en-US", "en-GB", "en-CA", "en-AU"]

TIMEZONES = [
    "America/New_York", "America/Chicago", "America/Denver",
    "America/Los_Angeles", "America/Toronto", "Europe/London",
]


class StealthBrowser:
    def __init__(self, proxy: dict | None = None):
        self.proxy = proxy
        self._playwright = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self.page: Page | None = None

    async def launch(self) -> Page:
        self._playwright = await async_playwright().start()

        launch_args = {
            "headless": config.HEADLESS,
            "slow_mo": config.SLOW_MO,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--disable-features=IsolateOrigins,site-per-process",
                "--disable-infobars",
                "--no-first-run",
                "--no-default-browser-check",
                f"--window-size={1920},{1080}",
            ],
        }

        if self.proxy:
            launch_args["proxy"] = self.proxy

        self._browser = await self._playwright.chromium.launch(**launch_args)

        viewport = random.choice(VIEWPORTS)
        locale = random.choice(LOCALES)
        timezone = random.choice(TIMEZONES)

        self._context = await self._browser.new_context(
            viewport=viewport,
            locale=locale,
            timezone_id=timezone,
            user_agent=_random_user_agent(),
            color_scheme=random.choice(["light", "dark", "no-preference"]),
            has_touch=False,
            java_script_enabled=True,
            permissions=["geolocation"],
            geolocation={"latitude": 40.7128, "longitude": -74.0060},
        )

        self.page = await self._context.new_page()

        # Apply stealth patches
        await stealth_async(self.page)

        # Extra stealth: override navigator properties
        await self.page.add_init_script("""
            // Override webdriver
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });

            // Override plugins length
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });

            // Override languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });

            // Chrome runtime
            window.chrome = { runtime: {} };

            // Permissions query
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) =>
                parameters.name === 'notifications'
                    ? Promise.resolve({ state: Notification.permission })
                    : originalQuery(parameters);
        """)

        log.info(f"Browser launched (viewport={viewport['width']}x{viewport['height']}, locale={locale})")
        return self.page

    async def close(self):
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        log.info("Browser closed")

    async def save_cookies(self, path: str):
        if self._context:
            cookies = await self._context.cookies()
            import json
            from pathlib import Path
            Path(path).write_text(json.dumps(cookies, indent=2))

    async def load_cookies(self, path: str):
        from pathlib import Path
        import json
        cookie_path = Path(path)
        if cookie_path.exists() and self._context:
            cookies = json.loads(cookie_path.read_text())
            await self._context.add_cookies(cookies)
            log.info(f"Loaded cookies from {path}")


def _random_user_agent() -> str:
    chrome_versions = [
        "120.0.6099.109", "121.0.6167.85", "122.0.6261.69",
        "123.0.6312.58", "124.0.6367.91", "125.0.6422.76",
    ]
    platforms = [
        ("Windows NT 10.0; Win64; x64", "Windows"),
        ("Macintosh; Intel Mac OS X 10_15_7", "macOS"),
        ("X11; Linux x86_64", "Linux"),
    ]

    platform, _ = random.choice(platforms)
    chrome_ver = random.choice(chrome_versions)

    return (
        f"Mozilla/5.0 ({platform}) AppleWebKit/537.36 "
        f"(KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36"
    )
