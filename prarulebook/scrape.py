import re
import pandas as pd
from datetime import datetime
from typing import Optional, List
import requests
from bs4 import BeautifulSoup

from .utils import (
    pull_nodes, extract_node_text, extract_results, assign_link_type,
    clean_to_link, replace_whitespace, get_html_response, BASE_URL
)


def scrape_menu(url: str, selector: str, rulebook_date: Optional[str] = None) -> pd.DataFrame:
    """
    Scrape names and URLs from the PRA rulebook menu.

    Parameters
    ----------
    url : str
        URL to scrape.
    selector : str
        CSS selector to scrape.
    rulebook_date : str, optional
        Date in dd-mm-yyyy format. Needed for rule ID scraping.

    Returns
    -------
    pd.DataFrame
        Data frame with names and URLs of rulebook elements.
    """
    if not url.startswith("http"):
        raise ValueError("Provide a valid URL.")

    if not selector:
        raise ValueError("Provide a valid selector to scrape.")

    response = requests.get(url)

    if response.status_code != 200:
        print(f"Warning: Status code {response.status_code}")
        return pd.DataFrame({
            'name': [None],
            'menu_url': [None],
            'provided_url': [url]
        })

    soup = BeautifulSoup(response.content, 'html.parser')
    nodes = soup.select(selector)

    if len(nodes) == 0:
        return pd.DataFrame({
            'name': [None],
            'menu_url': [None],
            'provided_url': [url]
        })

    # Extract text
    nodes_text = []
    for node in nodes:
        text = node.get_text(strip=True)
        text = replace_whitespace(text)
        nodes_text.append(text if text else None)

    if len(nodes_text) == 0:
        nodes_text = [None]

    # Extract URLs
    nodes_url = []
    for i, node in enumerate(nodes):
        href = node.get('href')
        if href and nodes_text[i] is not None:
            full_url = f"{BASE_URL}{href}" if href.startswith('/') else href
            nodes_url.append(full_url)
        else:
            nodes_url.append(None)

    # Handle rule URLs
    if selector == ".rule-number":
        nodes_url = [None] * len(nodes_text)

    # For rule selector, use scrape_menu_rule
    if selector == "a":
        return scrape_menu_rule(url, nodes, rulebook_date)

    # Combine into dataframe
    df = pd.DataFrame({
        'name': nodes_text,
        'menu_url': nodes_url,
        'provided_url': [url] * len(nodes_text)
    })

    return df


def scrape_menu_rule(url: str, nodes, rulebook_date: str) -> pd.DataFrame:
    """
    Scrape rules within chapters.

    Parameters
    ----------
    url : str
        URL to scrape.
    nodes : list
        BeautifulSoup nodes from scrape_menu.
    rulebook_date : str
        Date in dd-mm-yyyy format.

    Returns
    -------
    pd.DataFrame
        Data frame with rule URLs and metadata.
    """
    ids = []
    for node in nodes:
        node_id = node.get('id')
        if node_id:
            ids.append(node_id)

    ids = [id for id in ids if id and len(id) == 6]

    if len(ids) == 0:
        return pd.DataFrame({
            'rule_url': [None],
            'rule_id': [None],
            'rule_number_sel': [None],
            'rule_text_sel': [None],
            'rule_link_sel': [None],
            'chapter_url': [url]
        })

    try:
        ids = [int(id) for id in ids]
    except ValueError:
        ids = []

    if len(ids) == 0:
        return pd.DataFrame({
            'rule_url': [None],
            'rule_id': [None],
            'rule_number_sel': [None],
            'rule_text_sel': [None],
            'rule_link_sel': [None],
            'chapter_url': [url]
        })

    # Create rule URLs and selectors
    rule_urls = [
        f"{BASE_URL}/rulebook/Content/Rule/{id}/{rulebook_date}#{id}"
        for id in ids
    ]

    rule_no_selectors = [f"#{id}+ .div-row .rule-number" for id in ids]
    rule_text_selectors = [f"#{id}+ .div-row .col3" for id in ids]
    rule_link_selectors = [f"#{id}+ .div-row a" for id in ids]

    df = pd.DataFrame({
        'rule_url': rule_urls,
        'rule_id': ids,
        'rule_number_sel': rule_no_selectors,
        'rule_text_sel': rule_text_selectors,
        'rule_link_sel': rule_link_selectors,
        'chapter_url': [url] * len(ids)
    })

    return df


def scrape_sector_structure(url: str) -> pd.DataFrame:
    """
    Scrape sector structure from rulebook.

    Parameters
    ----------
    url : str
        Top-level rulebook URL.

    Returns
    -------
    pd.DataFrame
        Data frame with sector structure.
    """
    print("--- Scraping SECTORS ---")
    sectors = scrape_menu(url, ".nav-child a")
    sectors.columns = ["sector_name", "sector_url", "rulebook_url"]
    return sectors


def scrape_part_structure(df: pd.DataFrame) -> pd.DataFrame:
    """
    Scrape part structure from sectors.

    Parameters
    ----------
    df : pd.DataFrame
        Data frame with sector URLs from scrape_sector_structure.

    Returns
    -------
    pd.DataFrame
        Data frame with part structure.
    """
    print("--- Scraping PARTS ---")

    parts_list = []
    for sector_url in df['sector_url']:
        if pd.isna(sector_url):
            continue
        parts = scrape_menu(sector_url, ".Part a")
        parts_list.append(parts)

    if parts_list:
        parts = pd.concat(parts_list, ignore_index=True)
    else:
        parts = pd.DataFrame({'name': [], 'menu_url': [], 'provided_url': []})

    parts.columns = ["part_name", "part_url", "sector_url"]
    parts['part_name'] = parts['part_name'].astype(str).str.strip()

    # Join with sector names
    parts_sectors = parts.merge(df, on="sector_url", how="left")
    return parts_sectors


def scrape_chapter_structure(df: pd.DataFrame) -> pd.DataFrame:
    """
    Scrape chapter structure from parts.

    Parameters
    ----------
    df : pd.DataFrame
        Data frame with part URLs from scrape_part_structure.

    Returns
    -------
    pd.DataFrame
        Data frame with chapter structure.
    """
    print("--- Scraping CHAPTERS ---")

    chapters_list = []
    for part_url in df['part_url']:
        if pd.isna(part_url):
            continue
        chapters = scrape_menu(part_url, ".Chapter a")
        chapters_list.append(chapters)

    if chapters_list:
        chapters = pd.concat(chapters_list, ignore_index=True)
    else:
        chapters = pd.DataFrame({'name': [], 'menu_url': [], 'provided_url': []})

    chapters.columns = ["chapter_name", "chapter_url", "part_url"]

    # Clean chapter names
    chapters['chapter_name'] = chapters['chapter_name'].astype(str).str.replace(r'[\r\n]', ' ', regex=True)
    chapters['chapter_name'] = chapters['chapter_name'].str.replace(r'\s+', ' ', regex=True).str.strip()

    # Remove chapters with no URL
    chapters = chapters[chapters['chapter_url'].notna()]

    # Join with parts and sectors
    chapters_parts_sectors = chapters.merge(df, on="part_url", how="left")
    return chapters_parts_sectors


def scrape_rule_structure(df: pd.DataFrame, rulebook_date: str) -> pd.DataFrame:
    """
    Scrape rule structure from chapters.

    Parameters
    ----------
    df : pd.DataFrame
        Data frame with chapter URLs from scrape_chapter_structure.
    rulebook_date : str
        Date in dd-mm-yyyy format.

    Returns
    -------
    pd.DataFrame
        Data frame with rule structure.
    """
    print("\n--- Scraping RULES ---")

    rules_list = []
    for chapter_url in df['chapter_url']:
        if pd.isna(chapter_url):
            continue
        rules = scrape_menu(chapter_url, "a", rulebook_date)
        rules_list.append(rules)

    if rules_list:
        rules = pd.concat(rules_list, ignore_index=True)
    else:
        rules = pd.DataFrame()

    # Rename columns
    if 'name' in rules.columns:
        rules.rename(columns={'menu_url': 'rule_url', 'provided_url': 'chapter_url'}, inplace=True)

    # Join with chapter info
    if not rules.empty and not df.empty:
        rules_chapters_parts_sectors = rules.merge(df, on="chapter_url", how="left")
    else:
        rules_chapters_parts_sectors = rules

    return rules_chapters_parts_sectors


def scrape_rule_id(
    url: str,
    selector_rule_no: str,
    selector_rule_text: str
) -> pd.DataFrame:
    """
    Scrape individual rule content.

    Parameters
    ----------
    url : str
        Rule URL.
    selector_rule_no : str
        CSS selector for rule number.
    selector_rule_text : str
        CSS selector for rule text.

    Returns
    -------
    pd.DataFrame
        Data frame with rule content.
    """
    if pd.isna(url):
        return pd.DataFrame({
            'rule_number': [None],
            'rule_text': [None],
            'rule_url': [url]
        })

    soup = get_html_response(url)
    if soup is None:
        return pd.DataFrame({
            'rule_number': [None],
            'rule_text': [None],
            'rule_url': [url]
        })

    print(".", end="", flush=True)

    # Pull rule number
    rule_no_nodes = soup.select(selector_rule_no)
    rule_no_text = []
    for node in rule_no_nodes:
        text = node.get_text(strip=True)
        rule_no_text.append(text if text else None)

    if len(rule_no_text) == 0:
        rule_no_text = [None]

    # Pull rule text
    rule_text_nodes = soup.select(selector_rule_text)
    rule_texts = []
    for node in rule_text_nodes:
        text = node.get_text(strip=True)
        rule_texts.append(text if text else None)

    if len(rule_texts) == 0:
        rule_texts = [None]

    df = pd.DataFrame({
        'rule_number': rule_no_text,
        'rule_text': rule_texts,
        'rule_url': [url] * max(len(rule_no_text), len(rule_texts))
    })

    return df
