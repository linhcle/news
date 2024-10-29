import logging
from playwright.sync_api import Playwright, sync_playwright, TimeoutError
import re

def scrape_issue_links(page):
    """Scrape all issue links from the homepage."""
    issue_links = []
    try:
        posts = page.locator('a[data-testid="post-preview-title"]')

        if posts.count() == 0:
            logging.info("No posts found.")
        else:
            logging.info(f"Found {posts.count()} posts.")
            for i in range(posts.count()):
                link = posts.nth(i).get_attribute("href")
                issue_links.append(link)
        logging.error("Timed out waiting for posts to load.")
    except Exception as e:
        logging.error(f"Error while scraping issue links: {e}")

    return issue_links

def scrape_issue_content(page):
    """Extract content and metadata from an issue page."""
    try:
        # Wait for the content div to load
        page.wait_for_selector('div.body.markup', timeout=10000)

        all_texts = page.locator('div.body.markup').all_inner_texts()

        # Join the texts with newlines and strip extra spaces
        content = '\n'.join([text.strip() for text in all_texts])
        title = page.title()

        return {
            'title': title,
            'summary': content,
            'link': page.url
        }
    except Exception as e:
        logging.error(f"Error while scraping issue content: {e}")
        return None

def clean_content(content):
    cleaned_content = re.sub(r'[^a-zA-Z0-9\s.,!?;:\-—]', '', content)
    cleaned_content = re.sub(r'([—-])\n+', r'\1', cleaned_content)
    cleaned_content = re.sub(r'(?<=\w)\n(?=\w)', ' ', cleaned_content)
    cleaned_content = re.sub(r'(?<=[.,!?;])\n(?=\w)', ' ', cleaned_content)
    cleaned_content = re.sub(r'(?<=\w)\n(?=[.,!?;])', '', cleaned_content)
    cleaned_content = re.sub(r'\s*The Rundown:', r'\nThe Rundown:', cleaned_content)
    cleaned_content = re.sub(r'\n{2,}', '\n', cleaned_content)
    cleaned_content = re.sub(r'\s+(?=[.,!?;])', '', cleaned_content)
    cleaned_content = re.sub(r'(?<=[.,!?;])\s+', ' ', cleaned_content)
    cleaned_content = re.sub(r'\s*Takeaway:', r'\nTakeaway:', cleaned_content)
    cleaned_content = re.sub(r'\s*Takeaway\n:', r'\nTakeaway:\n', cleaned_content)
    return cleaned_content.strip()

def extract_story_name_and_source(content):
    story_titles = []
    pattern_between_sections = r'Find Out More\s*(.*?)\s*The Rundown:'
    matches_between_sections = re.findall(pattern_between_sections, content, re.DOTALL)

    for section in matches_between_sections:
        sentences = re.split(r'(?<=[.!?])\s+', section.strip())
        for sentence in reversed(sentences):
            if ',' in sentence:
                story_titles.append(sentence.strip())
                break

    pattern_takeaway = r'Takeaway:\s*(.*?)\s*The Rundown:'
    takeaway_sections = re.findall(pattern_takeaway, content, re.DOTALL)

    for section in takeaway_sections:
        sentences = re.split(r'(?<=[.!?])\s+', section.strip())
        for sentence in reversed(sentences):
            if ',' in sentence:
                story_titles.append(sentence.strip())
                break

    for title in story_titles:
        content = content.replace(title, '', 1)

    return story_titles, content

def filter_stories(content, keywords=["merger", "acquisition", "acquire", "m&a", "merge", "fund"]):
    filtered_stories = []
    story_titles, modified_content = extract_story_name_and_source(content)
    for title in story_titles:
        if any(keyword.lower() in title.lower() for keyword in keywords):
            filtered_stories.append(title)

    return filtered_stories

def insert_story_titles(content):
    rundown_pattern = r'The Rundown:(.*?)(?=(Takeaway:|$))'
    rundowns = re.findall(rundown_pattern, content, re.DOTALL)
    story_titles, modified_content = extract_story_name_and_source(content)

    for i, (rundown, _) in enumerate(rundowns):
        if i < len(story_titles):
            title = story_titles[i]
            modified_content = modified_content.replace(
                f'The Rundown:{rundown}', f'\n{title}\n\nThe Rundown:{rundown}'
            )
    return modified_content

def final_clean_content(content):
    cleaned_content = re.sub(r'.*?\n([A-Z][^\n]+?, [^\n]+)\n', r'\1\n', content, 1, flags=re.DOTALL)
    cleaned_content = re.sub(r'Show Some Love.*', '', cleaned_content, flags=re.DOTALL)
    cleaned_content = re.sub(r'\n{2,}', '\n\n', cleaned_content)
    return cleaned_content.strip()



def fetch_fintech_radar_articles(playwright: Playwright):
    """Main function to fetch and process articles."""
    browser = playwright.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
    context = browser.new_context()
    page = context.new_page()

    # Navigate to the Substack homepage or archive page
    page.goto("https://fintechradar.substack.com/archive?sort=new", timeout=60000)

    # Scrape all issue links from the homepage
    issue_links = scrape_issue_links(page)
    all_issues_data = []

    # Visit each issue link and extract content
    for url in issue_links:
        try:
            logging.info(f"Visiting {url}...")
            page.goto(url, timeout=60000)
            issue_data = scrape_issue_content(page)
            clean_text = clean_content(issue_data['summary'])
            filtered_stories = filter_stories(clean_text)
            if filtered_stories:
                modified_content = insert_story_titles(clean_text)
                final_content = final_clean_content(modified_content)
                issue_data = {
                'title': issue_data['title'] if issue_data['title'] else 'No Title',
                'summary': final_content,
                'link': url
            }
                all_issues_data.append(issue_data)
        except Exception as e:
            logging.error(f"Failed to scrape {url}: {e}")

    context.close()
    browser.close()

    return all_issues_data

def main():
    """Main entry point for running the script."""
    logging.basicConfig(level=logging.INFO)

    with sync_playwright() as playwright:
        articles = fetch_fintech_radar_articles(playwright)
        logging.info(f"Fetched {len(articles)} articles.")

if __name__ == "__main__":
    main()
