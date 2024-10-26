import streamlit as st
import feedparser
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

# RSS Feeds for Different Outlets
rss_feeds = {
    "WSJ": [
        "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
        "https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml",
    ],
    "BBC News": ["http://feeds.bbci.co.uk/news/rss.xml?edition=us"],
    "CNN": ["http://rss.cnn.com/rss/money_latest.rss"],
}
keywords = [
    "merge", "M&A", "acquisition", "takeover", "joint venture", 
    "divestiture", "merger agreement", "IPO", "public offering", 
    "capital raise", "production", "supply chain", "manufacturing", 
    "inventory", "output", "distribution", "operations", 
    "finance", "funding", "investment", "private equity", 
    "venture capital", "debt", "interest rates", "inflation", 
    "monetary policy", "bank", "central bank", "credit", 
    "lending", "tech", "technology", "artificial intelligence", 
    "AI", "machine learning", "cloud computing", "blockchain", 
    "fintech", "semiconductor", "chip", "processor", "microchip", 
    "Nvidia", "TSMC", "Intel", "ARM", "electronics", 
    "fed", "Federal Reserve", "central bank policy", "GDP", 
    "recession", "inflation report", "stimulus", "quantitative easing", 
    "quarter", "fiscal quarter", "earnings report", 
    "guidance", "forecast", "valuation", "stock market", 
    "bonds", "commodities", "exchange rates", "foreign exchange", 
    "real estate", "housing market", "commodities", "energy", 
    "oil", "gas", "renewable energy", "electric vehicles", 
    "ESG", "sustainability", "regulation", "compliance", 
    "data privacy", "cybersecurity", "risk management"
]

# Headers with Referer for Each Outlet
headers_referer = {
    "WSJ": "https://www.wsj.com/",
    "BBC News": "http://bbci.co.uk/",
    "CNN": "http://cnn.com"
}

# Common Headers
headers_template = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}

# Initialize session state to track the selected outlet
if 'selected_outlet' not in st.session_state:
    st.session_state.selected_outlet = None

# Callback function to reset the outlet selection
def reset_outlet():
    st.session_state.selected_outlet = None

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

def apply_global_font(outlet_name):
    font_styles = {
        "WSJ": "Exchange, Georgia, Times, serif",
        "BBC News": "Reith Sans, Arial, sans-serif",
        "Reuters": "Noto Sans, Arial, sans-serif",
        "CNN": "CNN Sans, Arial, Helvetica, sans-serif"
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



# Display articles for a specific news outlet
def display_articles(outlet_name, feed_urls):
    st.title(f"{outlet_name} - Articles")

    today = datetime.today()
    start_date = today - timedelta(days=7)

    # Fetch and merge articles
    articles = fetch_and_merge_feeds(outlet_name, feed_urls)

    # Loop through articles and display them
    for entry in articles:
        published_date = datetime(*entry.published_parsed[:6])
        if any(keyword.lower() in (entry.title + entry.summary).lower() for keyword in keywords):
            if start_date <= published_date <= today:
                st.markdown(
                    f"""
                    <div style="
                        background-color: #ffffff;
                        padding: 20px;
                        margin-bottom: 15px;
                        border-radius: 10px;
                        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                    ">
                        <h3 style="color: #001f3f;">{entry.title}</h3>
                        <p><strong>Published:</strong> {published_date.strftime('%Y-%m-%d')}</p>
                        <p><strong>Summary:</strong> {entry.summary}</p>
                        <a href="{entry.link}" target="_blank" style="text-decoration: none; color: #1a73e8;">
                            🔗 Read full article
                        </a>
                    </div>
                    """, unsafe_allow_html=True
                )

    # Back button to return to the landing page with a callback
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

# Footer
st.markdown(
    """
    <hr style="border:1px solid #eee; margin-top: 50px;" />
    <footer style="text-align: center; font-size: small;">
        Made with ❤️ by your wifey
    </footer>
    """, unsafe_allow_html=True
)
