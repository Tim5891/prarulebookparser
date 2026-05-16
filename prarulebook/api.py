from datetime import datetime
import pandas as pd
from typing import Optional, Literal
import requests
from bs4 import BeautifulSoup

from .scrape import (
    scrape_sector_structure, scrape_part_structure, scrape_chapter_structure,
    scrape_rule_structure
)
from .utils import (
    pull_nodes, extract_node_text, assign_link_type, clean_to_link,
    replace_whitespace, BASE_URL
)


def get_structure(
    rulebook_date: str,
    layer: Literal["sector", "part", "chapter", "rule"] = "chapter"
) -> pd.DataFrame:
    """
    Scrape the Rulebook structure.

    Parameters
    ----------
    rulebook_date : str
        Date of the rulebook. Use dd-mm-yyyy format.
    layer : str
        Layer to scrape. Options: 'sector', 'part', 'chapter', 'rule'.
        Default is 'chapter'.

    Returns
    -------
    pd.DataFrame
        Data frame with the rulebook structure.

    Raises
    ------
    ValueError
        If date format is invalid or layer is not recognized.

    Examples
    --------
    >>> structure = get_structure("16-11-2007", layer="part")
    >>> chapters = get_structure("18-06-2019", layer="chapter")
    """
    # Validate date format
    try:
        date_obj = datetime.strptime(rulebook_date, "%d-%m-%Y")
    except ValueError:
        raise ValueError(
            "Provide a correct date in dd-mm-yyyy format. From '01-01-2005' till today."
        )

    # Validate layer
    valid_layers = ["rule", "chapter", "part", "sector"]
    if layer not in valid_layers:
        raise ValueError(
            f"Provide a layer to scrape. Available options: {', '.join(valid_layers)}"
        )

    # Determine if using Handbook or Rulebook based on date
    cutoff_date = datetime.strptime("29-08-2015", "%d-%m-%Y")
    if date_obj < cutoff_date:
        rule_type = "Handbook"
    else:
        rule_type = "Rulebook"

    # Validate date is within available range
    oldest_date = datetime.strptime("01-01-2005", "%d-%m-%Y")
    today = datetime.today()

    if date_obj < oldest_date or date_obj > today:
        raise ValueError(
            "Provide a correct date in dd-mm-yyyy format. From '01-01-2005' till today."
        )

    print(f"You are requesting the {rule_type} as of {rulebook_date}")

    # Construct base URL
    top_url = f"{BASE_URL}/rulebook/Home/{rule_type}/{rulebook_date}"

    # Scrape structure based on requested layer
    if layer == "sector":
        return scrape_sector_structure(top_url)

    if layer == "part":
        sectors = scrape_sector_structure(top_url)
        return scrape_part_structure(sectors)

    if layer == "chapter":
        sectors = scrape_sector_structure(top_url)
        parts = scrape_part_structure(sectors)
        return scrape_chapter_structure(parts)

    if layer == "rule":
        sectors = scrape_sector_structure(top_url)
        parts = scrape_part_structure(sectors)
        chapters = scrape_chapter_structure(parts)
        return scrape_rule_structure(chapters, rulebook_date)


def get_content(
    url: str,
    content_type: Literal["text", "links"] = "text",
    single_rule_selector: Optional[str] = None
) -> pd.DataFrame:
    """
    Extract full text or links from a PRA Rulebook URL.

    Parameters
    ----------
    url : str
        URL to scrape.
    content_type : str
        Type of information to scrape. Options: 'text' or 'links'.
        Default is 'text'.
    single_rule_selector : str, optional
        If "yes", indicates scraping individual rule URLs. Leave blank
        for higher levels (chapter, part, sector).

    Returns
    -------
    pd.DataFrame
        Data frame with URLs and corresponding text or links.

    Raises
    ------
    ValueError
        If URL is invalid or parameters are incorrect.

    Examples
    --------
    >>> # Get text from a chapter
    >>> text = get_content(
    ...     "http://www.prarulebook.co.uk/rulebook/Content/Chapter/242047/16-11-2007"
    ... )
    >>> # Get links from a rule
    >>> links = get_content(
    ...     "http://www.prarulebook.co.uk/rulebook/Content/Rule/211145/18-06-2019#211145",
    ...     content_type="links",
    ...     single_rule_selector="yes"
    ... )
    """
    if not url.startswith("http"):
        raise ValueError("Provide a valid URL.")

    if single_rule_selector and single_rule_selector != "yes":
        raise ValueError("Use 'single_rule_selector' set to 'yes' if you want to scrape single rules.")

    if single_rule_selector == "yes" and "Content/Rule" not in url:
        raise ValueError("Use rule-level URLs for single_rule_selector='yes'.")

    # Default CSS selectors
    selector_rule = ".col1"
    selector_text = ".col3"
    selector_links = ".col3 a"

    # Handle single rule selector
    if single_rule_selector == "yes":
        # Extract rule ID from URL
        rule_id = url.split("#")[-1]
        selector_text = f"#{rule_id}+ .div-row .col3"
        selector_rule = f"#{rule_id}+ .div-row .col1"
        selector_links = f"#{rule_id}+ .div-row .col3 a"

    # Handle glossary URLs
    if "Glossary" in url:
        selector_text = ".GlossaryPara"
        selector_rule = ".glossary-term"
        selector_links = ".GlossaryPara a"

    if content_type == "text":
        return _get_content_text(url, selector_text, selector_rule, single_rule_selector)

    elif content_type == "links":
        return _get_content_links(url, selector_links)

    else:
        raise ValueError("content_type must be 'text' or 'links'.")


def _get_content_text(
    url: str,
    selector_text: str,
    selector_rule: str,
    single_rule_selector: Optional[str]
) -> pd.DataFrame:
    """Extract text content from URL."""
    print(url)

    try:
        response = requests.get(url)
        if response.status_code != 200:
            return pd.DataFrame({
                'rule_number': [None],
                'rule_text': [None],
                'url': [url],
                'active': [None]
            })

        soup = BeautifulSoup(response.content, 'html.parser')

        # Pull text nodes
        text_nodes = soup.select(selector_text)
        if len(text_nodes) == 0:
            print(f"Check the quality of {url}")
            return pd.DataFrame({
                'rule_number': [None],
                'rule_text': [None],
                'url': [url],
                'active': [None]
            })

        nodes_text = [node.get_text(strip=True) for node in text_nodes]

        # Pull rule nodes
        rule_nodes = soup.select(selector_rule)
        nodes_rule = [node.get_text(strip=True) for node in rule_nodes]

        # Remove first element for non-rule levels to balance lengths
        if single_rule_selector is None and len(nodes_rule) > 1:
            nodes_rule = nodes_rule[1:]

        # Check if lengths match
        if len(nodes_text) != len(nodes_rule):
            print(f"Check the quality of {url}")
            return pd.DataFrame({
                'rule_number': [None],
                'rule_text': [None],
                'url': [url],
                'active': [None]
            })

        df = pd.DataFrame({
            'rule_number': nodes_rule,
            'rule_text': nodes_text,
            'url': [url] * len(nodes_text)
        })

        # Mark inactive rules
        df['active'] = ~df['rule_number'].str.contains("Inactive date", regex=True, na=False)

        return df

    except Exception as e:
        print(f"Error processing {url}: {e}")
        return pd.DataFrame({
            'rule_number': [None],
            'rule_text': [None],
            'url': [url],
            'active': [None]
        })


def _get_content_links(url: str, selector_links: str) -> pd.DataFrame:
    """Extract links from URL."""
    print(url)

    try:
        response = requests.get(url)
        if response.status_code != 200:
            return pd.DataFrame({
                'from': [url],
                'to': [None],
                'to_text': [None],
                'to_type': [None]
            })

        soup = BeautifulSoup(response.content, 'html.parser')
        link_nodes = soup.select(selector_links)

        if len(link_nodes) == 0:
            return pd.DataFrame({
                'from': [url],
                'to': [None],
                'to_text': [None],
                'to_type': [None]
            })

        link_urls = []
        link_texts = []

        for node in link_nodes:
            href = node.get('href')
            text = node.get_text(strip=True)
            link_urls.append(href)
            link_texts.append(text if text else None)

        df = pd.DataFrame({
            'from': [url] * len(link_urls),
            'to': link_urls,
            'to_text': link_texts
        })

        # Assign link type
        df['to_type'] = df['to'].apply(assign_link_type)

        # Clean link URLs
        df['to'] = df['to'].apply(lambda x: clean_to_link(x) if pd.notna(x) else x)

        return df

    except Exception as e:
        print(f"Error processing {url}: {e}")
        return pd.DataFrame({
            'from': [url],
            'to': [None],
            'to_text': [None],
            'to_type': [None]
        })


def recode_layer(from_url: str, to: str = "all", structure_file: pd.DataFrame = None) -> pd.DataFrame:
    """
    Recode layer of the rulebook structure.

    Parameters
    ----------
    from_url : str
        Source URL (rule, chapter, part, or sector).
    to : str
        Target layer. Options: 'rule_url', 'rule_name', 'chapter_url', 'chapter_name',
        'part_url', 'part_name', 'sector_url', 'sector_name', 'all'.
        Default is 'all'.
    structure_file : pd.DataFrame
        Data frame from get_structure output.

    Returns
    -------
    pd.DataFrame
        Data frame with recoded layers.

    Raises
    ------
    ValueError
        If parameters are invalid.

    Examples
    --------
    >>> structure = get_structure("16-11-2017", layer="chapter")
    >>> result = recode_layer(
    ...     structure.loc[0, 'chapter_url'],
    ...     to="all",
    ...     structure_file=structure
    ... )
    """
    valid_to = [
        "rule_url", "rule_name", "chapter_url", "chapter_name",
        "part_url", "part_name", "sector_url", "sector_name", "all"
    ]

    if to not in valid_to:
        raise ValueError(
            f"Provide correct 'to' argument. Available options: {', '.join(valid_to)}"
        )

    if structure_file is None or structure_file.empty:
        raise ValueError("Provide a valid structure_file from get_structure().")

    # Determine URL type
    link_type = assign_link_type(from_url)
    if link_type is None:
        raise ValueError("Provide a correct 'from' URL")

    # Map type to column name
    type_to_col = {
        "Sector": "sector_url",
        "Part": "part_url",
        "Chapter": "chapter_url",
        "Rule": "rule_url"
    }

    if link_type not in type_to_col:
        raise ValueError("Incorrect URL")

    from_col = type_to_col[link_type]

    # Check if column exists in structure file
    if from_col not in structure_file.columns:
        raise ValueError(f"Check if 'from' URL type ({from_col}) can be found in structure_file.")

    # Create from dataframe
    from_df = pd.DataFrame({from_col: [from_url]})

    # Join with structure file
    if to == "all":
        result = from_df.merge(structure_file, on=from_col, how="left")
    else:
        cols_to_select = [from_col, to]
        # Filter to only available columns
        cols_to_select = [col for col in cols_to_select if col in structure_file.columns]
        result = from_df.merge(
            structure_file[cols_to_select],
            on=from_col,
            how="left"
        )

    return result
