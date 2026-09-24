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
            is_open_access=r.get("isOpenAccess") == "y",
            in_pmc=r.get("inPMC") == "y" or r.get("source") == "PMC",
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

    def search(self, query: str, limit: int = 25) -> list[PaperRef]:
        """``GET /search?query=...&format=json`` -> parsed ``resultList.result``."""
        url = f"{self.BASE}/search?" + urlencode(
            {"query": query, "format": "json", "pageSize": limit}
        )
        payload = json.loads(self._get(url))
        results = payload.get("resultList", {}).get("result", [])
        return [PaperRef.from_result(r) for r in results]

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
