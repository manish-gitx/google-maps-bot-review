import json
from pathlib import Path
from datetime import datetime, timezone
from utils.logger import log


class AccountManager:
    def __init__(self, accounts_file: str):
        self.accounts_file = Path(accounts_file)
        self.accounts: list[dict] = []
        self._load()

    def _load(self):
        if not self.accounts_file.exists():
            log.error(f"Accounts file not found: {self.accounts_file}")
            return
        with open(self.accounts_file, "r") as f:
            self.accounts = json.load(f)
        log.info(f"Loaded {len(self.accounts)} accounts from {self.accounts_file}")

    def save(self):
        with open(self.accounts_file, "w") as f:
            json.dump(self.accounts, f, indent=2)

    def get_active_accounts(self) -> list[dict]:
        return [a for a in self.accounts if a.get("status") == "active"]

    def mark_used(self, email: str):
        for account in self.accounts:
            if account["email"] == email:
                account["last_used"] = datetime.now(timezone.utc).isoformat()
                account["reviews_posted"] = account.get("reviews_posted", 0) + 1
                break
        self.save()

    def mark_banned(self, email: str):
        for account in self.accounts:
            if account["email"] == email:
                account["status"] = "banned"
                log.warning(f"Account marked as banned: {email}")
                break
        self.save()

    def mark_failed(self, email: str, reason: str = "unknown"):
        for account in self.accounts:
            if account["email"] == email:
                account["status"] = f"failed_{reason}"
                log.warning(f"Account marked as failed ({reason}): {email}")
                break
        self.save()
