import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, channel="chrome")
        page = await browser.new_page()

        console_errors = []
        page.on("console", lambda msg: console_errors.append(f"[{msg.type}] {msg.text}"))
        page.on("pageerror", lambda err: console_errors.append(f"[PAGE_ERROR] {err}"))

        await page.goto("http://localhost:5001/", wait_until="networkidle")
        print("=== Page loaded ===")

        # Switch to TikTok tab
        await page.click("button:has-text('TikTok')")
        await asyncio.sleep(1)
        print("=== After TikTok tab click ===")

        # Wait for data
        await asyncio.sleep(5)

        # Check for elements
        status_text = await page.text_content("#tiktok-status")
        print(f"Status: {status_text}")

        profile_html = await page.innerHTML("#tiktok-profile-cards")
        has_content = len(profile_html) > 100
        has_spinner = "loading" in profile_html
        print(f"Profile cards: {'CONTENT' if has_content else 'EMPTY'}, Spinner: {has_spinner}")
        print(f"Profile HTML length: {len(profile_html)}")

        fg_html = await page.innerHTML("#tiktok-follower-growth")
        print(f"Follower growth HTML: {fg_html[:200]}")

        # Check if renderTikTokAll ran
        videos_table = await page.innerHTML("#tiktok-videos-table")
        has_table = "<tr" in videos_table
        print(f"Videos table has rows: {has_table}")
        print(f"Videos table HTML: {videos_table[:200]}")

        # Print console errors
        print(f"\n=== Console errors ({len(console_errors)}) ===")
        for ce in console_errors:
            print(ce)

        await browser.close()

asyncio.run(main())
