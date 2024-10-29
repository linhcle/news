import os
import logging
from playwright.sync_api import sync_playwright

# Ensure Playwright uses the correct path and installs dependencies
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "/home/appuser/.cache/ms-playwright"

def install_chromium():
    """Install Chromium for Playwright at runtime."""
    try:
        os.system("playwright install chromium --with-deps")
        logging.info("Chromium installed successfully.")
    except Exception as e:
        logging.error(f"Failed to install Chromium: {e}")

def scrape_substack():
    """Scrape links from the Fintech Radar Substack page."""
    links = []
    try:
        with sync_playwright() as p:
            logging.info("Launching Chromium...")
            # Do not specify executable_path; let Playwright handle it
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox"]
            )
            page = browser.new_page()

            # Open the Substack page
            url = "https://fintechradar.substack.com"
            page.goto(url)

            # Find all post links using their anchor tag structure
            posts = page.locator('a[data-testid="post-preview-title"]')

            if posts.count() == 0:
                logging.info("No posts found on the page.")
            else:
                logging.info("Recent posts:")
                for i in range(posts.count()):
                    link = posts.nth(i).get_attribute("href")
                    logging.info(link)
                    links.append(link)

            browser.close()
    except Exception as e:
        logging.error(f"Error launching Chromium or scraping data: {e}")

    return links

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
    links = scrape_substack()
    logging.info(f"Scraped links: {links}")# Perform the scraping task

if __name__ == "__main__":
    main()  # Run the Streamlit app logic
