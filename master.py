# app.py
import streamlit as st
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from fintechradar import fetch_fintech_radar_articles
from llm import small_summary
import requests
import re 

# RSS Feeds for Different Outlets
rss_feeds = {
    "WSJ": [
        "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
        "https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml",
    ],
    "BBC News": ["http://feeds.bbci.co.uk/news/rss.xml?edition=us"],
    "CNN": ["http://rss.cnn.com/rss/money_latest.rss"],
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
    "AI", "machine learning", "cloud computing", "blockchain", 
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

def reset_outlet():
    st.session_state.selected_outlet = None

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

# Example cookie string from browser
cookie_string = "DJSESSION=country%3Dus%7C%7Ccontinent%3Dna%7C%7Cregion%3D; ccpaApplies=true; gdprApplies=false; regulationApplies=gdpr%3Afalse%2Ccpra%3Atrue%2Cvcdpa%3Atrue; vcdpaApplies=true; wsjregion=na%2Cus; s_ppv=WSJ_Article_Markets_Global%2520Autonomous%2520Driving%2520Tech%2520Company%2520Pony.ai%2520Files%2520for%2520IPO%2C18%2C18%2C1421; s_tp=7859; cX_P=m2b33gqtgokwf327; permutive-id=a96c17d7-df25-481b-876a-e135c0c470f3; datadome=ZfqQ~hy_Tto4B7x4oLSeeGsDQhSozIQ0Ijw~GxhQgz_91ixv6bPn1HDyr4T_yBvYdMfEZ7syDL5J1LANFu~KtE_OI6Wh3nutXJN6zsqFk34TFRzIofV7zLw3JVEbHexP; _fbp=fb.1.1729035503481.2052138784; _gcl_au=1.1.948539531.1729035504; _pin_unauth=dWlkPVlqUTRZekV5TWpFdFpUQmlPQzAwTXpBNExXSTNZbUl0TnpFeU5EWTNZakkzWldFNA; _screload=; _uetsid=c894b7908d8411ef960c6f217d45bdf4; _uetvid=91a3e5b08b4e11efbc819380aa10b6ff; _dj_id.9183=.1729035504.6.1729281759.1729278691.12f107b9-a44b-46c1-a281-d81cfbc8b484.d37cd409-430e-42e2-8f0a-f54be0a75f30.45c7ede2-6402-456a-868b-663238b18f5d.1729281240253.9; _dj_ses.9183=*; _dj_sp_id=334983e3-bfb9-4cdc-8c4e-8d45156e06cc; _ga=GA1.1.1581800930.1729035504; _ga_K2H7B9JRSS=GS1.1.1729281240.6.1.1729281758.47.0.0; _meta_cross_domain_id=bf253acc-0335-46a0-9308-76d0a9498939; _ncg_id_=c457f523-c17a-4883-9d5e-6d2e365bd34b; _ncg_sp_id.5378=c457f523-c17a-4883-9d5e-6d2e365bd34b.1729035504.7.1729281759.1729278691.1a149c29-f733-40fd-b252-68563d14dff5; _ncg_sp_ses.5378=*; _rdt_uuid=1729035503641.2b569a25-528f-4a93-86d9-75cc6abc72b7; _scid_r=-PVo8HF5O-5LTLJrVjlnJPCKJHoQM4VGESF0fA; ajs_anonymous_id=21c450e9-7e21-4b3e-8361-7f28e4c1091a; s_cc=true; _fbp=fb.1.1729035503481.2052138784; _scor_uid=55a6e3e51e7d464c83907cd0c7f3b673; _pctx=%7Bu%7DN4IgrgzgpgThIC5QCYCGBmAjAYwBwBYp90BWfAIwDYBOc7AE3swDN7zdyp6TvN7VMqagAZ8JbAHYRles2bZMuYZijKSw5NWyTK6YAHcIAKwC%2BiUAAcYUZgEsAHohCGjIADQgALgE8LUJwDCABogJiYekLAAyp6onpBOqAB2APZJ7iAQtp5QAJL0TtTIxVi4lJjouCTI%2BGUiwqFAA; _ncg_domain_id_=c457f523-c17a-4883-9d5e-6d2e365bd34b.1.1729035503.1760571503; _pcid=%7B%22browserId%22%3A%22m2b33gqtgokwf327%22%7D; utag_main=v_id:0192928c06c800121462795ad28505075001406d00b35$_sn:7$_se:10$_ss:0$_st:1729283556907$vapi_domain:wsj.com$_prevpage:WSJ_Home_US%20Home%20Page%3Bexp-1729285356909$ses_id:1729281240193%3Bexp-session$_pn:9%3Bexp-session; __eoi=ID=9ada9fb47331629d:T=1729035504:RT=1729281558:S=AA-AfjYn3Nsi5P3pWIE3kKB7bjJv; __gads=ID=cebbaa1ec367c456:T=1729035504:RT=1729281558:S=ALNI_MYTXGtiH6E2sjOV8aLL9xHnBGgb5g; __gpi=UID=00000f29f5031115:T=1729035504:RT=1729281558:S=ALNI_MYYsoX357jlK0Cf3JNiNYojNhbI9A; _pubcid=3dd956fd-40cd-4a23-bdaa-34fe88d055c5; _pubcid_cst=DCwOLBEsaQ%3D%3D; _lr_env_src_ats=true; usr_prof_v2=eyJwIjp7InBzIjowLjUsInEiOjAuNzF9LCJhIjp7ImVkIjoidHJ1ZSIsInIiOiIyMDIzLTA4LTE2VDAwOjAwOjAwLjAwMFoiLCJlIjoiMjA0My0wOC0xNVQwMDowMDowMC4wMDBaIiwicyI6IjIwMjMtMDgtMTZUMDA6MDA6MDAuMDAwWiIsInNiIjoiRWR1Y2F0aW9uYWwiLCJmIjoiMiBZZWFyIiwibyI6IlN0dWRlbnQgRGlnaXRhbCBQYWNrIiwiYXQiOiJTVFVERU5UIiwidCI6MTR9LCJjcCI6eyJlYyI6IlN0YWJsZSIsInBjIjowLjAxMTg1LCJwc3IiOjAuMzAxMSwidGQiOjQyOCwiYWQiOjI4LCJxYyI6NywicW8iOjE5LCJzY2VuIjp7ImNoZSI6MC4wMTYzMiwiY2huIjowLjAxNTk1LCJjaGEiOjAuMDExODUsImNocCI6MC4wMjUxNX19LCJvcCI6eyJqIjp7Imp0IjoibXNjIiwiamYiOiJzIiwiamkiOiJmcyJ9LCJpIjoiNDEwMDAwNDAifSwiaWMiOjZ9; _lr_sampling_rate=100; AMCV_CB68E4BA55144CAA0A4C98A5%40AdobeOrg=1585540135%7CMCIDTS%7C20014%7CMCMID%7C26896660438108245592336874403348510020%7CMCAID%7CNONE%7CMCOPTOUT-1729285892s%7CNONE%7CMCAAMLH-1729883492%7C7%7CMCAAMB-1729883492%7Cj8Odv6LonN4r3an7LhD3WZrU1bUpAkFkkiY1ncBR96t2PTI%7CMCSYNCSOP%7C411-20019%7CvVersion%7C4.4.0; _lr_geo_location=US; _lr_geo_location_state=NY; _ga_KY43GPPTM9=GS1.1.1729214834.1.1.1729214885.0.0.0; TR=V2-2a31c84e4354b69bcdd1fdb8bed5d51da1a9045c7906dffc1801e015029cc763; ca_id=eJxNkG9PgzAQh79LX4-tHYXSvXITNBjczMQ_iTGktNetCmwZRTTG727ZZuK7-z333OVy32hjPqApGlEDmqG8azZohLSoTfX1BzNwCGphKhdEVXZtBWPrzAouNgMey13tlK4zyhnAtFZSEo-xknk0otwro1J7OGQSAgxKaexsexDy_TgwFT6REQXqB7QMeSmVIlq5GVCBCogSRHBMA8k4DpXWkkSYACYBnnIpWei7ZYddBS2avaCrdZKsk2svXcbpYxo_zDPXfbq_8dK7eXwu58t4vUrjIp8vsiQ_w8v8-VzdrhZplpwCeh0h0dltYc3wCsKmwyU-5SMkDyAsqEJYx33OQhxy7rg5gn8ifO5PgDJ2BKZ1p6Kttft2Npn0fT_u27fhhxNZGWgs-vkFkdl2Lg.JnV5XrKzyl1T4RY0jh46tM9xWJHG4uxUi5CkHKV6wNhk7bCgNU--Zp7yXngV6RyVaTEcK1I_kXnoIqpfUe6oRDx_66MXgMupMzwVmahHov1wri1ABv1SAl4g74jXqLhfoyGVyvTJa33Rg1i7Rz4CKgP--_FwcGJNMAEAUQkwBIRGNA_BibE3N-dELkv3ab2ZVLfHjSxv2L87UHM2hoAcqiD7iigXmRqdu8u0MUVVVA2vYbB8zFLh7Bit3sDFh_Lcn-iJ0l46ms80yMkOv6LwMgwawriMq2hY7bBFR-YxI3x0qzE5-OWz7f3XvFpAgK-K0NVaNgZ8ya9DVvmW6pimkeXGShTGPqEvz2d1Dm9iVkegO8ZFaZ5awgEvTSvEHJCu2W_vMvxP4Scl48ou4EZFdueGfpZrT1OreyJaZ0CM3Fi8ePaVvUZbsbl6YBsrzmomQQRD09TY9qLNbKrPqM2Uw-1c_S1dUSqTTbmxsuDwAvZaRSjTY64J3tIL8e-HY46G8XugZ-FdTH0jOAeJmcRHZbfgOnpGqkCZj81k55Db5oWjxDC9xQ9HcXHmydTp7Gqmc94-BIa-kOXNRLPRZGPwy7sUacaNUWQKG-x7v-Umntn6K4zsst4_jD7vON7B68esSB9GPXX-9Hoei0xZ8VihGJFwA9zKJiftax36LKQ9RKk; ca_rt=HM7mYiQSSh4Q5lx8O1Zx-A.APRp2_1lWAeRupdh_HFXJJmshoCpCdpyBmjuW3MwTLSHXsSWCMtcdXkrTm1KC55SlMj0YKsLF9gQW2FnRM29OGxM9L1W_9ZqTEZyp8wiXzM; ab_uuid=08c81a86-ffc4-4ef4-9ba2-8fd6862c1216; AMCVS_CB68E4BA55144CAA0A4C98A5%40AdobeOrg=1; _sctr=1%7C1728964800000; cX_G=cx%3Ash35x335rpqg244id7tudlby0%3A1gx6s1c0gmo7e; _scid=5XVo8HF5O-5LTLJrVjlnJPCKJHoQM4VG; _sp_su=false; _meta_cross_domain_recheck=1729035503682; _meta_facebookTag_sync=1729035503482; _meta_googleAdsSegments_library_loaded=1729035503482; sub_type=WSJ-SUB; djcs_route=6ae12622-356b-46a8-b672-da41cc50790"

# Convert the string to a dictionary
cookies_dict = cookie_string_to_dict(cookie_string)


def display_articles(outlet_name, feed_urls):
    st.title(f"{outlet_name}")

    today = datetime.today()
    start_date = today - timedelta(days=7)

    if outlet_name == "Fintech Radar":
        issues = fetch_fintech_radar_articles()
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
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36',
                    'Referer': 'https://www.wsj.com/',
                    'Accept-Language': 'en-US,en;q=0.9',
                }
                response = requests.get(entry.link, cookies=cookies_dict, headers=headers)
                soup = BeautifulSoup(response.content, 'html.parser')
                paragraphs = soup.find_all('p')
                
                st.write("**Full Article Content:**")
                content = []
                stop_keywords = ["Copyright", "All Rights Reserved"]  # End signals
                skip_phrases = ["Advertisement", "Listen", "This copy is for", "www.djreprints.com"]  # Skip noise

                for paragraph in paragraphs:
                    text = paragraph.get_text().strip()
                    # Stop processing if we reach the "Copyright" section
                    if any(stop_word in text for stop_word in stop_keywords):
                        break

                    # Skip noisy or irrelevant paragraphs
                    if any(skip_phrase in text for skip_phrase in skip_phrases):
                        continue
                    if len(text) < 10:  # Skip very short paragraphs (like timestamps)
                        continue
                    content.append(text)
                    st.write(text)
                 # Optional: Fetch full article content using requests and BeautifulSoup
                if st.button(f"Show Summary - {entry.title}"):
                    content_str = '\n'.join(content)
                    summary = small_summary(content_str)
                    st.write(summary)
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
print(page.evaluate("() => navigator.userAgent"))
