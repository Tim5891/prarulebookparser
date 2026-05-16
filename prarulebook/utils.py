import re
import requests
from bs4 import BeautifulSoup
from typing import Optional, List
import pandas as pd

BASE_URL = "http://www.prarulebook.co.uk"


def pull_nodes(url: str, selector: str):
    """Pull HTML nodes using CSS selector."""
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            nodes = soup.select(selector)
            return nodes if nodes else None
        return None
    except Exception:
        return None


def extract_node_text(nodes) -> List[str]:
    """Extract text from BeautifulSoup nodes."""
    if nodes is None or len(nodes) == 0:
        return None

    texts = []
    for node in nodes:
        text = node.get_text(strip=True)
        texts.append(text if text else None)

    return texts if texts else None


def extract_results(response) -> Optional[str]:
    """Extract results if page is active (status 200)."""
    if response.status_code == 200:
        return response.text
    else:
        print(f"Warning: Status code {response.status_code}")
        return None


def assign_link_type(url: str) -> Optional[str]:
    """Assign link type based on URL pattern."""
    if not url or pd.isna(url):
        return None

    if "Content/Part" in url:
        return "Part"
    elif "Content/Chapter" in url:
        return "Chapter"
    elif "Content/Rule" in url:
        return "Rule"
    elif "Content/Sector" in url:
        return "Sector"
    elif "LegalInstrument" in url:
        return "Legal"
    elif "/Glossary" in url:
        return "Glossary"
    else:
        return "Other"


def clean_to_link(url: str) -> str:
    """Clean and format links (append domain if needed)."""
    if not url or pd.isna(url):
        return url

    if url.startswith("/rulebook/"):
        return f"{BASE_URL}{url}"
    return url


def replace_whitespace(text: str) -> str:
    """Replace multiple whitespace with single space."""
    if not text or pd.isna(text):
        return text

    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def get_html_response(url: str) -> Optional[BeautifulSoup]:
    """Get HTML response and parse with BeautifulSoup."""
    if not url.startswith("http"):
        raise ValueError("Provide a valid URL.")

    try:
        response = requests.get(url)
        if response.status_code == 200:
            return BeautifulSoup(response.content, 'html.parser')
        return None
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None
