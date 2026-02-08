import json
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import click
from appium import webdriver as appium_webdriver
from appium.options.android import UiAutomator2Options

import config
from core.account_manager import AccountManager
from core.proxy_manager import ProxyManager
from core.emulator_manager import EmulatorManager
from core.device_spoofing import get_random_profile, apply_device_props
from core.gps_spoofing import set_gps_location
from core.google_auth import GoogleAuth
from core.maps_automation import MapsAutomation
from utils.logger import log
from utils.review_generator import generate_review, generate_batch_reviews


RESULTS_FILE = "results.json"


def load_results() -> list[dict]:
    path = Path(RESULTS_FILE)
    if path.exists():
        return json.loads(path.read_text())
    return []


def save_result(result: dict):
    results = load_results()
    results.append(result)
    Path(RESULTS_FILE).write_text(json.dumps(results, indent=2))


def create_appium_driver(serial: str, port: int = 4723) -> appium_webdriver.Remote:
    """Create an Appium driver connected to the emulator."""
    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.device_name = serial
    options.udid = serial
    options.no_reset = True
    options.auto_grant_permissions = True
    options.new_command_timeout = 300

    appium_url = f"{config.APPIUM_HOST}:{port}"
    log.info(f"Connecting Appium to {serial} via {appium_url}")

    driver = appium_webdriver.Remote(appium_url, options=options)
    return driver


def process_account(
    account: dict,
    place_name: str,
    latitude: float,
    longitude: float,
    review_text: str | None,
    rating: int,
    avd_name: str,
    emulator_port: int,
    proxy_manager: ProxyManager,
    account_manager: AccountManager,
    emulator_manager: EmulatorManager,
    screenshot_dir: Path,
) -> bool:
    email = account["email"]
    password = account["password"]

    result = {
        "email": email,
        "place_name": place_name,
        "rating": rating,
        "status": "failed",
        "error": None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    serial = None
    driver = None

    try:
        # --- Get proxy ---
        proxy = proxy_manager.get_proxy()
        if proxy:
            log.info(f"Using proxy: {proxy['host']}:{proxy['port']}")

        # --- Spoof device identity ---
        device_profile = get_random_profile()
        log.info(f"Device profile: {device_profile['model']} (IMEI: {device_profile['imei']})")

        # --- Boot emulator ---
        serial = emulator_manager.boot_emulator(
            avd_name=avd_name,
            port=emulator_port,
            proxy=proxy,
            wipe_data=True,
        )

        if not serial:
            result["error"] = "emulator_boot_failed"
            save_result(result)
            return False

        # --- Apply device spoofing ---
        apply_device_props(serial, device_profile)

        # --- Set GPS location ---
        set_gps_location(serial, latitude, longitude)

        # --- Connect Appium ---
        driver = create_appium_driver(serial, config.APPIUM_PORT)

        # --- Login to Google Account ---
        auth = GoogleAuth(driver, serial)
        logged_in = auth.login(email, password)

        if not logged_in:
            result["error"] = "login_failed"
            account_manager.mark_failed(email, "login")
            save_result(result)
            return False

        time.sleep(random.uniform(3, 6))

        # --- Open Google Maps ---
        maps = MapsAutomation(driver)
        if not maps.open_maps():
            result["error"] = "maps_open_failed"
            save_result(result)
            return False

        # --- Simulate natural browsing ---
        maps.simulate_browsing(duration=random.randint(8, 20))

        # --- Search for the place ---
        if not maps.search_place(place_name):
            result["error"] = "search_failed"
            save_result(result)
            return False

        time.sleep(random.uniform(2, 4))

        # --- Simulate reading the place details ---
        maps.simulate_browsing(duration=random.randint(5, 15))

        # --- Post review ---
        if review_text is None:
            review_text = generate_review(place_name=place_name, rating=rating)

        posted = maps.post_review(review_text, rating)

        if posted:
            result["status"] = "success"
            result["review_text"] = review_text
            account_manager.mark_used(email)
            log.info(f"Review posted by {email}")

            # Screenshot as proof
            screenshot_path = screenshot_dir / f"{email.replace('@', '_at_')}_{int(time.time())}.png"
            emulator_manager.take_screenshot(serial, str(screenshot_path))
        else:
            result["error"] = "review_post_failed"
            log.error(f"Review posting failed for {email}")

        save_result(result)
        return posted

    except Exception as e:
        result["error"] = str(e)
        log.error(f"Error processing {email}: {e}")
        save_result(result)
        return False

    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
        if serial:
            emulator_manager.kill_emulator(serial)


@click.group()
def cli():
    """Google Maps Review Bot - Mobile Emulation / Appium"""
    pass


@cli.command()
@click.option("--place", required=True, help="Place name to search on Google Maps")
@click.option("--lat", required=True, type=float, help="Latitude of the place")
@click.option("--lon", required=True, type=float, help="Longitude of the place")
@click.option("--avd", default="review_bot_avd", help="AVD name to use")
@click.option("--accounts", default=None, type=int, help="Number of accounts (default: all)")
@click.option("--rating-min", default=config.DEFAULT_MIN_RATING, help="Min star rating")
@click.option("--rating-max", default=config.DEFAULT_MAX_RATING, help="Max star rating")
@click.option("--review", default=None, help="Custom review text (default: auto-generated)")
@click.option("--delay-min", default=config.BETWEEN_ACCOUNTS_MIN, help="Min delay between accounts (seconds)")
@click.option("--delay-max", default=config.BETWEEN_ACCOUNTS_MAX, help="Max delay between accounts (seconds)")
@click.option("--port", default=5554, type=int, help="Emulator port (default: 5554)")
def run(place, lat, lon, avd, accounts, rating_min, rating_max, review, delay_min, delay_max, port):
    """Run the review bot for a Google Maps place."""

    if not config.OPENAI_API_KEY:
        log.error("OPENAI_API_KEY not set. Check your .env file.")
        sys.exit(1)

    account_manager = AccountManager(config.ACCOUNTS_FILE)
    proxy_manager = ProxyManager(config.PROXY_LIST_FILE)
    emulator_manager = EmulatorManager()

    active_accounts = account_manager.get_active_accounts()
    if not active_accounts:
        log.error("No active accounts found")
        sys.exit(1)

    if accounts:
        active_accounts = active_accounts[:accounts]

    # Check AVD exists
    available_avds = emulator_manager.list_avds()
    if avd not in available_avds:
        log.warning(f"AVD '{avd}' not found. Creating it...")
        if not emulator_manager.create_avd(avd):
            log.error("Failed to create AVD")
            sys.exit(1)

    # Pre-generate all reviews via OpenAI in one batch
    pre_generated = []
    if review is None:
        log.info(f"Pre-generating {len(active_accounts)} reviews via OpenAI...")
        pre_generated = generate_batch_reviews(
            place_name=place,
            count=len(active_accounts),
            rating_range=(rating_min, rating_max),
        )

    log.info(f"Starting bot with {len(active_accounts)} accounts")
    log.info(f"Target: {place} ({lat}, {lon})")
    log.info(f"Rating range: {rating_min}-{rating_max}")
    log.info(f"Review engine: OpenAI ({config.OPENAI_MODEL})")
    log.info(f"AVD: {avd}")

    screenshot_dir = Path("screenshots")
    screenshot_dir.mkdir(exist_ok=True)

    success_count = 0
    fail_count = 0

    for i, account in enumerate(active_accounts):
        # Use pre-generated review or custom text
        if review:
            this_review = review
            this_rating = random.randint(rating_min, rating_max)
        elif i < len(pre_generated):
            this_review = pre_generated[i]["text"]
            this_rating = pre_generated[i]["rating"]
        else:
            this_review = None
            this_rating = random.randint(rating_min, rating_max)

        log.info(f"\n{'='*60}")
        log.info(f"Account {i+1}/{len(active_accounts)}: {account['email']}")
        log.info(f"Rating: {this_rating} | Review: {(this_review or 'will generate')[:50]}...")
        log.info(f"{'='*60}")

        success = process_account(
            account=account,
            place_name=place,
            latitude=lat,
            longitude=lon,
            review_text=this_review,
            rating=this_rating,
            avd_name=avd,
            emulator_port=port,
            proxy_manager=proxy_manager,
            account_manager=account_manager,
            emulator_manager=emulator_manager,
            screenshot_dir=screenshot_dir,
        )

        if success:
            success_count += 1
        else:
            fail_count += 1

        # Delay between accounts
        if i < len(active_accounts) - 1:
            delay = random.randint(delay_min, delay_max)
            log.info(f"Waiting {delay}s before next account...")
            time.sleep(delay)

    log.info(f"\n{'='*50}")
    log.info(f"DONE: {success_count} success, {fail_count} failed out of {len(active_accounts)}")
    log.info(f"{'='*50}")


@cli.command()
@click.option("--name", default="review_bot_avd", help="AVD name")
@click.option("--device", default=None, help="Device type (e.g., pixel_6)")
@click.option("--api", default=None, type=int, help="Android API level")
def setup(name, device, api):
    """Create an AVD for the bot."""
    emulator_manager = EmulatorManager()

    if emulator_manager.create_avd(name, device, api):
        log.info(f"AVD '{name}' created. You can now use: python main.py run --avd {name} ...")
    else:
        log.error("AVD creation failed. Ensure Android SDK and system images are installed.")


@cli.command()
def status():
    """Show account status and results summary."""
    account_manager = AccountManager(config.ACCOUNTS_FILE)

    active = len(account_manager.get_active_accounts())
    total = len(account_manager.accounts)
    banned = len([a for a in account_manager.accounts if a.get("status") == "banned"])
    failed = len([a for a in account_manager.accounts if "failed" in a.get("status", "")])

    log.info(f"Accounts: {total} total, {active} active, {banned} banned, {failed} failed")

    results = load_results()
    if results:
        success = len([r for r in results if r["status"] == "success"])
        failed_r = len([r for r in results if r["status"] == "failed"])
        log.info(f"Reviews: {success} posted, {failed_r} failed")

    # Show running emulators
    emulator_manager = EmulatorManager()
    running = emulator_manager.get_running_emulators()
    log.info(f"Running emulators: {len(running)} ({', '.join(running) if running else 'none'})")


@cli.command()
def list_avds():
    """List available Android Virtual Devices."""
    emulator_manager = EmulatorManager()
    avds = emulator_manager.list_avds()
    if avds:
        for avd in avds:
            log.info(f"  - {avd}")
    else:
        log.info("No AVDs found. Run: python main.py setup")


@cli.command()
@click.option("--place-name", default="a local restaurant", help="Place name")
@click.option("--count", default=5, help="Number of review samples")
def preview(place_name, count):
    """Preview OpenAI-generated review texts."""
    if not config.OPENAI_API_KEY:
        log.error("OPENAI_API_KEY required for preview. Check .env file.")
        sys.exit(1)

    log.info(f"Generating {count} reviews for: {place_name}\n")
    reviews = generate_batch_reviews(place_name, count=count, rating_range=(4, 5))

    for r in reviews:
        log.info(f"  [{r['rating']} stars] {r['text']}")


if __name__ == "__main__":
    cli()
