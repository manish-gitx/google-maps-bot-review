import random
from pathlib import Path
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
                    self.proxies.append(self._normalize(line))
        log.info(f"Loaded {len(self.proxies)} proxies")

    def _normalize(self, proxy: str) -> str:
        # Handle host:port:user:pass format
        if not proxy.startswith(("http://", "https://", "socks5://", "socks4://")):
            parts = proxy.split(":")
            if len(parts) == 4:
                host, port, user, password = parts
                return f"http://{user}:{password}@{host}:{port}"
            elif len(parts) == 2:
                return f"http://{proxy}"
        return proxy

    def get_proxy(self) -> dict | None:
        if not self.proxies:
            return None
        proxy_url = random.choice(self.proxies)
        return {"server": proxy_url}

    def get_playwright_proxy(self) -> dict | None:
        if not self.proxies:
            return None
        proxy_url = random.choice(self.proxies)

        # Parse proxy URL for Playwright format
        # Playwright expects: {"server": "host:port", "username": "user", "password": "pass"}
        from urllib.parse import urlparse
        parsed = urlparse(proxy_url)

        proxy_dict = {"server": f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"}
        if parsed.username:
            proxy_dict["username"] = parsed.username
        if parsed.password:
            proxy_dict["password"] = parsed.password

        return proxy_dict

    @property
    def has_proxies(self) -> bool:
        return len(self.proxies) > 0
