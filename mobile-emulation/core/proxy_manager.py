import random
from pathlib import Path
from urllib.parse import urlparse
from utils.logger import log


class ProxyManager:
    def __init__(self, proxy_file: str):
        self.proxies: list[str] = []
        self._load(proxy_file)

    def _load(self, proxy_file: str):
        path = Path(proxy_file)
        if not path.exists():
            log.warning(f"Proxy file not found: {path}. Running without proxies.")
            return
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    self.proxies.append(line)
        log.info(f"Loaded {len(self.proxies)} proxies")

    def get_proxy(self) -> dict | None:
        """Return a random proxy parsed into components."""
        if not self.proxies:
            return None

        proxy_url = random.choice(self.proxies)
        parsed = urlparse(proxy_url)

        return {
            "url": proxy_url,
            "host": parsed.hostname,
            "port": parsed.port,
            "username": parsed.username,
            "password": parsed.password,
            "scheme": parsed.scheme or "http",
        }

    @property
    def has_proxies(self) -> bool:
        return len(self.proxies) > 0
