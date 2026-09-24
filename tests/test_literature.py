"""Tests for artharness.connectors.literature — Europe PMC offline transport."""

import json

import pytest

from artharness.connectors.literature import EuropePMCClient, PaperRef

SEARCH_JSON = json.dumps({
    "hitCount": 2,
    "resultList": {"result": [
        {
            "id": "7654321",
            "source": "PMC",
            "pmid": "111222",
            "doi": "10.1000/pmc.paper",
            "title": "A partner protein of clade RTs",
            "authorString": "Doe J, Roe K.",
            "journalTitle": "J Mol Biol",
            "pubYear": "2024",
            "inPMC": "y",
            "isOpenAccess": "y",
        },
        {
            "id": "998877",
            "source": "MED",
            "pmid": "998877",
            "doi": "10.1000/med.paper",
            "title": "Reverse transcriptases: a review",
            "authorString": "Smith A.",
            "journalTitle": "Virology",
            "pubYear": "2023",
            "inPMC": "n",
            "isOpenAccess": "n",
        },
    ]},
})

FULL_TEXT_XML = "<article><body>full text of the PMC record</body></article>"

FIXTURES = {
    "/search?": SEARCH_JSON,
    "/fullTextXML": FULL_TEXT_XML,
}


def _transport(urls):
    def transport(url):
        urls.append(url)
        for key, body in FIXTURES.items():
            if key in url:
                return body
        raise AssertionError(f"no recorded fixture for URL: {url}")
    return transport


def _client(urls):
    return EuropePMCClient(live=False, transport=_transport(urls))


def test_search_parses_result_list_into_paper_refs():
    urls = []
    refs = _client(urls).search("reverse transcriptase partner", limit=5)
    assert len(urls) == 1
    assert urls[0].startswith(f"{EuropePMCClient.BASE}/search?")
    assert "format=json" in urls[0]
    assert "pageSize=5" in urls[0]
    assert len(refs) == 2

    pmc, med = refs
    assert pmc.id == "7654321"
    assert pmc.source == "PMC"
    assert pmc.pmid == "111222"
    assert pmc.doi == "10.1000/pmc.paper"
    assert pmc.title == "A partner protein of clade RTs"
    assert pmc.authors == "Doe J, Roe K."
    assert pmc.journal == "J Mol Biol"
    assert pmc.year == "2024"
    assert pmc.in_pmc is True
    assert pmc.is_open_access is True

    assert med.id == "998877"
    assert med.source == "MED"
    assert med.in_pmc is False
    assert med.is_open_access is False


def test_full_text_url_only_for_pmc_records():
    client = _client([])
    pmc, med = client.search("q")
    assert pmc.pmcid == "PMC7654321"  # PMC prefix added to a bare numeric id
    assert client.full_text_url(pmc) == (
        f"{EuropePMCClient.BASE}/PMC7654321/fullTextXML")
    assert med.pmcid is None
    assert client.full_text_url(med) is None

    prefixed = PaperRef(id="PMC123", source="PMC", pmid=None, doi=None, title="t",
                        authors="", journal=None, year=None, in_pmc=True)
    assert prefixed.pmcid == "PMC123"  # no double prefix


def test_fetch_full_text_returns_fixture_xml_for_pmc():
    urls = []
    client = _client(urls)
    pmc, med = client.search("q")
    assert client.fetch_full_text(pmc) == FULL_TEXT_XML
    assert urls[-1].endswith("/PMC7654321/fullTextXML")
    assert client.fetch_full_text(med) is None


def test_landing_url_prefers_doi():
    client = _client([])
    pmc, med = client.search("q")
    assert client.landing_url(pmc) == "https://doi.org/10.1000/pmc.paper"
    assert client.landing_url(med) == "https://doi.org/10.1000/med.paper"
    no_doi = PaperRef(id="42", source="MED", pmid="42", doi=None, title="t",
                      authors="", journal=None, year=None)
    assert client.landing_url(no_doi) == "https://europepmc.org/article/MED/42"


def test_offline_client_without_transport_raises():
    with pytest.raises(RuntimeError):
        EuropePMCClient(live=False).search("q")
