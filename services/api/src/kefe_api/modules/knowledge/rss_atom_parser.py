from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
import re
import xml.etree.ElementTree as ET

from kefe_api.modules.knowledge.source_acquisition import FinalSourceCaptureError

_ATOM_NS = "http://www.w3.org/2005/Atom"
_FORBIDDEN_XML = re.compile(br"<\s*(?:!DOCTYPE|!ENTITY|\?xml-stylesheet|\?[^>]+|xi:include)", re.IGNORECASE)
_SPACE = re.compile(r"\s+")


class FeedFormat(StrEnum):
    RSS_2_0 = "RSS_2_0"
    ATOM_1_0 = "ATOM_1_0"


@dataclass(frozen=True, slots=True)
class FeedParseLimits:
    max_document_bytes: int = 1_048_576
    max_depth: int = 24
    max_elements: int = 5_000
    max_entries: int = 200
    max_text_chars: int = 8_192

    def __post_init__(self) -> None:
        for value, name in (
            (self.max_document_bytes, "max_document_bytes"),
            (self.max_depth, "max_depth"),
            (self.max_elements, "max_elements"),
            (self.max_entries, "max_entries"),
            (self.max_text_chars, "max_text_chars"),
        ):
            if not 1 <= value <= 10_000_000:
                raise ValueError(f"{name} is outside the supported bound")


@dataclass(frozen=True, slots=True)
class ParsedFeedEntry:
    external_id: str
    title: str | None
    canonical_url: str | None
    published_text: str | None
    summary_text: str | None


@dataclass(frozen=True, slots=True)
class ParsedFeed:
    format: FeedFormat
    title: str | None
    canonical_url: str | None
    entries: tuple[ParsedFeedEntry, ...]
    metadata: MappingProxyType


def _text(value: str | None, limits: FeedParseLimits) -> str | None:
    if value is None:
        return None
    normalized = _SPACE.sub(" ", value).strip()
    if not normalized:
        return None
    if len(normalized) > limits.max_text_chars:
        raise FinalSourceCaptureError("SOURCE_FEED_LIMIT_EXCEEDED")
    return normalized


def _element_text(element: ET.Element | None, limits: FeedParseLimits) -> str | None:
    if element is None:
        return None
    return _text(" ".join(element.itertext()), limits)


def _validate_tree(root: ET.Element, limits: FeedParseLimits) -> None:
    count = 0
    stack: list[tuple[ET.Element, int]] = [(root, 1)]
    while stack:
        element, depth = stack.pop()
        count += 1
        if count > limits.max_elements or depth > limits.max_depth:
            raise FinalSourceCaptureError("SOURCE_FEED_LIMIT_EXCEEDED")
        stack.extend((child, depth + 1) for child in reversed(tuple(element)))


def _rss(root: ET.Element, limits: FeedParseLimits) -> ParsedFeed:
    if root.tag != "rss" or root.attrib.get("version") != "2.0":
        raise FinalSourceCaptureError("SOURCE_FEED_FORMAT_UNSUPPORTED")
    channel = root.find("channel")
    if channel is None:
        raise FinalSourceCaptureError("SOURCE_FEED_FORMAT_UNSUPPORTED")
    items = tuple(channel.findall("item"))
    if len(items) > limits.max_entries:
        raise FinalSourceCaptureError("SOURCE_FEED_LIMIT_EXCEEDED")
    entries: list[ParsedFeedEntry] = []
    for item in items:
        guid = _element_text(item.find("guid"), limits)
        link = _element_text(item.find("link"), limits)
        external_id = guid or link
        if external_id is None:
            raise FinalSourceCaptureError("SOURCE_FEED_ENTRY_IDENTITY_MISSING")
        entries.append(
            ParsedFeedEntry(
                external_id=external_id,
                title=_element_text(item.find("title"), limits),
                canonical_url=link,
                published_text=_element_text(item.find("pubDate"), limits),
                summary_text=_element_text(item.find("description"), limits),
            )
        )
    return ParsedFeed(
        format=FeedFormat.RSS_2_0,
        title=_element_text(channel.find("title"), limits),
        canonical_url=_element_text(channel.find("link"), limits),
        entries=tuple(entries),
        metadata=MappingProxyType({"entry_count": len(entries)}),
    )


def _atom_link(element: ET.Element, limits: FeedParseLimits) -> str | None:
    for link in element.findall(f"{{{_ATOM_NS}}}link"):
        relation = link.attrib.get("rel", "alternate")
        if relation == "alternate":
            return _text(link.attrib.get("href"), limits)
    return None


def _atom(root: ET.Element, limits: FeedParseLimits) -> ParsedFeed:
    if root.tag != f"{{{_ATOM_NS}}}feed":
        raise FinalSourceCaptureError("SOURCE_FEED_FORMAT_UNSUPPORTED")
    items = tuple(root.findall(f"{{{_ATOM_NS}}}entry"))
    if len(items) > limits.max_entries:
        raise FinalSourceCaptureError("SOURCE_FEED_LIMIT_EXCEEDED")
    entries: list[ParsedFeedEntry] = []
    for item in items:
        identity = _element_text(item.find(f"{{{_ATOM_NS}}}id"), limits)
        link = _atom_link(item, limits)
        external_id = identity or link
        if external_id is None:
            raise FinalSourceCaptureError("SOURCE_FEED_ENTRY_IDENTITY_MISSING")
        entries.append(
            ParsedFeedEntry(
                external_id=external_id,
                title=_element_text(item.find(f"{{{_ATOM_NS}}}title"), limits),
                canonical_url=link,
                published_text=(
                    _element_text(item.find(f"{{{_ATOM_NS}}}published"), limits)
                    or _element_text(item.find(f"{{{_ATOM_NS}}}updated"), limits)
                ),
                summary_text=(
                    _element_text(item.find(f"{{{_ATOM_NS}}}summary"), limits)
                    or _element_text(item.find(f"{{{_ATOM_NS}}}content"), limits)
                ),
            )
        )
    return ParsedFeed(
        format=FeedFormat.ATOM_1_0,
        title=_element_text(root.find(f"{{{_ATOM_NS}}}title"), limits),
        canonical_url=_atom_link(root, limits),
        entries=tuple(entries),
        metadata=MappingProxyType({"entry_count": len(entries)}),
    )


def parse_rss_atom(
    document: bytes,
    *,
    limits: FeedParseLimits = FeedParseLimits(),
) -> ParsedFeed:
    if type(document) is not bytes:
        raise TypeError("document must be exact bytes")
    if not document:
        raise FinalSourceCaptureError("SOURCE_FEED_DOCUMENT_EMPTY")
    if len(document) > limits.max_document_bytes:
        raise FinalSourceCaptureError("SOURCE_FEED_DOCUMENT_TOO_LARGE")
    if _FORBIDDEN_XML.search(document):
        raise FinalSourceCaptureError("SOURCE_FEED_XML_FORBIDDEN")
    try:
        root = ET.fromstring(document)
    except ET.ParseError as exc:
        raise FinalSourceCaptureError("SOURCE_FEED_XML_MALFORMED") from exc
    _validate_tree(root, limits)
    if root.tag == "rss":
        return _rss(root, limits)
    if root.tag == f"{{{_ATOM_NS}}}feed":
        return _atom(root, limits)
    raise FinalSourceCaptureError("SOURCE_FEED_FORMAT_UNSUPPORTED")


__all__ = [
    "FeedFormat",
    "FeedParseLimits",
    "ParsedFeed",
    "ParsedFeedEntry",
    "parse_rss_atom",
]
