# app.py
import streamlit as st
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from fintechradar import fetch_fintech_radar_articles
from llm import small_summary
import requests
import re 
from playwright.sync_api import Playwright, sync_playwright, TimeoutError
import os


os.system("playwright install chromium")

# RSS Feeds for Different Outlets
rss_feeds = {
    "WSJ": [
        "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
        "https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml",
    ],
    "BBC News": ["http://feeds.bbci.co.uk/news/rss.xml?edition=us"],
}

# Add Fintech Radar as a new option
rss_feeds["Fintech Radar"] = None  # No RSS; handled differently

# Keywords to filter articles
keywords = [
    "merge", "M&A", "acquisition", "takeover", "joint venture", 
    "divestiture", "merger agreement", "IPO", "public offering", 
    "capital raise", "supply chain", "manufacturing", 
    "inventory", "output", "distribution", "operations", 
    "finance", "funding", "investment", "private equity", 
    "venture capital", "debt", "interest rates", "inflation", 
    "monetary policy", "bank", "central bank", "credit", 
    "lending",  "technology", "artificial intelligence", 
    "AI", "cloud computing", "blockchain", 
    "fintech", "semiconductor", "chip", "processor", "microchip", 
    "Nvidia", "TSMC", "Intel", "ARM",
    "fed", "Federal Reserve", "central bank policy", "GDP", 
    "recession", "inflation report", "quantitative easing", 
    "quarter", "fiscal quarter", "earnings report", 
    "guidance", "forecast", "valuation", "stock market", 
    "bonds", "commodities", "exchange rates", "foreign exchange", 
    "real estate",
    "ESG", "sustainability"
]

keywords_fintech = [
    "merge", "M&A", "acquisition", "acquire"
]
# Initialize session state to track selected outlet
if 'selected_outlet' not in st.session_state:
    st.session_state.selected_outlet = None
# Headers with Referer for Each Outlet
headers_referer = {
    "WSJ": "https://www.wsj.com/",
    "BBC News": "http://bbci.co.uk/",
}

# Common Headers
headers_template = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}

# Initialize session state to track the selected outlet
if 'selected_outlet' not in st.session_state:
    st.session_state.selected_outlet = None

def reset_outlet():
    st.session_state.selected_outlet = None

def apply_global_font(outlet_name):
    font_styles = {
        "WSJ": "Exchange, Georgia, Times, serif",
        "BBC News": "Reith Sans, Arial, sans-serif",
        "Reuters": "Noto Sans, Arial, sans-serif",
    }
    font_family = font_styles.get(outlet_name, "Arial, sans-serif")

    # Inject the global CSS
    st.markdown(
        f"""
        <style>
        html, body, [class*="css"] {{
            font-family: {font_family};
            color: #333333;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )


# Fetch RSS feeds and merge them if necessary
def fetch_and_merge_feeds(outlet_name, feed_urls):
    headers = headers_template.copy()
    headers['Referer'] = headers_referer.get(outlet_name, "")
    merged_entries = []

    # Fetch and parse each feed, and collect entries
    for url in feed_urls:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            feed = feedparser.parse(response.content)
            merged_entries.extend(feed.entries)
        else:
            st.error(f"Failed to load articles from {outlet_name}. (Status Code: {response.status_code})")

    # Remove duplicate articles based on title
    unique_entries = {}
    for entry in merged_entries:
        if entry.title not in unique_entries:
            unique_entries[entry.title] = entry

    return list(unique_entries.values())


def parse_article(article):
    """Extracts the title, subtitles, and rundowns from the article string."""
    # Use regex to split by one or more consecutive newlines
    sections = re.split(r'\n\s*\n', article.strip())
    # Initialize a list to store subtitles and rundowns
    stories = []

    # Process the remaining sections in pairs (subtitle, rundown)
    for i in range(0, len(sections)-1, 2):
        subtitle = sections[i].strip()  # Extract subtitle
        # Split the rundown by "Takeaway:" if it exists
        rundown_parts = re.split(r'Takeaway:\s*', sections[i + 1].strip(), maxsplit=1)
        rundown = rundown_parts[0].replace("The Rundown:", "").strip()  # Everything before "Takeaway:"
        takeaway = rundown_parts[1].replace("Takeaway:", "").strip() if len(rundown_parts) > 1 else "No Takeaway Available"

        # Store the parsed data in the stories list
        stories.append((subtitle, rundown, takeaway))

    return stories

def cookie_string_to_dict(cookie_string):
    # Split the cookie string by '; ' to get individual key-value pairs
    cookies = cookie_string.split('; ')
    
    # Split each pair by '=' and store them in a dictionary
    cookie_dict = {}
    for cookie in cookies:
        key, value = cookie.split('=', 1)  # Split only on the first '='
        cookie_dict[key] = value

    return cookie_dict

    
def display_articles(outlet_name, feed_urls):
    st.title(f"{outlet_name}")

    today = datetime.today()
    start_date = today - timedelta(days=7)

    if outlet_name == "Fintech Radar":
        with sync_playwright() as playwright:
            issues = fetch_fintech_radar_articles(playwright)
        for issue in issues:
            # print(issue)
            stories = parse_article(issue['summary'])
            for subtitle, rundown, takeaway in stories:
            # Check if any keyword matches within the entire article content
                if (any(keyword.lower() in rundown.lower() for keyword in keywords_fintech)) or (any(keyword.lower() in takeaway.lower() for keyword in keywords_fintech)):
                    insights = small_summary(rundown+takeaway)
                    st.markdown(
                        f"""
                        <div style="
                            background-color: #ffffff;
                            padding: 20px;
                            margin-bottom: 15px;
                            border-radius: 10px;
                            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                        ">
                            <h3 style="color: #001f3f;">{issue['title']}</h3>
                            <p style="font-style: italic; color: #555555;">{subtitle}</p>
                            <p><strong>The Rundown:</strong> {rundown}</p>
                            <p><strong>Takeaway:</strong> {takeaway}</p>
                            <p><strong>Summary:</strong> {insights}</p>
                            <a href="{issue['link']}" target="_blank" style="text-decoration: none; color: #1a73e8;">
                            🔗 Read full issue
                        </a>
                        </div>
                        """, unsafe_allow_html=True
                    )

    else:
        articles = fetch_and_merge_feeds(outlet_name, feed_urls)
        for entry in articles:
            if any(keyword.lower() in (entry['title'] + entry['summary']).lower() for keyword in keywords):
                # if start_date <= entry['published'] <= today:
                 # Display article details in Streamlit
                st.subheader(entry.title)
                st.write(f"**Summary:** {entry.summary}")
                st.write(f"**Article Type:** {entry.get('wsj_articletype', 'N/A')}")
                st.write(f"**Link to Article:** {entry.link}")
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36',
                    'Referer': 'https://www.wsj.com/',
                    'Accept-Language': 'en-US,en;q=0.9',
                }
                st.button("Back to Landing Page", on_click=reset_outlet)


# Landing Page: Display buttons for each news outlet
if st.session_state.selected_outlet is None:
    st.title("Hubby Tung's Special Newsletter")
    st.subheader("Choose a News Outlet")

    # Display a button for each outlet with a lambda function
    for outlet_name in rss_feeds.keys():
        st.button(outlet_name, on_click=lambda o=outlet_name: st.session_state.__setitem__('selected_outlet', o))

# Display articles for the selected outlet
else:
    apply_global_font(st.session_state.selected_outlet)
    display_articles(st.session_state.selected_outlet, rss_feeds[st.session_state.selected_outlet])


st.markdown(
    """
    <hr style="border:1px solid #eee; margin-top: 50px;" />
    <footer style="text-align: center; font-size: small;">
        Made with ❤️ by your wifey
    </footer>
    """, unsafe_allow_html=True
)