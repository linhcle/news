import re
from playwright.sync_api import Playwright, sync_playwright, TimeoutError

def run(playwright: Playwright) -> None:
    """Automate interaction with the Fintech Radar Substack using Playwright."""
    try:
        # Launch the browser in non-headless mode for testing purposes
        browser = playwright.chromium.launch(headless=False)  
        context = browser.new_context()
        page = context.new_page()

        # Navigate to the Substack homepage
        page.goto("https://fintechradar.substack.com/", timeout=60000)

        # Handle the "Maybe Later" modal if it exists
        try:
            maybe_later_button = page.get_by_test_id("maybeLater")
            if maybe_later_button.is_visible():
                maybe_later_button.click()
                print("Clicked 'Maybe Later'.")
        except TimeoutError:
            print("'Maybe Later' modal not found. Continuing...")

        # Click on a specific issue link using role-based selector
        page.get_by_role("link", name=re.compile(r"Issue #133: Stripe To Buy", re.IGNORECASE)).click()
        print("Navigated to Issue #133.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Ensure resources are closed properly
        context.close()
        browser.close()

# Run the Playwright automation
with sync_playwright() as playwright:
    run(playwright)
