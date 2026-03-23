"""
ChromeLauncher — Launch real Chrome with CDP and connect via Playwright.

Starts Chrome as a subprocess with --remote-debugging-port (no --enable-automation),
waits for the CDP endpoint to be ready, and provides a Playwright connection.
"""
import asyncio
import subprocess
import platform
import urllib.request
import json


_CHROME_PATHS = {
    "Darwin": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "Linux": "/usr/bin/google-chrome",
    "Windows": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
}


class ChromeLauncher:
    def __init__(self, port: int = 9222, user_data_dir: str = "/tmp/chrome-nobot"):
        self.port = port
        self.user_data_dir = user_data_dir
        self._proc: subprocess.Popen | None = None

    # ── public ───────────────────────────────────────────

    async def start(self) -> None:
        """Launch Chrome and wait for the CDP port to be ready."""
        if await self._is_ready():
            print(f"[ChromeLauncher] CDP already listening on port {self.port}")
            return

        chrome_path = _CHROME_PATHS.get(platform.system())
        if not chrome_path:
            raise RuntimeError(f"Unsupported OS: {platform.system()}")

        args = [
            chrome_path,
            f"--remote-debugging-port={self.port}",
            f"--user-data-dir={self.user_data_dir}",
            "--no-first-run",
            "--no-default-browser-check",
            # NOTE: --enable-automation is deliberately excluded
        ]

        print(f"[ChromeLauncher] Starting Chrome on port {self.port}…")
        self._proc = subprocess.Popen(
            args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

        # Wait for CDP to become ready (max 10 seconds)
        for _ in range(20):
            if await self._is_ready():
                print("[ChromeLauncher] CDP ready.")
                return
            await asyncio.sleep(0.5)

        raise RuntimeError("Chrome did not start within 10 seconds")

    async def connect(self, playwright) -> tuple:
        """Connect Playwright to Chrome via CDP. Returns (browser, page)."""
        browser = await playwright.chromium.connect_over_cdp(
            f"http://localhost:{self.port}"
        )
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()
        return browser, page

    async def stop(self) -> None:
        """Terminate the Chrome process if we started it."""
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()
            self._proc.wait(timeout=5)
            print("[ChromeLauncher] Chrome stopped.")

    # ── private ──────────────────────────────────────────

    async def _is_ready(self) -> bool:
        try:
            url = f"http://localhost:{self.port}/json/version"
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=2) as resp:
                data = json.loads(resp.read())
                return "webSocketDebuggerUrl" in data
        except Exception:
            return False
