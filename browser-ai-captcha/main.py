import asyncio
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

import click

import config
from core.account_manager import AccountManager
from core.proxy_manager import ProxyManager
from core.captcha_solver import CaptchaSolver
from core.browser import StealthBrowser
from core.google_auth import GoogleAuth
from core.review_poster import ReviewPoster
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


async def process_account(
    account: dict,
    place_url: str,
    place_name: str,
    review_text: str | None,
    rating: int,
    proxy_manager: ProxyManager,
    captcha_solver: CaptchaSolver,
    account_manager: AccountManager,
    screenshot_dir: Path,
):
    email = account["email"]
    password = account["password"]

    result = {
        "email": email,
        "place_url": place_url,
        "rating": rating,
        "status": "failed",
        "error": None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    proxy = proxy_manager.get_playwright_proxy()
    if proxy:
        log.info(f"Using proxy: {proxy['server']}")

    browser = StealthBrowser(proxy=proxy)

    try:
        page = await browser.launch()

        # Load existing cookies if available
        cookie_path = f"cookies/{email.replace('@', '_at_')}.json"
        await browser.load_cookies(cookie_path)

        # --- Login ---
        auth = GoogleAuth(page, captcha_solver)
        logged_in = await auth.login(email, password)

        if not logged_in:
            result["error"] = "login_failed"
            log.error(f"Login failed for {email}")
            account_manager.mark_captcha_failed(email)
            save_result(result)
            return False

        # Save cookies for future sessions
        Path("cookies").mkdir(exist_ok=True)
        await browser.save_cookies(cookie_path)

        # --- Generate review via OpenAI ---
        if review_text is None:
            review_text = generate_review(place_name=place_name, rating=rating)

        poster = ReviewPoster(page)
        posted = await poster.post_review(place_url, review_text, rating)

        if posted:
            result["status"] = "success"
            result["review_text"] = review_text
            account_manager.mark_used(email)
            log.info(f"Review posted by {email}")

            screenshot_path = screenshot_dir / f"{email.replace('@', '_at_')}_{int(datetime.now().timestamp())}.png"
            await poster.screenshot(str(screenshot_path))
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
        await browser.close()


@click.group()
def cli():
    """Google Maps Review Bot - Browser Automation + OpenAI CAPTCHA Solver"""
    pass


@cli.command()
@click.option("--place-url", required=True, help="Google Maps place URL")
@click.option("--place-name", required=True, help="Place name (used for AI review generation)")
@click.option("--accounts", default=None, type=int, help="Number of accounts to use (default: all)")
@click.option("--rating-min", default=config.DEFAULT_MIN_RATING, help="Minimum star rating")
@click.option("--rating-max", default=config.DEFAULT_MAX_RATING, help="Maximum star rating")
@click.option("--review", default=None, help="Custom review text (default: OpenAI-generated)")
@click.option("--delay-min", default=config.BETWEEN_ACCOUNTS_MIN, help="Min delay between accounts (seconds)")
@click.option("--delay-max", default=config.BETWEEN_ACCOUNTS_MAX, help="Max delay between accounts (seconds)")
def run(place_url, place_name, accounts, rating_min, rating_max, review, delay_min, delay_max):
    """Run the review bot for a Google Maps place."""

    if not config.OPENAI_API_KEY:
        log.error("OPENAI_API_KEY not set. Check your .env file.")
        sys.exit(1)

    account_manager = AccountManager(config.ACCOUNTS_FILE)
    proxy_manager = ProxyManager(config.PROXY_LIST_FILE)
    captcha_solver = CaptchaSolver()

    active_accounts = account_manager.get_active_accounts()
    if not active_accounts:
        log.error("No active accounts found")
        sys.exit(1)

    if accounts:
        active_accounts = active_accounts[:accounts]

    # Pre-generate all reviews via OpenAI in one batch (cheaper)
    pre_generated = []
    if review is None:
        log.info(f"Pre-generating {len(active_accounts)} reviews via OpenAI...")
        pre_generated = generate_batch_reviews(
            place_name=place_name,
            count=len(active_accounts),
            rating_range=(rating_min, rating_max),
        )

    log.info(f"Starting bot with {len(active_accounts)} accounts")
    log.info(f"Target: {place_name}")
    log.info(f"URL: {place_url}")
    log.info(f"Rating range: {rating_min}-{rating_max}")
    log.info(f"CAPTCHA solver: {config.CAPTCHA_SOLVER}")
    log.info(f"Proxies loaded: {proxy_manager.has_proxies}")

    screenshot_dir = Path("screenshots")
    screenshot_dir.mkdir(exist_ok=True)

    async def run_all():
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

            success = await process_account(
                account=account,
                place_url=place_url,
                place_name=place_name,
                review_text=this_review,
                rating=this_rating,
                proxy_manager=proxy_manager,
                captcha_solver=captcha_solver,
                account_manager=account_manager,
                screenshot_dir=screenshot_dir,
            )

            if success:
                success_count += 1
            else:
                fail_count += 1

            if i < len(active_accounts) - 1:
                delay = random.randint(delay_min, delay_max)
                log.info(f"Waiting {delay}s before next account...")
                await asyncio.sleep(delay)

        log.info(f"\n{'='*60}")
        log.info(f"DONE: {success_count} success, {fail_count} failed out of {len(active_accounts)}")
        log.info(f"{'='*60}")

    asyncio.run(run_all())


@cli.command()
def status():
    """Show account status and results summary."""
    account_manager = AccountManager(config.ACCOUNTS_FILE)

    active = len(account_manager.get_active_accounts())
    total = len(account_manager.accounts)
    banned = len([a for a in account_manager.accounts if a.get("status") == "banned"])
    blocked = len([a for a in account_manager.accounts if a.get("status") == "captcha_blocked"])

    log.info(f"Accounts: {total} total, {active} active, {banned} banned, {blocked} CAPTCHA-blocked")

    results = load_results()
    if results:
        success = len([r for r in results if r["status"] == "success"])
        failed = len([r for r in results if r["status"] == "failed"])
        log.info(f"Reviews: {success} posted, {failed} failed")


@cli.command()
@click.option("--place-name", default="a local restaurant", help="Place name")
@click.option("--count", default=5, help="Number of review samples to generate")
def preview(place_name, count):
    """Preview OpenAI-generated review texts."""
    if not config.OPENAI_API_KEY:
        log.error("OPENAI_API_KEY required for preview. Check .env file.")
        sys.exit(1)

    log.info(f"Generating {count} reviews for: {place_name}\n")
    reviews = generate_batch_reviews(place_name, count=count, rating_range=(4, 5))

    for i, r in enumerate(reviews):
        log.info(f"  [{r['rating']} stars] {r['text']}")


if __name__ == "__main__":
    cli()
