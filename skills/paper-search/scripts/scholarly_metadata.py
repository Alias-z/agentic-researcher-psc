#!/usr/bin/env python3
"""Public scholarly metadata: paged PubMed/UniProt searches and verified DOI lookup.

Standard library only. No Zotero access, credentials, PDFs, or browser internals.
"""

import argparse
import html
import json
import re
import time
import unicodedata
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlparse
from urllib.request import Request, urlopen

from screen_batch import validate_candidate, write_private_json
from zotero_check import normalize_doi, normalize_year


NCBI = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
UNIPROT = "https://rest.uniprot.org/citations/search"
CROSSREF = "https://api.crossref.org/works"
USER_AGENT = "PSC-paper-search/1.0 (public scholarly metadata)"


def text(value):
    return html.unescape(re.sub(r"<[^>]+>", "", str(value or ""))).strip()


def title_key(value):
    value = unicodedata.normalize("NFKD", text(value).casefold())
    return " ".join(re.findall(r"\w+", "".join(c for c in value if not unicodedata.combining(c))))


def author_family(value):
    """Handle family-first API names and abbreviated Scholar names conservatively."""
    if isinstance(value, list):
        value = value[0] if value else ""
    if isinstance(value, dict):
        return title_key(value.get("family") or value.get("lastName") or value.get("name"))
    value = re.split(r"\s+(?:et\s+al\.?|and)\b|[;&…]", str(value or ""), maxsplit=1)[0]
    if "," in value:
        value = value.split(",", 1)[0]
    words = value.strip().split()
    # Initials such as S., SAM, Y.N., or S M do not identify a surname.
    names = [word for word in words if not re.fullmatch(r"(?:[A-Z]\.?){1,4}", word)]
    return title_key(" ".join(names) if names else value)


class Client:
    def __init__(self, cache_path=None):
        self.cache_path = cache_path
        self.cache = json.loads(cache_path.read_text()) if cache_path and cache_path.exists() else {}
        self.last_request = {}

    def get(self, url, kind="json"):
        cache_key = kind + ":" + url
        if cache_key in self.cache:
            return self.cache[cache_key]
        host = urlparse(url).hostname
        if host not in ("eutils.ncbi.nlm.nih.gov", "rest.uniprot.org", "api.crossref.org"):
            raise ValueError("Only official NCBI, UniProt, and Crossref metadata URLs are supported")
        interval = 1.0 if host == "api.crossref.org" else 0.4
        for attempt in range(3):
            time.sleep(max(0, interval - (time.monotonic() - self.last_request.get(host, 0))))
            self.last_request[host] = time.monotonic()
            try:
                with urlopen(Request(url, headers={"User-Agent": USER_AGENT,
                                                  "Accept": "application/json" if kind == "json" else "application/xml"}),
                             timeout=20) as response:
                    raw = response.read().decode("utf-8")
                    body = json.loads(raw) if kind == "json" else raw
                    result = {"body": body, "next_url": next_link(response.headers.get("Link", "")),
                              "total": response.headers.get("X-Total-Results")}
                self.cache[cache_key] = result
                if self.cache_path:
                    write_private_json(self.cache_path, self.cache)
                return result
            except HTTPError as error:
                if error.code not in (429, 500, 502, 503, 504) or attempt == 2:
                    raise
                delay = error.headers.get("Retry-After", "")
                delay = int(delay) if delay.isdigit() else 2 ** (attempt + 1)
                if delay > 30:
                    raise  # Leave long server backoffs for a later run.
                time.sleep(max(1, delay))


def next_link(header):
    for part in header.split(","):
        match = re.search(r'<([^>]+)>;\s*rel="?next"?', part)
        if match:
            return match.group(1)
    return ""


def pubmed_records(xml):
    records = []
    for item in ET.fromstring(xml).findall("PubmedArticle"):
        article = item.find(".//Article")
        pmid = item.findtext(".//MedlineCitation/PMID", "")
        title_element = article.find("ArticleTitle")
        title = "".join(title_element.itertext()) if title_element is not None else ""
        authors, families = [], []
        for author in article.findall("AuthorList/Author"):
            family = author.findtext("LastName", "")
            if family:
                families.append(family)
                authors.append((family + " " + author.findtext("Initials", "")).strip())
            else:
                authors.append(author.findtext("CollectiveName", ""))
        years = [normalize_year(element.text) for element in
                 article.findall("Journal/JournalIssue/PubDate/Year") + article.findall("ArticleDate/Year")]
        for date in item.findall("PubmedData/History/PubMedPubDate"):
            if date.get("PubStatus") in ("epublish", "ppublish"):
                years.append(normalize_year(date.findtext("Year")))
        year = next((year for year in years if year), "") or normalize_year(
            article.findtext("Journal/JournalIssue/PubDate/MedlineDate"))
        doi = next((e.text for e in item.findall("PubmedData/ArticleIdList/ArticleId")
                    if e.get("IdType") == "doi"), "")
        if not doi:
            doi = next((e.text for e in article.findall("ELocationID")
                        if e.get("EIdType") == "doi" and e.get("ValidYN", "Y") == "Y"), "")
        doi = normalize_doi(doi)
        abstract = []
        for section in article.findall("Abstract/AbstractText"):
            label = section.get("Label", "")
            abstract.append((label + ": " if label else "") + "".join(section.itertext()))
        url = "https://pubmed.ncbi.nlm.nih.gov/" + pmid + "/"
        records.append({"source_id": "pubmed:" + pmid, "source_url": url, "pmid": pmid,
                        "title": title, "authors": authors, "first_author": families[0] if families else "",
                        "year": year, "publication_years": sorted(set(filter(None, years + [year]))),
                        "journal": article.findtext("Journal/Title", ""),
                        "abstract": "\n".join(abstract), "summary_type": "author abstract",
                        "doi": doi, "doi_verified": bool(doi), "doi_status": "verified" if doi else "not_found",
                        "doi_provenance": url if doi else "", "topic_fit": "uncertain"})
    return records


def pubmed_fetch(client, pmids):
    records = {}
    pmids = list(dict.fromkeys(str(pmid) for pmid in pmids if str(pmid).isdigit()))
    for start in range(0, len(pmids), 100):
        url = NCBI + "efetch.fcgi?" + urlencode({"db": "pubmed", "retmode": "xml",
                                                 "id": ",".join(pmids[start:start + 100])})
        for record in pubmed_records(client.get(url, "xml")["body"]):
            records[record["pmid"]] = record
    return records


def pubmed_search(client, query, start, size):
    url = NCBI + "esearch.fcgi?" + urlencode({"db": "pubmed", "term": query, "retmode": "json",
                                              "sort": "relevance", "retstart": start, "retmax": size})
    found = client.get(url)["body"]["esearchresult"]
    if found.get("ERROR"):
        raise ValueError(found["ERROR"])
    pmids = found["idlist"]
    records = pubmed_fetch(client, pmids)
    ordered = []
    for rank, pmid in enumerate(pmids, start + 1):
        if pmid in records:
            ordered.append({**records[pmid], "source_rank": rank})
    total = int(found["count"])
    next_start = start + len(pmids) if pmids and start + len(pmids) < total else None
    return {"source": "pubmed", "total": total, "next_start": next_start,
            "query_translation": found.get("querytranslation", ""), "records": ordered}


def uniprot_search(client, query, start, size, next_url=None):
    url = next_url or UNIPROT + "?" + urlencode({"query": query, "format": "json", "size": size})
    parsed = urlparse(url)
    if parsed.hostname != "rest.uniprot.org" or parsed.path != "/citations/search":
        raise ValueError("--next-url must be the official UniProt citations next-page link")
    response = client.get(url)
    records = []
    for rank, entry in enumerate(response["body"].get("results", []), start + 1):
        citation = entry["citation"]
        refs = {ref["database"]: ref["id"] for ref in citation.get("citationCrossReferences", [])}
        doi = normalize_doi(refs.get("DOI", ""))
        citation_id = citation["id"]
        url = "https://www.uniprot.org/citations/" + citation_id
        authors = citation.get("authors", [])
        records.append({"source_id": "uniprot:" + citation_id, "source_url": url,
                        "source_rank": rank, "pmid": refs.get("PubMed", ""),
                        "title": text(citation.get("title")), "authors": authors,
                        "first_author": author_family(authors), "year": normalize_year(citation.get("publicationDate")),
                        "journal": citation.get("journal", ""),
                        "abstract": text(citation.get("literatureAbstract")), "summary_type": "author abstract",
                        "doi": doi, "doi_verified": bool(doi), "doi_status": "verified" if doi else "not_found",
                        "doi_provenance": url if doi else "", "topic_fit": "uncertain"})
    return {"source": "uniprot", "total": int(response["total"]) if response["total"] else None,
            "next_url": response["next_url"], "records": records}


def crossref_record(item):
    authors = item.get("author", [])
    years = []
    for field in ("published", "published-print", "published-online", "issued"):
        for parts in item.get(field, {}).get("date-parts", []):
            if parts:
                years.append(str(parts[0]))
    doi = normalize_doi(item.get("DOI"))
    return {"title": text(next(iter(item.get("title", [])), "")), "doi": doi,
            "authors": [(a.get("given", "") + " " + a.get("family", "")).strip() for a in authors],
            "first_author": authors[0].get("family", "") if authors else "",
            "year": years[0] if years else "", "publication_years": years,
            "journal": next(iter(item.get("container-title", [])), ""),
            "abstract": text(item.get("abstract")), "summary_type": "author abstract",
            "doi_provenance": "https://api.crossref.org/works/" + doi}


def same_paper(candidate, metadata, identified=False):
    if title_key(candidate.get("title")) != title_key(metadata.get("title")):
        return False
    year = normalize_year(candidate.get("year"))
    years = metadata.get("publication_years") or [normalize_year(metadata.get("year"))]
    if year and year not in years:
        return False
    family = author_family(candidate.get("first_author") or candidate.get("authors"))
    other = author_family(metadata.get("first_author") or metadata.get("authors"))
    if family and (not other or family != other):
        return False
    # An exact stable PMID or DOI also corroborates the title. A title query alone
    # needs a year or first author, rather than blindly accepting the first hit.
    return identified or bool(year or family)


def record_pmid(candidate):
    pmid = str(candidate.get("pmid") or "")
    if pmid.isdigit():
        return pmid
    match = re.search(r"pubmed\.ncbi\.nlm\.nih\.gov/(\d+)", candidate.get("source_url", ""))
    return match.group(1) if match else ""


def enrich(candidate, metadata):
    result = dict(candidate)
    result.update({"doi": metadata["doi"], "doi_verified": True, "doi_status": "verified",
                   "doi_provenance": metadata["doi_provenance"], "doi_reason": ""})
    for field in ("authors", "first_author", "year", "journal", "abstract", "summary_type", "pmid"):
        if not result.get(field) and metadata.get(field):
            result[field] = metadata[field]
    return result


def resolve_dois(client, candidates):
    pending = [c for c in candidates if c.get("topic_fit") != "no" and not c.get("doi_verified")]
    pmids = [record_pmid(c) for c in pending if record_pmid(c)]
    errors = []
    try:
        pubmed = pubmed_fetch(client, pmids)
    except (HTTPError, URLError, ValueError, ET.ParseError) as error:
        pubmed = {}
        errors.append("PubMed metadata unavailable: " + str(error))
    output = []
    for candidate in candidates:
        if candidate not in pending:
            output.append(dict(candidate))
            continue
        pmid = record_pmid(candidate)
        if pmid in pubmed and pubmed[pmid].get("doi") and same_paper(candidate, pubmed[pmid], identified=True):
            output.append(enrich(candidate, pubmed[pmid]))
            continue
        lookup_errors, matches = [], []
        try:
            doi = normalize_doi(candidate.get("doi"))
            if doi:
                message = client.get(CROSSREF + "/" + quote(doi, safe=""))["body"]["message"]
                record = crossref_record(message)
                if same_paper(candidate, record, identified=True):
                    matches.append(record)
            else:
                query = urlencode({"query.title": candidate["title"], "rows": 5})
                for item in client.get(CROSSREF + "?" + query)["body"]["message"]["items"]:
                    record = crossref_record(item)
                    if record["doi"] and same_paper(candidate, record):
                        matches.append(record)
        except (HTTPError, URLError, ValueError, KeyError) as error:
            lookup_errors.append("Crossref: " + str(error))
        unique = {record["doi"]: record for record in matches}
        if len(unique) == 1:
            output.append(enrich(candidate, next(iter(unique.values()))))
            continue
        if not unique and not pmid:
            try:
                found = pubmed_search(client, '"' + candidate["title"].rstrip(".") + '"[Title]', 0, 3)
                for record in found["records"]:
                    if record["doi"] and same_paper(candidate, record):
                        unique[record["doi"]] = record
            except (HTTPError, URLError, ValueError, ET.ParseError) as error:
                lookup_errors.append("PubMed: " + str(error))
            if len(unique) == 1:
                output.append(enrich(candidate, next(iter(unique.values()))))
                continue
        result = dict(candidate)
        result.update({"doi_verified": False, "doi_status": "unresolved",
                       "doi_reason": ("Multiple corroborated DOI records" if len(unique) > 1 else
                                      "Metadata lookup unavailable" if lookup_errors or (pmid and errors) else
                                      "No corroborated DOI in public metadata; inspect source detail")})
        output.append(result)
        errors.extend(lookup_errors)
    return {"records": output, "errors": list(dict.fromkeys(errors))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, help="Shared temporary metadata cache; use one DOI resolver queue")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("pubmed", "uniprot"):
        search = sub.add_parser(name)
        search.add_argument("--query", required=True)
        search.add_argument("--start", type=int, default=0)
        search.add_argument("--size", type=int, default=5)
        search.add_argument("--output", required=True, type=Path)
        if name == "uniprot":
            search.add_argument("--next-url")
    resolver = sub.add_parser("resolve-dois")
    resolver.add_argument("--input", required=True, type=Path)
    resolver.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    client = Client(args.cache)
    if args.command == "resolve-dois":
        candidates = json.loads(args.input.read_text())
        if not isinstance(candidates, list) or any(not isinstance(c, dict) or not c.get("title") for c in candidates):
            parser.error("--input must be an array of paper records with titles")
        for candidate in candidates:
            validate_candidate(candidate)
        result = resolve_dois(client, candidates)
    else:
        if args.start < 0 or not 1 <= args.size <= 100:
            parser.error("--start must be nonnegative; --size must be 1–100")
        if args.command == "pubmed":
            result = pubmed_search(client, args.query, args.start, args.size)
        else:
            result = uniprot_search(client, args.query, args.start, args.size, args.next_url)
    write_private_json(args.output, result)
    print(json.dumps({"records": len(result["records"]),
                      **{key: result[key] for key in ("total", "next_start", "next_url", "errors") if key in result}},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
