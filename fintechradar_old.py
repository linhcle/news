import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
from playwright.sync_api import sync_playwright

BASE_URL = "https://fintechradar.substack.com/archive?sort=new"

# Set up Playwright with Chromium
def scrape_substack():
    links = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Open the Substack page
        url = "https://fintechradar.substack.com"
        page.goto(url)
        time.sleep(5)  # Wait for the page to fully load

        # Find all post links using their anchor tag structure
        posts = page.locator('a[data-testid="post-preview-title"]')

        if posts.count() == 0:
            print("No posts found on the page.")
        else:
            print("Recent posts:")
            for i in range(posts.count()):
                link = posts.nth(i).get_attribute("href")
                print(link)
                links.append(link)

        browser.close()
    return links

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

def fetch_fintech_radar_articles():
    issue_links = scrape_substack()
    all_issues_data = []

    for url in issue_links:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        content_div = soup.find('div', class_='body markup')
        content = content_div.get_text(separator='\n', strip=True) if content_div else 'No content found'
        print("content",content)
        clean_text = clean_content(content)
        filtered_stories = filter_stories(clean_text)

        if filtered_stories:
            modified_content = insert_story_titles(clean_text)
            final_content = final_clean_content(modified_content)
            date_obj = soup.find('time')['datetime'] if soup.find('time') else 'Unknown Date'

            issue_data = {
                'title': soup.title.string if soup.title else 'No Title',
                'summary': final_content,
                'published': date_obj,
                'link': url
            }
            all_issues_data.append(issue_data)
    return all_issues_data

# Run the script
if __name__ == "__main__":
    articles = fetch_fintech_radar_articles()
    print(f"Fetched {len(articles)} articles.")
