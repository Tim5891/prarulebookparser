# prarulebook

A Python package to scrape the [PRA (Prudential Regulation Authority) Rulebook](http://www.prarulebook.co.uk/) website. The package extracts the rulebook structure and content in formats suitable for text and network analysis.

## About

`prarulebook` scrapes the website containing the rules made and enforced by the PRA under powers conferred by the Financial Services and Markets Act 2000 (FSMA).

The inputs to this package are the PRA Rulebook website. Outputs are the rules published on the PRA Rulebook website in a format more amenable to text and network analysis.

`prarulebook` was inspired by the R package developed while preparing:

**Amadxarif, Z., Brookes, J., Garbarino, N., Patel, R., Walczak, E. (2019)** *[The Language of Rules: Textual Complexity in Banking Reforms](https://www.bankofengland.co.uk/working-paper/2019/the-language-of-rules-textual-complexity-in-banking-reforms)*. Staff Working Paper No. 834. Bank of England.

## Data Classification

Bank of England Data Classification: OFFICIAL BLUE

## Disclaimer

This package is an outcome of a research project. All errors are mine. All views expressed are personal views, not those of any employer.

Any use of this package with the PRA Rulebook must comply with the PRA Rulebook's [Terms of Use](http://www.prarulebook.co.uk/terms-of-use). These include, but are not limited to, restrictions on using content from the PRA Rulebook for commercial purposes without obtaining a licence from the PRA.

## Installation

Install from source:

```bash
pip install -e .
```

Or install with development dependencies:

```bash
pip install -e ".[dev]"
```

## Usage

### Structure

The simplest way to extract a rulebook structure is to use the `get_structure()` function:

```python
from prarulebook import get_structure

# Get the structure at part level
parts = get_structure("16-11-2007", layer="part")

# Get the structure at chapter level
chapters = get_structure("18-06-2019", layer="chapter")
```

Warnings (HTTP 410) will be displayed when pages are no longer active. Pulling more granular data takes longer. Available layers (in descending order):

- `sector`
- `part`
- `chapter`
- `rule`

### Content

Once structure URLs are obtained, they can be used to extract content.

#### Text

To extract text content from the rulebook, use the `get_content()` function:

```python
from prarulebook import get_content

# Get text from a single chapter
chapter_text = get_content(chapters.iloc[0]['chapter_url'])

# Get text from a single rule
rule_text = get_content(
    rules.iloc[2]['rule_url'],
    content_type="text",
    single_rule_selector="yes"
)
```

You can apply this across multiple chapters using pandas:

```python
import pandas as pd

# Get text from first 5 chapters
chapter_texts = []
for url in chapters['chapter_url'][:5]:
    text_df = get_content(url)
    chapter_texts.append(text_df)

chapters_text = pd.concat(chapter_texts, ignore_index=True)
```

#### Links

To extract links for network analysis, use `get_content()` with `content_type="links"`:

```python
# Get links from a chapter
chapter_links = get_content(chapters.iloc[0]['chapter_url'], content_type="links")

# Get links from multiple parts
parts_links = []
for url in parts['part_url'][:5]:
    links_df = get_content(url, content_type="links")
    parts_links.append(links_df)

parts_links_combined = pd.concat(parts_links, ignore_index=True)
```

The output includes:

- `from` - source URL
- `to` - target URL
- `to_text` - link text
- `to_type` - type of target (Rule, Chapter, Part, Sector, Glossary, Legal, Other)

### Recoding Layers

To navigate between different hierarchy levels, use `recode_layer()`:

```python
from prarulebook import recode_layer

structure = get_structure("16-11-2017", layer="chapter")

# Get all information for a specific chapter
result = recode_layer(
    structure.iloc[0]['chapter_url'],
    to="all",
    structure_file=structure
)

# Get just the part name for a specific chapter
part_name = recode_layer(
    structure.iloc[0]['chapter_url'],
    to="part_name",
    structure_file=structure
)
```

Available `to` options:
- `rule_url`, `rule_name`
- `chapter_url`, `chapter_name`
- `part_url`, `part_name`
- `sector_url`, `sector_name`
- `all` (returns all available fields)

## Data Structure

The package returns pandas DataFrames with the following structures:

### Structure Data
- `sector_url` / `sector_name`
- `part_url` / `part_name`
- `chapter_url` / `chapter_name`
- `rule_url` / `rule_id` (when layer="rule")

### Text Content
- `rule_number` - Rule identifier
- `rule_text` - Rule text content
- `url` - Source URL
- `active` - Boolean indicating if rule is active

### Link Content
- `from` - Source URL
- `to` - Target URL
- `to_text` - Link text
- `to_type` - Type of target link

## Requirements

- Python 3.8+
- requests
- beautifulsoup4
- pandas
- lxml

## Testing

Run tests with:

```bash
pytest
```

Or with coverage:

```bash
pytest --cov=prarulebook
```

## License

GPL-3

## Credits

Original R implementation: Eryk Walczak
Python rewrite: 2024
