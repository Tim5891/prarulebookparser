import pytest
from prarulebook.utils import assign_link_type, clean_to_link, replace_whitespace


def test_assign_link_type():
    """Test link type assignment."""
    assert assign_link_type("http://www.prarulebook.co.uk/Content/Part/123") == "Part"
    assert assign_link_type("http://www.prarulebook.co.uk/Content/Chapter/456") == "Chapter"
    assert assign_link_type("http://www.prarulebook.co.uk/Content/Rule/789") == "Rule"
    assert assign_link_type("http://www.prarulebook.co.uk/Content/Sector/012") == "Sector"
    assert assign_link_type("http://www.prarulebook.co.uk/Glossary/test") == "Glossary"
    assert assign_link_type("http://www.example.com") == "Other"
    assert assign_link_type(None) is None


def test_clean_to_link():
    """Test link cleaning."""
    result = clean_to_link("/rulebook/Content/Rule/123")
    assert result.startswith("http://www.prarulebook.co.uk")

    result = clean_to_link("http://example.com")
    assert result == "http://example.com"

    assert clean_to_link(None) is None


def test_replace_whitespace():
    """Test whitespace replacement."""
    assert replace_whitespace("hello   world") == "hello world"
    assert replace_whitespace("  leading  trailing  ") == "leading trailing"
    assert replace_whitespace(None) is None
