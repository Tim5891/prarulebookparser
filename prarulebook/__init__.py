"""
PRArulebook: Scraper for the Prudential Regulation Authority rulebook.

A Python package to scrape the PRA Rulebook website and extract rules,
chapters, parts, and sectors for text and network analysis.
"""

__version__ = "0.0.1"
__author__ = "Eryk Walczak"

from .api import get_structure, get_content, recode_layer
from .scrape import (
    scrape_sector_structure,
    scrape_part_structure,
    scrape_chapter_structure,
    scrape_rule_structure,
    scrape_menu,
    scrape_menu_rule,
    scrape_rule_id,
)

__all__ = [
    "get_structure",
    "get_content",
    "recode_layer",
    "scrape_sector_structure",
    "scrape_part_structure",
    "scrape_chapter_structure",
    "scrape_rule_structure",
    "scrape_menu",
    "scrape_menu_rule",
    "scrape_rule_id",
]
