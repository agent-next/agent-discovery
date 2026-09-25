"""Literature search connector — Europe PMC REST API.

Paper: the fixed-input benchmark's level L5 exercises "literature search"
(Methods "Fixed-input benchmark", p.38) and campaign sessions had a literature
connector (Methods, p.28). The paper does not name the provider (NOT-IN-PAPER);
Europe PMC is used here because it exposes a free REST API with open-access
full text.

Offline-first: ``EuropePMCClient(live=False)`` (the default) never touches the
network — pass ``transport`` to replay recorded responses, or ``live=True`` to
use ``urllib.request``. Endpoint paths, field names and paging are all
NOT-IN-PAPER implementation details.
"""

from __future__ import annotations

import json
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from urllib.parse import urlencode


@dataclass
class PaperRef:
    """One Europe PMC search result (resultList.result[] fields)."""

    id: str
    source: str  # Europe PMC source code, e.g. "MED", "PMC"
    pmid: str | None
    doi: str | None
    title: str
    authors: str  # authorString, verbatim
    journal: str | None
    year: str | None
    is_open_access: bool = False
    in_pmc: bool = False

    @staticmethod
    def _flag(v: str | None) -> bool:
        # live API returns UPPERCASE "Y"/"N" (probed 2026-09-24); lowercase
        # comparisons made every MED record look non-OA (S1 finding, live-verified)
        return (v or "").strip().lower() == "y"

    @classmethod
    def from_result(cls, r: dict) -> PaperRef:
        return cls(
            id=r.get("id", ""),
            source=r.get("source", ""),
            pmid=r.get("pmid"),
            doi=r.get("doi"),
            title=r.get("title", ""),
            authors=r.get("authorString", ""),
            journal=r.get("journalTitle"),
            year=r.get("pubYear"),
            is_open_access=cls._flag(r.get("isOpenAccess")),
            in_pmc=cls._flag(r.get("inPMC")) or r.get("source") == "PMC",
        )

    @property
    def pmcid(self) -> str | None:
        """'PMC'-prefixed id for the fullTextXML endpoint, when in PMC."""
        if not self.in_pmc:
            return None
        return self.id if self.id.upper().startswith("PMC") else f"PMC{self.id}"


class EuropePMCClient:
    """Minimal Europe PMC client (search + open-access full text)."""

    BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest"

    def __init__(self, live: bool = False,
                 transport: Callable[[str], str] | None = None) -> None:
        self.live = live
        self._transport = transport

    def _get(self, url: str) -> str:
        if self._transport is not None:
            return self._transport(url)
        if not self.live:
            raise RuntimeError(
                "EuropePMCClient is offline: pass live=True for real HTTP or "
                "transport=<callable(url)->str> to replay recorded fixtures"
            )
        with urllib.request.urlopen(url, timeout=30) as resp:
            return resp.read().decode("utf-8")

    MAX_PAGE = 1000  # Europe PMC pageSize cap (errCode 404 above it, probed)

    def search(self, query: str, limit: int = 25) -> list[PaperRef]:
        """``GET /search?query=...&format=json`` -> parsed ``resultList.result``.

        Errors must not masquerade as zero hits: an ``errCode`` payload raises
        (HTTP 200 error envelopes are how this API reports bad params/rate
        limits — probed 2026-09-24 with pageSize=2000). Pages past the first are
        followed via ``nextCursorMark`` so callers actually get ``limit`` hits.
        """
        page_size = min(limit, self.MAX_PAGE)
        out: list[PaperRef] = []
        cursor: str | None = None
        while len(out) < limit:
            params = {"query": query, "format": "json", "pageSize": page_size}
            if cursor:
                params["cursorMark"] = cursor
            payload = json.loads(self._get(f"{self.BASE}/search?" + urlencode(params)))
            if "errCode" in payload or "errMsg" in payload:
                raise RuntimeError(
                    f"Europe PMC error {payload.get('errCode')}: "
                    f"{payload.get('errMsg')}")
            results = payload.get("resultList", {}).get("result", [])
            out.extend(PaperRef.from_result(r) for r in results)
            nxt = payload.get("nextCursorMark")
            if not results or not nxt or nxt == cursor:
                break
            cursor = nxt
        return out[:limit]

    def full_text_url(self, ref: PaperRef) -> str | None:
        """fullTextXML endpoint when the record is in PMC, else ``None``."""
        if ref.pmcid is None:
            return None
        return f"{self.BASE}/{ref.pmcid}/fullTextXML"

    def landing_url(self, ref: PaperRef) -> str:
        """Publisher landing page via DOI, else the Europe PMC record page."""
        if ref.doi:
            return f"https://doi.org/{ref.doi}"
        return f"https://europepmc.org/article/{ref.source}/{ref.id}"

    def fetch_full_text(self, ref: PaperRef) -> str | None:
        """JATS XML for PMC records; ``None`` otherwise (see :meth:`landing_url`)."""
        url = self.full_text_url(ref)
        if url is None:
            return None
        return self._get(url)
