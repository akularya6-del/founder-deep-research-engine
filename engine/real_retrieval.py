from __future__ import annotations

import hashlib
import html
import base64
from io import BytesIO
import json
import os
import re
import time
from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus, urlparse
from urllib.request import Request, urlopen


class RetrievalConfigurationError(RuntimeError):
    pass


class RetrievalError(RuntimeError):
    pass


@dataclass(frozen=True)
class SearchResult:
    query: str
    url: str
    title: str
    snippet: str
    provider: str
    retrieved_at: str


@dataclass(frozen=True)
class SourceArtifact:
    source_id: str
    url: str
    retrieved_at: str
    http_status: int
    content_type: str
    content_hash: str
    title: str
    text: str
    excerpt: str
    provider: str


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_ignored = 0
        self.title_parts: list[str] = []
        self.text_parts: list[str] = []
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript", "svg", "template"}:
            self.in_ignored += 1
        if tag == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "svg", "template"} and self.in_ignored:
            self.in_ignored -= 1
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_ignored:
            return
        value = re.sub(r"\s+", " ", html.unescape(data)).strip()
        if not value:
            return
        if self._in_title:
            self.title_parts.append(value)
        elif len(value) > 1:
            self.text_parts.append(value)

    @property
    def title(self) -> str:
        return " ".join(self.title_parts).strip()

    @property
    def text(self) -> str:
        return "\n".join(self.text_parts).strip()


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _require_http_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise RetrievalError(f"Refusing non-http URL: {url}")


def _json_request(url: str, payload: dict[str, Any], headers: dict[str, str], timeout: int) -> Any:
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise RetrievalError(f"JSON request failed for {url}: {exc}") from exc


class SearchProvider:
    name = "abstract"

    def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        raise NotImplementedError


class TavilySearchProvider(SearchProvider):
    name = "tavily"

    def __init__(self, api_key: str | None = None, endpoint: str | None = None, timeout: int = 30) -> None:
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        self.endpoint = endpoint or os.getenv("TAVILY_ENDPOINT", "https://api.tavily.com/search")
        self.timeout = timeout
        if not self.api_key:
            raise RetrievalConfigurationError("TAVILY_API_KEY is required for the Tavily provider.")

    def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        payload = {"api_key": self.api_key, "query": query, "max_results": limit, "search_depth": "advanced"}
        data = _json_request(self.endpoint, payload, {}, self.timeout)
        results = []
        for item in data.get("results", []):
            url = item.get("url", "")
            if not url:
                continue
            results.append(SearchResult(query, url, item.get("title", ""), item.get("content", ""), self.name, _now()))
        return results


class FirecrawlSearchProvider(SearchProvider):
    name = "firecrawl"

    def __init__(self, api_key: str | None = None, endpoint: str | None = None, timeout: int = 30) -> None:
        self.api_key = api_key or os.getenv("FIRECRAWL_API_KEY")
        self.endpoint = endpoint or os.getenv("FIRECRAWL_SEARCH_ENDPOINT", "https://api.firecrawl.dev/v2/search")
        self.timeout = timeout
        if not self.api_key:
            raise RetrievalConfigurationError("FIRECRAWL_API_KEY is required for the Firecrawl provider.")

    def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        data = _json_request(
            self.endpoint,
            {"query": query, "limit": limit},
            {"Authorization": f"Bearer {self.api_key}"},
            self.timeout,
        )
        items = data.get("data", data.get("results", []))
        results = []
        for item in items:
            url = item.get("url", "")
            if not url:
                continue
            results.append(SearchResult(query, url, item.get("title", ""), item.get("description", item.get("markdown", "")), self.name, _now()))
        return results


class SearXNGSearchProvider(SearchProvider):
    name = "searxng"

    def __init__(self, endpoint: str | None = None, timeout: int = 30) -> None:
        self.endpoint = (endpoint or os.getenv("SEARXNG_ENDPOINT", "")).rstrip("/")
        self.timeout = timeout
        if not self.endpoint:
            raise RetrievalConfigurationError("SEARXNG_ENDPOINT is required for the SearXNG provider.")

    def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        url = f"{self.endpoint}/search?q={quote_plus(query)}&format=json"
        request = Request(url, headers={"User-Agent": "FounderResearchSystem/2.0"})
        try:
            with urlopen(request, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            raise RetrievalError(f"SearXNG request failed: {exc}") from exc
        results = []
        for item in data.get("results", [])[:limit]:
            if item.get("url"):
                results.append(SearchResult(query, item["url"], item.get("title", ""), item.get("content", ""), self.name, _now()))
        return results


class BingHtmlSearchProvider(SearchProvider):
    """Small, rate-limited public Bing HTML adapter used when API providers fail."""
    name = "bing_html"

    def __init__(self, timeout: int | None = None) -> None:
        self.timeout = timeout or int(os.getenv("BING_TIMEOUT", "8"))

    @staticmethod
    def _destination(href: str) -> str:
        if "bing.com/ck/a" not in href or "u=a1" not in href:
            return href
        try:
            encoded = href.split("u=a1", 1)[1].split("&", 1)[0]
            return base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)).decode("utf-8", "ignore")
        except Exception:
            return href

    def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        url = "https://www.bing.com/search?q=" + quote_plus(query) + "&count=" + str(min(limit, 10))
        request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urlopen(request, timeout=self.timeout) as response:
                body = response.read().decode("utf-8", "replace")
        except Exception as exc:
            raise RetrievalError(f"Bing HTML request failed: {exc}") from exc
        results: list[SearchResult] = []
        blocks = re.split(r'<li class="b_algo"', body, flags=re.I)[1:]
        for item in blocks[:limit]:
            anchor_match = re.search(r'<h2[^>]*>\s*<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', item, flags=re.I | re.S)
            if not anchor_match:
                continue
            destination = self._destination(html.unescape(anchor_match.group(1)))
            if not destination.startswith(("http://", "https://")):
                continue
            title = re.sub(r"<[^>]+>", " ", anchor_match.group(2))
            caption_match = re.search(r'<div class="b_caption".*?</div>', item, flags=re.I | re.S)
            snippet = caption_match.group(0) if caption_match else item
            snippet = re.sub(r"<[^>]+>", " ", snippet)
            results.append(SearchResult(query, destination, " ".join(html.unescape(title).split()), " ".join(html.unescape(snippet).split()), self.name, _now()))
        return results


def provider_from_environment(name: str | None = None) -> SearchProvider:
    selected = (name or os.getenv("RESEARCH_SEARCH_PROVIDER", "")).lower().strip()
    if selected == "tavily":
        return TavilySearchProvider()
    if selected == "firecrawl":
        return FirecrawlSearchProvider()
    if selected == "searxng":
        return SearXNGSearchProvider()
    if selected in {"bing", "bing_html"}:
        return BingHtmlSearchProvider()
    raise RetrievalConfigurationError(
        "No live search provider configured. Set RESEARCH_SEARCH_PROVIDER to tavily, firecrawl, or searxng."
    )


def fetch_source(url: str, provider: str = "urllib", timeout: int = 30, max_bytes: int = 5_000_000) -> SourceArtifact:
    _require_http_url(url)
    request = Request(url, headers={"User-Agent": "FounderResearchSystem/2.0 (+public-research; contact route not automated)"})
    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read(max_bytes + 1)
            status = getattr(response, "status", 200)
            content_type = response.headers.get("Content-Type", "")
    except Exception as exc:
        raise RetrievalError(f"Source fetch failed for {url}: {exc}") from exc
    if len(body) > max_bytes:
        raise RetrievalError(f"Source exceeds max_bytes={max_bytes}: {url}")
    is_pdf = "application/pdf" in content_type.lower() or body[:4] == b"%PDF"
    if is_pdf:
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RetrievalError("PDF source requires pypdf; install requirements-live.txt.") from exc
        try:
            reader = PdfReader(BytesIO(body))
            text = "\n".join((page.extract_text() or "") for page in reader.pages).strip()
        except Exception as exc:
            raise RetrievalError(f"PDF text extraction failed for {url}: {exc}") from exc
        if not text:
            raise RetrievalError(f"PDF contains no extractable text: {url}")
        title = Path(urlparse(url).path).name or "PDF document"
    else:
        raw = body.decode("utf-8", errors="replace")
        parser = _TextExtractor()
        parser.feed(raw)
        text = parser.text if parser.text else re.sub(r"\s+", " ", raw).strip()
        title = parser.title
    content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    source_id = "SRC-" + hashlib.sha256((url + "|" + content_hash).encode("utf-8")).hexdigest()[:20]
    excerpt = text[:1200]
    return SourceArtifact(source_id, url, _now(), int(status), content_type, content_hash, title, text, excerpt, provider)


def as_json(obj: SearchResult | SourceArtifact) -> dict[str, Any]:
    return asdict(obj)
