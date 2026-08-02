from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit
from xml.etree import ElementTree

from kefe_api.modules.knowledge.provider_http_capture import ProviderHttpCapturePlan
from kefe_api.modules.knowledge.provider_http_evidence_capture import (
    MAX_PARSED_METADATA_CHARS,
    ProviderHttpParsedSource,
)
from kefe_api.modules.knowledge.provider_http_transport import (
    MAX_RESPONSE_BYTES,
    OutboundHttpRequest,
    ProviderHttpMethod,
    ProviderHttpResponse,
)
from kefe_api.modules.knowledge.provider_public_http_capture import (
    FinalPublicHttpParseError,
)
from kefe_api.modules.knowledge.source_identity import require_versioned_adapter_code

ATOM_NAMESPACE = "http://www.w3.org/2005/Atom"
XINCLUDE_NAMESPACE = "http://www.w3.org/2001/XInclude"
XML_LANGUAGE_ATTRIBUTE = "{http://www.w3.org/XML/1998/namespace}lang"
RSS_ATOM_ACCEPT_HEADER = (
    "application/atom+xml, application/rss+xml, "
    "application/xml;q=0.9, text/xml;q=0.8"
)
RSS_ATOM_USER_AGENT = "KEFE-FeedCapture/1.0"

_MEDIA_TYPE = re.compile(
    r"^[a-z0-9][a-z0-9!#$&^_.+-]*/[a-z0-9][a-z0-9!#$&^_.+-]*$"
)
_LANGUAGE_CODE = re.compile(r"^[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*$")
_XML_ENCODING = re.compile(br"encoding\s*=\s*['\"]([^'\"]+)['\"]", re.I)


def _fail(code: str) -> None:
    raise FinalPublicHttpParseError(code)


def _require_utc(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
        raise ValueError(f"{field_name} must be timezone-aware UTC")


def _tag_parts(tag: str) -> tuple[str | None, str]:
    if tag.startswith("{"):
        namespace, separator, local_name = tag[1:].partition("}")
        if not separator or not namespace or not local_name:
            _fail("SOURCE_PUBLIC_HTTP_PARSE_XML_INVALID")
        return namespace, local_name
    return None, tag


def _normalize_text(value: str) -> str:
    return " ".join(value.split())


@dataclass(frozen=True, slots=True)
class StrictRssAtomParseProfile:
    accepted_media_types: tuple[str, ...] = (
        "application/atom+xml",
        "application/rss+xml",
        "application/xml",
        "text/xml",
    )
    max_document_bytes: int = 1_048_576
    max_elements: int = 4096
    max_depth: int = 16
    max_items: int = 256
    max_node_text_chars: int = 16_384
    max_total_text_chars: int = 262_144
    max_attributes_per_element: int = 8
    max_total_attribute_chars: int = 65_536
    max_metadata_field_chars: int = 4096

    def __post_init__(self) -> None:
        normalized_media_types = tuple(
            item.strip().lower() for item in self.accepted_media_types
        )
        if not normalized_media_types:
            raise ValueError("at least one RSS/Atom media type is required")
        if any(_MEDIA_TYPE.fullmatch(item) is None for item in normalized_media_types):
            raise ValueError("RSS/Atom media types must be exact lowercase types")
        if normalized_media_types != tuple(sorted(set(normalized_media_types))):
            raise ValueError("RSS/Atom media types must be unique and sorted")
        if not 1 <= self.max_document_bytes <= MAX_RESPONSE_BYTES:
            raise ValueError("RSS/Atom document byte budget is invalid")
        if not 1 <= self.max_elements <= 100_000:
            raise ValueError("RSS/Atom element budget is invalid")
        if not 1 <= self.max_depth <= 64:
            raise ValueError("RSS/Atom depth budget is invalid")
        if not 0 <= self.max_items <= 10_000:
            raise ValueError("RSS/Atom item budget is invalid")
        if not 1 <= self.max_node_text_chars <= self.max_total_text_chars:
            raise ValueError("RSS/Atom node text budget is invalid")
        if not 1 <= self.max_total_text_chars <= 4_000_000:
            raise ValueError("RSS/Atom total text budget is invalid")
        if not 0 <= self.max_attributes_per_element <= 128:
            raise ValueError("RSS/Atom attribute-count budget is invalid")
        if not 0 <= self.max_total_attribute_chars <= 1_000_000:
            raise ValueError("RSS/Atom attribute-text budget is invalid")
        if not 1 <= self.max_metadata_field_chars <= MAX_PARSED_METADATA_CHARS:
            raise ValueError("RSS/Atom metadata field budget is invalid")

    @property
    def immutable_configuration(self) -> tuple[object, ...]:
        return (
            self.accepted_media_types,
            self.max_document_bytes,
            self.max_elements,
            self.max_depth,
            self.max_items,
            self.max_node_text_chars,
            self.max_total_text_chars,
            self.max_attributes_per_element,
            self.max_total_attribute_chars,
            self.max_metadata_field_chars,
        )


@dataclass(frozen=True, slots=True)
class StrictRssAtomCaptureDefinition:
    adapter_code: str
    profile: StrictRssAtomParseProfile = StrictRssAtomParseProfile()

    def __post_init__(self) -> None:
        require_versioned_adapter_code(self.adapter_code)
        if not isinstance(self.profile, StrictRssAtomParseProfile):
            raise ValueError("RSS/Atom definition requires an exact parser profile")

    def build_plan(
        self,
        *,
        external_locator: str,
        trace_id: str,
        at: datetime,
    ) -> ProviderHttpCapturePlan:
        del trace_id
        _require_utc(at, "at")
        self._validate_locator(external_locator)
        return ProviderHttpCapturePlan(
            adapter_code=self.adapter_code,
            request=OutboundHttpRequest(
                adapter_code=self.adapter_code,
                method=ProviderHttpMethod.GET,
                url=external_locator,
                public_headers=(
                    ("accept", RSS_ATOM_ACCEPT_HEADER),
                    ("user-agent", RSS_ATOM_USER_AGENT),
                ),
            ),
        )

    def parse_response(
        self,
        *,
        plan: ProviderHttpCapturePlan,
        response: ProviderHttpResponse,
        trace_id: str,
        at: datetime,
    ) -> ProviderHttpParsedSource:
        del trace_id
        _require_utc(at, "at")
        if type(plan) is not ProviderHttpCapturePlan:
            _fail("SOURCE_PUBLIC_HTTP_PARSE_FIELD_INVALID")
        if plan.adapter_code != self.adapter_code:
            _fail("SOURCE_PUBLIC_HTTP_PARSE_FIELD_INVALID")
        if type(response) is not ProviderHttpResponse:
            _fail("SOURCE_PUBLIC_HTTP_PARSE_FIELD_INVALID")
        if response.status_code != 200:
            _fail("SOURCE_PUBLIC_HTTP_PARSE_FIELD_INVALID")
        if response.media_type not in self.profile.accepted_media_types:
            _fail("SOURCE_PUBLIC_HTTP_PARSE_MEDIA_TYPE_UNSUPPORTED")
        if type(response.body) is not bytes:
            _fail("SOURCE_PUBLIC_HTTP_PARSE_FIELD_INVALID")
        if not response.body or len(response.body) > self.profile.max_document_bytes:
            _fail("SOURCE_PUBLIC_HTTP_PARSE_DOCUMENT_TOO_LARGE")

        self._validate_safe_xml(response.body)
        try:
            root = ElementTree.fromstring(response.body)
        except ElementTree.ParseError as exc:
            raise FinalPublicHttpParseError(
                "SOURCE_PUBLIC_HTTP_PARSE_XML_INVALID"
            ) from exc
        self._enforce_tree_profile(root)

        namespace, local_name = _tag_parts(root.tag)
        if namespace is None and local_name == "rss":
            return self._parse_rss(root, canonical_url=plan.request.url)
        if namespace == ATOM_NAMESPACE and local_name == "feed":
            return self._parse_atom(root, canonical_url=plan.request.url)
        _fail("SOURCE_PUBLIC_HTTP_PARSE_ROOT_UNSUPPORTED")

    def _validate_locator(self, value: str) -> None:
        if not value or value != value.strip():
            raise ValueError("RSS/Atom locator must not be blank or padded")
        try:
            parsed = urlsplit(value)
            port = parsed.port
        except ValueError as exc:
            raise ValueError("RSS/Atom locator is invalid") from exc
        if parsed.scheme != "https":
            raise ValueError("RSS/Atom locator must use https")
        if parsed.username is not None or parsed.password is not None:
            raise ValueError("RSS/Atom locator cannot contain userinfo")
        if parsed.hostname is None or parsed.fragment:
            raise ValueError("RSS/Atom locator requires a host and no fragment")
        try:
            parsed.hostname.encode("ascii")
        except UnicodeEncodeError as exc:
            raise ValueError("RSS/Atom locator hostname must be ASCII") from exc
        if "*" in parsed.hostname or port not in (None, 443):
            raise ValueError("RSS/Atom locator host or port is invalid")

    def _validate_safe_xml(self, body: bytes) -> None:
        if b"\x00" in body:
            _fail("SOURCE_PUBLIC_HTTP_PARSE_UNSAFE_XML")
        if body.startswith((b"\xff\xfe", b"\xfe\xff", b"\x00\x00\xfe\xff", b"\xff\xfe\x00\x00")):
            _fail("SOURCE_PUBLIC_HTTP_PARSE_UNSAFE_XML")
        try:
            body.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise FinalPublicHttpParseError(
                "SOURCE_PUBLIC_HTTP_PARSE_UNSAFE_XML"
            ) from exc

        inspected = body.removeprefix(b"\xef\xbb\xbf")
        remaining = inspected
        if inspected.startswith(b"<?xml"):
            end = inspected.find(b"?>")
            if end < 0:
                _fail("SOURCE_PUBLIC_HTTP_PARSE_XML_INVALID")
            declaration = inspected[: end + 2]
            encoding = _XML_ENCODING.search(declaration)
            if encoding is not None and encoding.group(1).lower() not in {
                b"utf-8",
                b"utf8",
            }:
                _fail("SOURCE_PUBLIC_HTTP_PARSE_UNSAFE_XML")
            remaining = inspected[end + 2 :]

        lowered = remaining.lower()
        if b"<?" in remaining:
            _fail("SOURCE_PUBLIC_HTTP_PARSE_UNSAFE_XML")
        if b"<!doctype" in lowered or b"<!entity" in lowered:
            _fail("SOURCE_PUBLIC_HTTP_PARSE_UNSAFE_XML")

    def _enforce_tree_profile(self, root: ElementTree.Element) -> None:
        stack: list[tuple[ElementTree.Element, int]] = [(root, 1)]
        element_count = 0
        total_text_chars = 0
        total_attribute_chars = 0

        while stack:
            element, depth = stack.pop()
            element_count += 1
            if element_count > self.profile.max_elements:
                _fail("SOURCE_PUBLIC_HTTP_PARSE_PROFILE_EXCEEDED")
            if depth > self.profile.max_depth:
                _fail("SOURCE_PUBLIC_HTTP_PARSE_PROFILE_EXCEEDED")
            if not isinstance(element.tag, str):
                _fail("SOURCE_PUBLIC_HTTP_PARSE_UNSAFE_XML")
            namespace, _ = _tag_parts(element.tag)
            if namespace == XINCLUDE_NAMESPACE:
                _fail("SOURCE_PUBLIC_HTTP_PARSE_UNSAFE_XML")
            if len(element.attrib) > self.profile.max_attributes_per_element:
                _fail("SOURCE_PUBLIC_HTTP_PARSE_PROFILE_EXCEEDED")
            for name, value in element.attrib.items():
                total_attribute_chars += len(name) + len(value)
                if total_attribute_chars > self.profile.max_total_attribute_chars:
                    _fail("SOURCE_PUBLIC_HTTP_PARSE_PROFILE_EXCEEDED")

            for value in (element.text, element.tail):
                if value is None:
                    continue
                if len(value) > self.profile.max_node_text_chars:
                    _fail("SOURCE_PUBLIC_HTTP_PARSE_PROFILE_EXCEEDED")
                total_text_chars += len(value)
                if total_text_chars > self.profile.max_total_text_chars:
                    _fail("SOURCE_PUBLIC_HTTP_PARSE_PROFILE_EXCEEDED")

            children = list(element)
            for child in reversed(children):
                stack.append((child, depth + 1))

    def _parse_rss(
        self,
        root: ElementTree.Element,
        *,
        canonical_url: str,
    ) -> ProviderHttpParsedSource:
        if root.attrib.get("version") != "2.0":
            _fail("SOURCE_PUBLIC_HTTP_PARSE_ROOT_UNSUPPORTED")
        channels = self._direct_children(root, namespace=None, local_name="channel")
        if len(channels) != 1:
            _fail("SOURCE_PUBLIC_HTTP_PARSE_REQUIRED_FIELD_MISSING")
        channel = channels[0]
        title = self._required_child_text(channel, None, "title")
        link = self._required_child_text(channel, None, "link")
        self._required_child_text(channel, None, "description")
        self._validate_declared_http_url(link)

        items = self._direct_children(channel, namespace=None, local_name="item")
        self._require_all_named_elements_direct(
            root,
            namespace=None,
            local_name="item",
            expected_count=len(items),
        )
        if len(items) > self.profile.max_items:
            _fail("SOURCE_PUBLIC_HTTP_PARSE_PROFILE_EXCEEDED")
        for item in items:
            item_title = self._optional_child_text(item, None, "title")
            item_description = self._optional_child_text(item, None, "description")
            item_link = self._optional_child_text(item, None, "link")
            item_guid = self._optional_child_text(item, None, "guid")
            if item_title is None and item_description is None:
                _fail("SOURCE_PUBLIC_HTTP_PARSE_REQUIRED_FIELD_MISSING")
            if item_link is None and item_guid is None:
                _fail("SOURCE_PUBLIC_HTTP_PARSE_REQUIRED_FIELD_MISSING")
            if item_link is not None:
                self._validate_declared_http_url(item_link)
            item_date = self._optional_child_text(item, None, "pubDate")
            if item_date is not None:
                self._parse_rss_timestamp(item_date)

        last_build_date = self._optional_child_text(
            channel,
            None,
            "lastBuildDate",
        )
        channel_pub_date = self._optional_child_text(channel, None, "pubDate")
        published_at = None
        if last_build_date is not None:
            published_at = self._parse_rss_timestamp(last_build_date)
        elif channel_pub_date is not None:
            published_at = self._parse_rss_timestamp(channel_pub_date)

        language = self._optional_child_text(channel, None, "language")
        return ProviderHttpParsedSource(
            external_id=canonical_url,
            canonical_url=canonical_url,
            publisher_or_issuer=title,
            published_at=published_at,
            language_code=self._normalize_language(language),
        )

    def _parse_atom(
        self,
        root: ElementTree.Element,
        *,
        canonical_url: str,
    ) -> ProviderHttpParsedSource:
        feed_id = self._required_child_text(root, ATOM_NAMESPACE, "id")
        title = self._required_child_text(root, ATOM_NAMESPACE, "title")
        updated = self._required_child_text(root, ATOM_NAMESPACE, "updated")
        published_at = self._parse_atom_timestamp(updated)

        entries = self._direct_children(
            root,
            namespace=ATOM_NAMESPACE,
            local_name="entry",
        )
        self._require_all_named_elements_direct(
            root,
            namespace=ATOM_NAMESPACE,
            local_name="entry",
            expected_count=len(entries),
        )
        if len(entries) > self.profile.max_items:
            _fail("SOURCE_PUBLIC_HTTP_PARSE_PROFILE_EXCEEDED")
        for entry in entries:
            self._required_child_text(entry, ATOM_NAMESPACE, "id")
            self._required_child_text(entry, ATOM_NAMESPACE, "title")
            entry_updated = self._required_child_text(
                entry,
                ATOM_NAMESPACE,
                "updated",
            )
            self._parse_atom_timestamp(entry_updated)

        language = root.attrib.get(XML_LANGUAGE_ATTRIBUTE)
        if language is not None:
            language = self._bounded_metadata(language)
        return ProviderHttpParsedSource(
            external_id=feed_id,
            canonical_url=canonical_url,
            publisher_or_issuer=title,
            published_at=published_at,
            language_code=self._normalize_language(language),
        )

    def _direct_children(
        self,
        parent: ElementTree.Element,
        *,
        namespace: str | None,
        local_name: str,
    ) -> tuple[ElementTree.Element, ...]:
        matches: list[ElementTree.Element] = []
        for child in list(parent):
            child_namespace, child_name = _tag_parts(child.tag)
            if child_namespace == namespace and child_name == local_name:
                matches.append(child)
        return tuple(matches)

    def _require_all_named_elements_direct(
        self,
        root: ElementTree.Element,
        *,
        namespace: str | None,
        local_name: str,
        expected_count: int,
    ) -> None:
        actual_count = 0
        for element in root.iter():
            element_namespace, element_name = _tag_parts(element.tag)
            if element_namespace == namespace and element_name == local_name:
                actual_count += 1
        if actual_count != expected_count:
            _fail("SOURCE_PUBLIC_HTTP_PARSE_FIELD_INVALID")

    def _required_child_text(
        self,
        parent: ElementTree.Element,
        namespace: str | None,
        local_name: str,
    ) -> str:
        value = self._single_child_text(parent, namespace, local_name)
        if value is None:
            _fail("SOURCE_PUBLIC_HTTP_PARSE_REQUIRED_FIELD_MISSING")
        return value

    def _optional_child_text(
        self,
        parent: ElementTree.Element,
        namespace: str | None,
        local_name: str,
    ) -> str | None:
        return self._single_child_text(parent, namespace, local_name)

    def _single_child_text(
        self,
        parent: ElementTree.Element,
        namespace: str | None,
        local_name: str,
    ) -> str | None:
        children = self._direct_children(
            parent,
            namespace=namespace,
            local_name=local_name,
        )
        if len(children) > 1:
            _fail("SOURCE_PUBLIC_HTTP_PARSE_FIELD_INVALID")
        if not children:
            return None
        value = _normalize_text("".join(children[0].itertext()))
        if not value:
            return None
        return self._bounded_metadata(value)

    def _bounded_metadata(self, value: str) -> str:
        normalized = _normalize_text(value)
        if not normalized or len(normalized) > self.profile.max_metadata_field_chars:
            _fail("SOURCE_PUBLIC_HTTP_PARSE_FIELD_INVALID")
        return normalized

    def _normalize_language(self, value: str | None) -> str | None:
        if value is None:
            return None
        if _LANGUAGE_CODE.fullmatch(value) is None:
            _fail("SOURCE_PUBLIC_HTTP_PARSE_FIELD_INVALID")
        return value.lower()

    def _validate_declared_http_url(self, value: str) -> None:
        try:
            parsed = urlsplit(value)
            port = parsed.port
        except ValueError as exc:
            raise FinalPublicHttpParseError(
                "SOURCE_PUBLIC_HTTP_PARSE_FIELD_INVALID"
            ) from exc
        if parsed.scheme not in {"http", "https"}:
            _fail("SOURCE_PUBLIC_HTTP_PARSE_FIELD_INVALID")
        if parsed.username is not None or parsed.password is not None:
            _fail("SOURCE_PUBLIC_HTTP_PARSE_FIELD_INVALID")
        if parsed.hostname is None or parsed.fragment:
            _fail("SOURCE_PUBLIC_HTTP_PARSE_FIELD_INVALID")
        if port not in (None, 80, 443):
            _fail("SOURCE_PUBLIC_HTTP_PARSE_FIELD_INVALID")

    def _parse_rss_timestamp(self, value: str) -> datetime:
        try:
            parsed = parsedate_to_datetime(value)
        except (TypeError, ValueError, OverflowError) as exc:
            raise FinalPublicHttpParseError(
                "SOURCE_PUBLIC_HTTP_PARSE_TIMESTAMP_INVALID"
            ) from exc
        if parsed.tzinfo is None:
            _fail("SOURCE_PUBLIC_HTTP_PARSE_TIMESTAMP_INVALID")
        return parsed.astimezone(UTC)

    def _parse_atom_timestamp(self, value: str) -> datetime:
        normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError as exc:
            raise FinalPublicHttpParseError(
                "SOURCE_PUBLIC_HTTP_PARSE_TIMESTAMP_INVALID"
            ) from exc
        if parsed.tzinfo is None:
            _fail("SOURCE_PUBLIC_HTTP_PARSE_TIMESTAMP_INVALID")
        return parsed.astimezone(UTC)


__all__ = [
    "ATOM_NAMESPACE",
    "RSS_ATOM_ACCEPT_HEADER",
    "RSS_ATOM_USER_AGENT",
    "StrictRssAtomCaptureDefinition",
    "StrictRssAtomParseProfile",
]
