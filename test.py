import os
import logging
from playwright.sync_api import sync_playwright

# Step 1: Configure environment variables for Playwright
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "/home/appuser/.cache/ms-playwright"  # Ensure correct browser path

# Step 2: Install Chromium if it’s not already installed
def install_chromium():
    try:
        os.system("playwright install chromium")  # Install Chromium at runtime
        logging.info("Chromium installed successfully.")
    except Exception as e:
        logging.error(f"Failed to install Chromium: {e}")

# Step 3: Function to scrape using Playwright
def scrape_substack():
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)  # Use headless mode
            page = browser.new_page()
            page.goto("https://fintechradar.substack.com")
            print(page.title())  # For testing, replace with your scraping logic
            browser.close()
    except Exception as e:
        logging.error(f"Error launching Chromium: {e}")

# Step 4: Main entry point for your Streamlit app
def main():
    logging.basicConfig(level=logging.INFO)  # Enable logging for debugging
    install_chromium()  # Ensure Chromium is installed
    scrape_substack()   # Perform the scraping task

if __name__ == "__main__":
    main()  # Run the Streamlit app logic
