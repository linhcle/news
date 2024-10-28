import os
import logging
from playwright.sync_api import sync_playwright
import requests
from bs4 import BeautifulSoup
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

def fetch_fintech_radar_articles():
    issue_links = scrape_substack()
    all_issues_data = []

    for url in issue_links:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        content_div = soup.find('div', class_='body markup')
        content = content_div.get_text(separator='\n', strip=True) if content_div else 'No content found'

        if content:
            issue_data = {
                'title': soup.title.string if soup.title else 'No Title',
                'summary': content,
                'link': url
            }
            all_issues_data.append(issue_data)
    return all_issues_data
# Step 4: Main entry point for your Streamlit app
def main():
    logging.basicConfig(level=logging.INFO)  # Enable logging for debugging
    install_chromium()  # Ensure Chromium is installed
    scrape_substack()  
    fetch_fintech_radar_articles() # Perform the scraping task

if __name__ == "__main__":
    main()  # Run the Streamlit app logic
