import os
import logging
from playwright.sync_api import sync_playwright

# Disable Streamlit file watcher to prevent inotify limit errors
os.environ["STREAMLIT_WATCH_FILE"] = "false"

# Set Playwright browser path and skip browser download
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "/home/appuser/.cache/ms-playwright"
os.environ["PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD"] = "0"

def install_chromium():
    """Install Chromium for Playwright."""
    try:
        logging.info("Installing Chromium...")
        result = os.system("playwright install chromium --with-deps")
        if result != 0:
            logging.error("Failed to install Chromium.")
        else:
            logging.info("Chromium installed successfully.")
        
        # Log the installation directory
        os.system("ls -alh /home/appuser/.cache/ms-playwright/")
    except Exception as e:
        logging.error(f"Error during Chromium installation: {e}")

def scrape_substack():
    """Scrape links from Fintech Radar Substack."""
    links = []
    try:
        with sync_playwright() as p:
            logging.info("Launching Chromium...")
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox"]
            )
            page = browser.new_page()

            url = "https://fintechradar.substack.com"
            page.goto(url)
            posts = page.locator('a[data-testid="post-preview-title"]')

            if posts.count() == 0:
                logging.info("No posts found.")
            else:
                for i in range(posts.count()):
                    link = posts.nth(i).get_attribute("href")
                    logging.info(link)
                    links.append(link)

            browser.close()
    except Exception as e:
        logging.error(f"Error launching Chromium or scraping data: {e}")

    return links

def main():
    logging.basicConfig(level=logging.INFO)
    install_chromium()  # Install Chromium before scraping
    links = scrape_substack()  # Perform the scraping
    logging.info(f"Scraped links: {links}")

if __name__ == "__main__":
    main()
