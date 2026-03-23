---
name: nobot
description: Human-like browser automation that bypasses bot detection using Real Chrome CDP.
version: 2.0.0
author: jujang
category: Automation / Browser
tags: [browser, bot-evasion, automation, human-like, cdp]
---

# Nobot — Human-like Browser Automation Skill

## Overview
A skill that controls Real Chrome via CDP to bypass bot detection (e.g., Akamai Bot Manager).
Runs the system Chrome with `--remote-debugging-port` instead of Playwright's bundled Chromium, and connects via `connect_over_cdp()` to maintain TLS/header fingerprints identical to consumer Chrome.

## Architecture

```
ChromeLauncher (scripts/chrome_launcher.py)
    └─ Real Chrome subprocess (--remote-debugging-port, NO --enable-automation)
        └─ Playwright connect_over_cdp()
            └─ HumanoidInteractor (scripts/humanoid_interactor.py)
                ├─ Bezier mouse movement + jitter
                ├─ Human-like typing (down/up for ASCII, type for Korean/CJK)
                ├─ Burst scrolling
                └─ Warm-up (mouse move, hover, scroll, scroll-back)
```

## Scripts

Scripts are located in the `scripts/` folder of this skill:

| File | Role |
|:---|:---|
| `scripts/chrome_launcher.py` | Real Chrome execution + CDP connection management |
| `scripts/humanoid_interactor.py` | Behavioral layer (mouse, keyboard, scroll, warm-up) |
| `scripts/coupang_simulator.py` | Coupang search simulator (for E2E verification) |

## Usage

### Running the Coupang Search Simulator
```bash
python -u .agents/skills/nobot/scripts/coupang_simulator.py
```
Searches first in English ("roborock") then in Korean ("로보락") and validates results.

### Direct Usage in Python
```python
import asyncio, sys, os
# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".agents/skills/nobot/scripts"))

from playwright.async_api import async_playwright
from chrome_launcher import ChromeLauncher
from humanoid_interactor import HumanoidInteractor

async def search_coupang(query: str):
    launcher = ChromeLauncher()
    await launcher.start()

    async with async_playwright() as p:
        browser, page = await launcher.connect(p)
        interactor = HumanoidInteractor(page)

        await page.goto("https://www.coupang.com", wait_until="commit", timeout=60000)
        await asyncio.sleep(4)

        # Warm-up: feed Sensor Script with natural events
        await interactor.warm_up()

        # Type and search
        search_input = "#wa-search-form input.headerSearchKeyword"
        search_btn = "#wa-search-form button.headerSearchBtn"
        await page.wait_for_selector(search_input, state="visible", timeout=15000)
        await interactor.human_type(search_input, query)
        await asyncio.sleep(1)
        await interactor.human_click(search_btn)
        await asyncio.sleep(5)

        # Extract results (site-specific JS)
        results = await page.evaluate("""...""")

        await browser.close()
    await launcher.stop()
    return results
```

## Site Selectors (Coupang)

| Element | Selector |
|:---|:---|
| Search Input | `#wa-search-form input.headerSearchKeyword` |
| Search Button | `#wa-search-form button.headerSearchBtn` |
| Product Item | `li[class*="ProductUnit"]` |

## Key Principles

1. **Real Chrome First** — Fingerprinting is not solved in code; Real Chrome generates the actual requests.
2. **No `--enable-automation`** — Automation flag is excluded from CDP connections. `navigator.webdriver = false`.
3. **Warm-Up Required** — Mouse/scroll events must be generated before searching (to feed the Sensor Script).
4. **Korean Input** — Use `keyboard.down/up` for ASCII characters and `keyboard.type()` for Korean/CJK.

## Extending to Other Sites

To add a new site:
1. Identify the search input/button selectors for the target site.
2. Write JS for result extraction (product item selector, title/price/ad extraction).
3. Use `scripts/coupang_simulator.py` as a reference to write a new simulator.
