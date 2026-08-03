from __future__ import annotations

from types import MappingProxyType

import pytest

from kefe_api.modules.knowledge.rss_atom_parser import (
    FeedFormat,
    FeedParseLimits,
    parse_rss_atom,
)
from kefe_api.modules.knowledge.source_acquisition import FinalSourceCaptureError


def _error(document: bytes, code: str, **limits) -> None:
    with pytest.raises(FinalSourceCaptureError) as captured:
        parse_rss_atom(document, limits=FeedParseLimits(**limits))
    assert captured.value.code == code


def test_parses_rss_20_in_source_order_and_collapses_markup_text() -> None:
    parsed = parse_rss_atom(
        b"""<rss version='2.0'><channel><title>  KEFE   Feed </title>
        <link>https://example.test/feed</link>
        <item><guid>one</guid><title> First   item </title>
        <link>https://example.test/one</link>
        <pubDate>Mon, 03 Aug 2026 01:00:00 GMT</pubDate>
        <description>Hello <b>world</b></description></item>
        <item><link>https://example.test/two</link><title>Second</title></item>
        </channel></rss>"""
    )
    assert parsed.format is FeedFormat.RSS_2_0
    assert parsed.title == "KEFE Feed"
    assert tuple(entry.external_id for entry in parsed.entries) == (
        "one",
        "https://example.test/two",
    )
    assert parsed.entries[0].summary_text == "Hello world"
    assert type(parsed.metadata) is MappingProxyType
    assert parsed.metadata["entry_count"] == 2


def test_parses_atom_10_with_exact_namespace_and_alternate_links() -> None:
    parsed = parse_rss_atom(
        b"""<feed xmlns='http://www.w3.org/2005/Atom'>
        <title>Atom feed</title><link rel='alternate' href='https://example.test/'/>
        <entry><id>tag:example.test,2026:1</id><title>Entry</title>
        <link href='https://example.test/1'/>
        <updated>2026-08-03T01:00:00Z</updated>
        <summary>Alpha <em>beta</em></summary></entry></feed>"""
    )
    assert parsed.format is FeedFormat.ATOM_1_0
    assert parsed.canonical_url == "https://example.test/"
    assert parsed.entries[0].external_id == "tag:example.test,2026:1"
    assert parsed.entries[0].canonical_url == "https://example.test/1"
    assert parsed.entries[0].summary_text == "Alpha beta"


@pytest.mark.parametrize(
    "document",
    (
        b"<!DOCTYPE rss [<!ENTITY xxe SYSTEM 'file:///etc/passwd'>]><rss version='2.0'/>",
        b"<!ENTITY x 'boom'><rss version='2.0'/>",
        b"<?xml-stylesheet href='https://example.test/x'?><rss version='2.0'/>",
        b"<rss version='2.0'><xi:include href='file:///etc/passwd'/></rss>",
    ),
)
def test_rejects_forbidden_xml_surfaces_before_parsing(document: bytes) -> None:
    _error(document, "SOURCE_FEED_XML_FORBIDDEN")


def test_rejects_empty_oversized_malformed_and_unsupported_documents() -> None:
    _error(b"", "SOURCE_FEED_DOCUMENT_EMPTY")
    _error(
        b"<rss version='2.0'/>" * 2,
        "SOURCE_FEED_DOCUMENT_TOO_LARGE",
        max_document_bytes=10,
    )
    _error(b"<rss>", "SOURCE_FEED_XML_MALFORMED")
    _error(b"<feed/>", "SOURCE_FEED_FORMAT_UNSUPPORTED")
    _error(
        b"<rss version='1.0'><channel/></rss>",
        "SOURCE_FEED_FORMAT_UNSUPPORTED",
    )


def test_enforces_depth_element_entry_and_text_limits() -> None:
    _error(
        b"<rss version='2.0'><channel><item/></channel></rss>",
        "SOURCE_FEED_LIMIT_EXCEEDED",
        max_depth=2,
    )
    _error(
        b"<rss version='2.0'><channel><title>x</title></channel></rss>",
        "SOURCE_FEED_LIMIT_EXCEEDED",
        max_elements=2,
    )
    _error(
        b"<rss version='2.0'><channel>"
        b"<item><guid>1</guid></item>"
        b"<item><guid>2</guid></item>"
        b"</channel></rss>",
        "SOURCE_FEED_LIMIT_EXCEEDED",
        max_entries=1,
    )
    _error(
        b"<rss version='2.0'><channel><title>12345</title></channel></rss>",
        "SOURCE_FEED_LIMIT_EXCEEDED",
        max_text_chars=4,
    )


def test_rejects_entries_without_stable_identity() -> None:
    _error(
        b"<rss version='2.0'><channel>"
        b"<item><title>missing</title></item>"
        b"</channel></rss>",
        "SOURCE_FEED_ENTRY_IDENTITY_MISSING",
    )
    _error(
        b"<feed xmlns='http://www.w3.org/2005/Atom'>"
        b"<entry><title>missing</title></entry></feed>",
        "SOURCE_FEED_ENTRY_IDENTITY_MISSING",
    )


def test_requires_exact_bytes_and_valid_limits() -> None:
    with pytest.raises(TypeError, match="exact bytes"):
        parse_rss_atom(bytearray(b"<rss/>"))  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        FeedParseLimits(max_entries=0)
