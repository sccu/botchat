"""
HumanoidInteractor — Simulates human-like browser interactions.

Works with any Playwright Page (CDP or regular).
No stealth JS needed when using real Chrome via CDP.
"""
import asyncio
import random
from playwright.async_api import Page


class HumanoidInteractor:
    """Simulates human-like browser interactions to bypass bot detection."""

    def __init__(self, page: Page):
        self.page = page
        self._mouse_x = 0.0
        self._mouse_y = 0.0

    # ── helpers ──────────────────────────────────────────

    async def _wait(self, min_ms: int = 50, max_ms: int = 200):
        await asyncio.sleep(random.randint(min_ms, max_ms) / 1000.0)

    def _bezier(self, t: float, p0: float, p1: float, p2: float) -> float:
        return (1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t ** 2 * p2

    # ── mouse ────────────────────────────────────────────

    async def move_to(self, x: float, y: float, steps: int = 20):
        """Move mouse along a Bezier curve with micro-jitter."""
        sx, sy = self._mouse_x, self._mouse_y
        cx = (sx + x) / 2 + random.uniform(-80, 80)
        cy = (sy + y) / 2 + random.uniform(-80, 80)

        for i in range(1, steps + 1):
            t = i / steps
            nx = self._bezier(t, sx, cx, x) + random.uniform(-2, 2)
            ny = self._bezier(t, sy, cy, y) + random.uniform(-2, 2)
            await self.page.mouse.move(nx, ny)
            await self._wait(8, 25)

        self._mouse_x, self._mouse_y = x, y

    async def move_to_selector(self, selector: str):
        box = await self.page.locator(selector).bounding_box()
        if not box:
            raise RuntimeError(f"Element not found: {selector}")
        tx = box["x"] + box["width"] / 2 + random.uniform(-3, 3)
        ty = box["y"] + box["height"] / 2 + random.uniform(-3, 3)
        await self.move_to(tx, ty)

    async def human_click(self, selector: str):
        await self.move_to_selector(selector)
        await self._wait(200, 600)
        await self.page.mouse.down()
        await self._wait(40, 120)
        await self.page.mouse.up()

    # ── keyboard ─────────────────────────────────────────

    async def human_type(self, selector: str, text: str):
        """Type text character-by-character with human-like rhythm.

        Uses keyboard.down/up for ASCII chars (realistic key events)
        and keyboard.type for non-ASCII (Korean, CJK etc.).
        """
        await self.human_click(selector)
        await self._wait(300, 600)

        pause_after = random.randint(2, max(3, len(text) - 1))
        for i, char in enumerate(text):
            if char.isascii():
                await self.page.keyboard.down(char)
                await self._wait(40, 120)
                await self.page.keyboard.up(char)
            else:
                await self.page.keyboard.type(char, delay=random.randint(40, 120))
            await self._wait(80, 250)

            if i == pause_after:
                await self._wait(400, 900)  # thinking pause

    # ── scroll ───────────────────────────────────────────

    async def human_scroll(self, dy: int, bursts: int = 3):
        """Scroll in short bursts with pauses."""
        per_burst = dy // bursts
        for _ in range(bursts):
            await self.page.mouse.wheel(0, per_burst + random.randint(-30, 30))
            await self._wait(400, 1200)

    # ── warm-up ──────────────────────────────────────────

    async def warm_up(self):
        """Simulate casual browsing to feed Sensor Script with events."""
        vw = self.page.viewport_size
        if not vw:
            return

        # Move to centre
        await self.move_to(vw["width"] / 2, vw["height"] / 2)
        await self._wait(1000, 2000)

        # Hover over top nav area
        await self.move_to(
            random.uniform(200, vw["width"] - 200),
            random.uniform(100, 150),
        )
        await self._wait(500, 1500)

        # Scroll down
        await self.human_scroll(random.randint(300, 500))
        await self._wait(1000, 2000)

        # Scroll back up slightly
        await self.human_scroll(-random.randint(50, 120), bursts=1)
        await self._wait(500, 1000)
