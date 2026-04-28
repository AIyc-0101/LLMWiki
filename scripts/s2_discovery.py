#!/usr/bin/env python3
"""Semantic Scholar discovery workflow for LLMWiki.

Usage examples:
  export S2_API_KEY="xxx"
  python scripts/s2_discovery.py search
  python scripts/s2_discovery.py enrich-seeds
  python scripts/s2_discovery.py citations
  python scripts/s2_discovery.py references
  python scripts/s2_discovery.py authors
  python scripts/s2_discovery.py recommend
  python scripts/s2_discovery.py weekly
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import sqlite3
import sys
import time
import traceback
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd
import requests
import yaml

ROOT = Path(__file__).resolve().parents[1]
DISCOVERY_DIR = ROOT / "discovery"
S2_DIR = DISCOVERY_DIR / "semantic_scholar"
CONFIG_PATH = S2_DIR / "config.yaml"
QUERIES_PATH = S2_DIR / "queries.txt"
SEEDS_PATH = S2_DIR / "seed_papers.csv"
AUTHORS_PATH = S2_DIR / "tracked_authors.csv"
CACHE_PATH = S2_DIR / "semantic_cache.sqlite"
WEEKLY_BASENAME = "semantic_weekly"
INBOX_PATH = DISCOVERY_DIR / "inbox.csv"

INBOX_COLUMNS = [
    "source",
    "topic",
    "score",
    "priority",
    "title",
    "year",
    "venue",
    "authors",
    "doi",
    "arxiv_id",
    "s2_paper_id",
    "url",
    "open_access_pdf",
    "abstract",
    "reason",
    "discovered_at",
    "next_action",
]

BASE_PAPER_FIELDS = (
    "paperId,title,abstract,year,venue,publicationDate,authors,externalIds,"
    "citationCount,referenceCount,openAccessPdf,fieldsOfStudy,url"
)
CITATION_FIELDS = (
    "citingPaper.paperId,citingPaper.title,citingPaper.abstract,citingPaper.year,"
    "citingPaper.venue,citingPaper.publicationDate,citingPaper.authors,"
    "citingPaper.externalIds,citingPaper.citationCount,citingPaper.openAccessPdf,"
    "citingPaper.url"
)
REFERENCE_FIELDS = (
    "citedPaper.paperId,citedPaper.title,citedPaper.abstract,citedPaper.year,"
    "citedPaper.venue,citedPaper.publicationDate,citedPaper.authors,"
    "citedPaper.externalIds,citedPaper.citationCount,citedPaper.openAccessPdf,"
    "citedPaper.url"
)
AUTHOR_FIELDS = (
    "authorId,name,affiliations,paperCount,citationCount,hIndex,papers.paperId,"
    "papers.title,papers.year,papers.venue,papers.publicationDate,"
    "papers.citationCount,papers.externalIds,papers.url"
)


def setup_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def configure_stdio_encoding() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def pause_before_exit() -> None:
    if os.name != "nt" or os.environ.get("S2_NO_PAUSE") == "1":
        return
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        return

    print("\n运行结束。按任意键退出...", end="", flush=True)
    try:
        import msvcrt

        msvcrt.getch()
    except Exception:
        try:
            input()
        except EOFError:
            pass
    finally:
        print()


def now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def run_timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def weekly_paths(run_id: str) -> Tuple[Path, Path]:
    return S2_DIR / f"{WEEKLY_BASENAME}_{run_id}.csv", S2_DIR / f"{WEEKLY_BASENAME}_{run_id}.md"


def clean_text(value: Any) -> str:
    text = str(value or "").strip()
    return "".join(ch if ch == "\n" or ch == "\t" or ord(ch) >= 32 else " " for ch in text)


def ensure_csv(path: Path, columns: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        pd.DataFrame(columns=columns).to_csv(path, index=False, encoding="utf-8-sig", quoting=csv.QUOTE_MINIMAL)


def load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def read_csv_safe(path: Path, columns: List[str]) -> pd.DataFrame:
    ensure_csv(path, columns)
    try:
        df = pd.read_csv(path, dtype=str).fillna("")
    except pd.errors.EmptyDataError:
        return pd.DataFrame(columns=columns)
    for c in columns:
        if c not in df.columns:
            df[c] = ""
    return df[columns]


@dataclass
class ScoreResult:
    score: int
    grade: str
    reason: str


class S2Client:
    def __init__(self, config: Dict[str, Any]) -> None:
        s2_conf = config.get("semantic_scholar", {})
        self.base_url = s2_conf.get("base_url", "https://api.semanticscholar.org")
        self.interval = float(s2_conf.get("request_interval_seconds", 1.1))
        self.max_retries = int(s2_conf.get("max_retries", 5))
        self.timeout = int(s2_conf.get("timeout_seconds", 30))

        api_key = os.environ.get("S2_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("Missing Semantic Scholar API key. Please set environment variable S2_API_KEY.")

        self.session = requests.Session()
        self.session.headers.update({"x-api-key": api_key})
        self.last_request_ts = 0.0

    def _wait_rate_limit(self) -> None:
        elapsed = time.time() - self.last_request_ts
        if elapsed < self.interval:
            time.sleep(self.interval - elapsed)

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        retriable = {429, 500, 502, 503, 504}
        url = f"{self.base_url.rstrip('/')}{path}"

        for attempt in range(self.max_retries + 1):
            self._wait_rate_limit()
            try:
                logging.info("S2 request %s %s params=%s", method, path, params or {})
                resp = self.session.request(method=method, url=url, params=params, json=json_body, timeout=self.timeout)
                self.last_request_ts = time.time()
            except requests.RequestException as exc:
                if attempt >= self.max_retries:
                    logging.error("S2 request failed after retries: %s", exc)
                    return {}
                backoff = min(2**attempt, 30)
                logging.warning("S2 request exception: %s, retry in %.1fs", exc, backoff)
                time.sleep(backoff)
                continue

            if resp.status_code in retriable and attempt < self.max_retries:
                backoff = min(2**attempt, 30)
                logging.warning("S2 status %s, retry in %.1fs", resp.status_code, backoff)
                time.sleep(backoff)
                continue

            if not resp.ok:
                logging.error("S2 non-OK response: status=%s body=%s", resp.status_code, resp.text[:300])
                return {}

            try:
                return resp.json() if resp.text else {}
            except ValueError:
                logging.error("S2 response is not valid JSON: %s", resp.text[:300])
                return {}
        return {}

    def paper_search(self, query: str, limit: int, offset: int = 0, fields: str = BASE_PAPER_FIELDS) -> List[Dict[str, Any]]:
        data = self._request(
            "GET",
            "/graph/v1/paper/search",
            params={"query": query, "limit": limit, "offset": offset, "fields": fields},
        )
        return data.get("data", []) if isinstance(data, dict) else []

    def paper_search_bulk(self, query: str, limit: int, fields: str = BASE_PAPER_FIELDS) -> List[Dict[str, Any]]:
        data = self._request(
            "GET",
            "/graph/v1/paper/search/bulk",
            params={"query": query, "limit": limit, "fields": fields},
        )
        if isinstance(data, dict) and data.get("data"):
            return data.get("data", [])
        return self.paper_search(query=query, limit=limit, fields=fields)

    def paper_detail(self, paper_id: str, fields: str = BASE_PAPER_FIELDS) -> Dict[str, Any]:
        return self._request("GET", f"/graph/v1/paper/{paper_id}", params={"fields": fields})

    def paper_batch(self, ids: List[str], fields: str = BASE_PAPER_FIELDS) -> List[Dict[str, Any]]:
        data = self._request("POST", "/graph/v1/paper/batch", params={"fields": fields}, json_body={"ids": ids})
        return data if isinstance(data, list) else []

    def paper_citations(self, paper_id: str, limit: int, fields: str = CITATION_FIELDS) -> List[Dict[str, Any]]:
        data = self._request("GET", f"/graph/v1/paper/{paper_id}/citations", params={"limit": limit, "fields": fields})
        return data.get("data", []) if isinstance(data, dict) else []

    def paper_references(self, paper_id: str, limit: int, fields: str = REFERENCE_FIELDS) -> List[Dict[str, Any]]:
        data = self._request("GET", f"/graph/v1/paper/{paper_id}/references", params={"limit": limit, "fields": fields})
        return data.get("data", []) if isinstance(data, dict) else []

    def author_search(self, query: str, limit: int = 1) -> List[Dict[str, Any]]:
        data = self._request(
            "GET", "/graph/v1/author/search", params={"query": query, "limit": limit, "fields": "authorId,name,affiliations"}
        )
        return data.get("data", []) if isinstance(data, dict) else []

    def author_detail(self, author_id: str, fields: str = AUTHOR_FIELDS) -> Dict[str, Any]:
        return self._request("GET", f"/graph/v1/author/{author_id}", params={"fields": fields})

    def recommend_for_paper(self, paper_id: str, limit: int, fields: str = BASE_PAPER_FIELDS) -> List[Dict[str, Any]]:
        data = self._request(
            "GET",
            f"/recommendations/v1/papers/forpaper/{paper_id}",
            params={"limit": limit, "fields": fields},
        )
        return data.get("recommendedPapers", []) if isinstance(data, dict) else []


class SemanticCache:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self._init_schema()

    def close(self) -> None:
        self.conn.close()

    def _init_schema(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS papers (
              paperId TEXT PRIMARY KEY,
              title TEXT,
              year INTEGER,
              venue TEXT,
              doi TEXT,
              arxiv_id TEXT,
              url TEXT,
              open_access_pdf TEXT,
              abstract TEXT,
              authors TEXT,
              citationCount INTEGER,
              source TEXT,
              discovered_at TEXT,
              raw_json TEXT
            )
            """
        )
        self.conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_papers_doi ON papers(doi) WHERE doi IS NOT NULL AND doi <> ''")
        self.conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_papers_arxiv ON papers(arxiv_id) WHERE arxiv_id IS NOT NULL AND arxiv_id <> ''"
        )
        self.conn.commit()

    def find_existing_id(self, paper: Dict[str, Any]) -> Optional[str]:
        pid = paper.get("paperId", "")
        doi = paper.get("doi", "")
        arxiv_id = paper.get("arxiv_id", "")

        cur = self.conn.cursor()
        if pid:
            row = cur.execute("SELECT paperId FROM papers WHERE paperId=?", (pid,)).fetchone()
            if row:
                return row[0]
        if doi:
            row = cur.execute("SELECT paperId FROM papers WHERE doi=?", (doi,)).fetchone()
            if row:
                return row[0]
        if arxiv_id:
            row = cur.execute("SELECT paperId FROM papers WHERE arxiv_id=?", (arxiv_id,)).fetchone()
            if row:
                return row[0]
        return None

    def upsert_paper(self, paper: Dict[str, Any], source: str) -> bool:
        existing_id = self.find_existing_id(paper)
        discovered_at = now_iso()
        raw_json = json.dumps(paper.get("raw_json", {}), ensure_ascii=False)

        record = (
            paper.get("paperId", ""),
            paper.get("title", ""),
            int(paper.get("year") or 0),
            paper.get("venue", ""),
            paper.get("doi", ""),
            paper.get("arxiv_id", ""),
            paper.get("url", ""),
            paper.get("open_access_pdf", ""),
            paper.get("abstract", ""),
            paper.get("authors", ""),
            int(paper.get("citationCount") or 0),
            source,
            discovered_at,
            raw_json,
        )

        if not existing_id:
            try:
                self.conn.execute(
                    """
                    INSERT INTO papers (
                      paperId,title,year,venue,doi,arxiv_id,url,open_access_pdf,abstract,
                      authors,citationCount,source,discovered_at,raw_json
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    record,
                )
                self.conn.commit()
            except sqlite3.IntegrityError:
                self._merge_update(paper, source)
                return False
            return True

        self._merge_update(paper, source)
        return False

    def _merge_update(self, paper: Dict[str, Any], source: str) -> None:
        pid = self.find_existing_id(paper)
        if not pid:
            return
        cur = self.conn.cursor()
        row = cur.execute("SELECT open_access_pdf, abstract, citationCount FROM papers WHERE paperId=?", (pid,)).fetchone()
        if not row:
            return

        old_pdf, old_abstract, old_citation = row
        new_pdf = paper.get("open_access_pdf", "") or old_pdf
        new_abstract = paper.get("abstract", "") or old_abstract
        new_citation = max(int(old_citation or 0), int(paper.get("citationCount") or 0))

        cur.execute(
            """
            UPDATE papers
            SET title=?, year=?, venue=?, doi=?, arxiv_id=?, url=?, open_access_pdf=?,
                abstract=?, authors=?, citationCount=?, source=?, discovered_at=?, raw_json=?
            WHERE paperId=?
            """,
            (
                paper.get("title", ""),
                int(paper.get("year") or 0),
                paper.get("venue", ""),
                paper.get("doi", ""),
                paper.get("arxiv_id", ""),
                paper.get("url", ""),
                new_pdf,
                new_abstract,
                paper.get("authors", ""),
                new_citation,
                source,
                now_iso(),
                json.dumps(paper.get("raw_json", {}), ensure_ascii=False),
                pid,
            ),
        )
        self.conn.commit()


def parse_external_ids(external_ids: Dict[str, Any]) -> Tuple[str, str]:
    if not isinstance(external_ids, dict):
        return "", ""
    doi = str(external_ids.get("DOI") or "").strip()
    arxiv_id = str(external_ids.get("ArXiv") or external_ids.get("ARXIV") or "").strip()
    return doi, arxiv_id


def author_names(authors: Any) -> str:
    if not isinstance(authors, list):
        return ""
    return "; ".join([clean_text(a.get("name", "")) for a in authors if isinstance(a, dict) and a.get("name")])


def normalize_paper(p: Dict[str, Any]) -> Dict[str, Any]:
    external = p.get("externalIds", {}) if isinstance(p, dict) else {}
    doi, arxiv_id = parse_external_ids(external)
    open_pdf = ""
    open_access_pdf = p.get("openAccessPdf")
    if isinstance(open_access_pdf, dict):
        open_pdf = str(open_access_pdf.get("url") or "").strip()

    return {
        "paperId": str(p.get("paperId") or "").strip(),
        "title": clean_text(p.get("title")),
        "abstract": clean_text(p.get("abstract")),
        "year": p.get("year") or "",
        "venue": clean_text(p.get("venue")),
        "doi": doi,
        "arxiv_id": arxiv_id,
        "url": clean_text(p.get("url")),
        "open_access_pdf": open_pdf,
        "authors": author_names(p.get("authors")),
        "citationCount": int(p.get("citationCount") or 0),
        "raw_json": p,
    }


def score_paper(paper: Dict[str, Any], source: str) -> ScoreResult:
    title = paper.get("title", "").lower()
    abstract = paper.get("abstract", "").lower()
    year = int(paper.get("year") or 0)
    citation_count = int(paper.get("citationCount") or 0)
    score = 0
    reasons: List[str] = []

    if any(k in title for k in ["structured illumination microscopy", " sim ", "microscopy super-resolution"]) or "sim reconstruction" in title:
        score += 4
        reasons.append("title matches SIM/microscopy super-resolution")

    if any(k in abstract for k in ["reconstruction", "super-resolution", "inverse problem", "physics-informed"]):
        score += 3
        reasons.append("abstract includes reconstruction/super-resolution keywords")

    if any(k in (title + " " + abstract) for k in ["multimodal", "vision-language", "large language model", "foundation model"]):
        score += 3
        reasons.append("mentions multimodal/VLM/LLM/foundation model")

    now_year = datetime.utcnow().year
    if year and year >= now_year - 2:
        score += 2
        reasons.append("recent paper")

    if paper.get("open_access_pdf"):
        score += 2
        reasons.append("has open access pdf")

    if citation_count >= 50:
        score += 2
        reasons.append("high citation count")

    if source in {"semantic_citation", "semantic_recommendation"}:
        score += 2
        reasons.append("high-value discovery source")

    if paper.get("venue"):
        score += 1
        reasons.append("venue available")

    text = f"{title} {abstract}"
    if "clinical diagnosis" in text and "reconstruction" not in text:
        score -= 3
        reasons.append("purely clinical diagnosis")
    if "biological experiment" in text and "algorithm" not in text:
        score -= 3
        reasons.append("pure biological experiment without algorithm")
    if "survey" in text and "reconstruction" not in text:
        score -= 2
        reasons.append("survey-like and less aligned")

    grade = "A" if score >= 8 else "B" if score >= 4 else "C"
    return ScoreResult(score=score, grade=grade, reason="; ".join(reasons) if reasons else "baseline score")


def record_identity(record: Dict[str, Any]) -> Tuple[str, str]:
    s2_id = str(record.get("s2_paper_id") or record.get("paperId") or "").strip()
    doi = str(record.get("doi") or "").strip().lower()
    arxiv_id = str(record.get("arxiv_id") or "").strip().lower()
    if s2_id or doi or arxiv_id:
        return ("id", f"{s2_id}|{doi}|{arxiv_id}")

    title = str(record.get("title") or "").strip().lower()
    year = str(record.get("year") or "").strip()
    return ("title_year", f"{title}|{year}")


def unique_records(records: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    out: List[Dict[str, Any]] = []
    for r in records:
        key = record_identity(r)
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


def append_rows(path: Path, rows: List[Dict[str, Any]], columns: List[str]) -> None:
    ensure_csv(path, columns)
    if not rows:
        return
    old = read_csv_safe(path, columns)
    new = pd.DataFrame(rows)
    for col in columns:
        if col not in new.columns:
            new[col] = ""

    existing_rows = old.fillna("").to_dict("records")
    existing_keys = {record_identity(r) for r in existing_rows}

    appendable_rows: List[Dict[str, Any]] = []
    for row in new[columns].fillna("").to_dict("records"):
        key = record_identity(row)
        if key in existing_keys:
            continue
        existing_keys.add(key)
        appendable_rows.append(row)

    if not appendable_rows:
        return

    combined = pd.concat([old, pd.DataFrame(appendable_rows, columns=columns)], ignore_index=True)
    combined = combined.fillna("")
    combined.to_csv(path, index=False, encoding="utf-8-sig", quoting=csv.QUOTE_MINIMAL)


def write_rows(path: Path, rows: List[Dict[str, Any]], columns: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    for col in columns:
        if col not in df.columns:
            df[col] = ""
    df[columns].fillna("").to_csv(path, index=False, encoding="utf-8-sig", quoting=csv.QUOTE_MINIMAL)


def load_queries() -> List[str]:
    if not QUERIES_PATH.exists():
        return []
    return [line.strip() for line in QUERIES_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]


def paper_to_output(p: Dict[str, Any], source: str, topic: str, priority: str) -> Dict[str, Any]:
    score = score_paper(p, source)
    return {
        "source": source,
        "topic": topic,
        "score": score.score,
        "priority": priority,
        "title": p.get("title", ""),
        "year": p.get("year", ""),
        "venue": p.get("venue", ""),
        "authors": p.get("authors", ""),
        "doi": p.get("doi", ""),
        "arxiv_id": p.get("arxiv_id", ""),
        "s2_paper_id": p.get("paperId", ""),
        "url": p.get("url", ""),
        "open_access_pdf": p.get("open_access_pdf", ""),
        "abstract": p.get("abstract", ""),
        "reason": score.reason,
        "discovered_at": now_iso(),
        "next_action": "download_pdf" if score.grade == "A" else "review",
        "grade": score.grade,
    }


def command_search(client: S2Client, cache: SemanticCache, config: Dict[str, Any]) -> List[Dict[str, Any]]:
    queries = load_queries()
    limit = int(config.get("search", {}).get("limit_per_query", 50))
    min_year = int(config.get("search", {}).get("min_year", 2023))
    outputs: List[Dict[str, Any]] = []

    for q in queries:
        query_count = 0
        for item in client.paper_search(q, limit=limit):
            p = normalize_paper(item)
            if int(p.get("year") or 0) and int(p.get("year") or 0) < min_year:
                continue
            is_new = cache.upsert_paper(p, source="semantic_search")
            if is_new:
                out = paper_to_output(p, source="semantic_search", topic=q, priority="medium")
                outputs.append(out)
            query_count += 1
            if query_count >= limit:
                break

    return outputs


def build_seed_ids(df: pd.DataFrame) -> List[str]:
    ids: List[str] = []
    for _, row in df.iterrows():
        if row.get("s2_paper_id"):
            ids.append(str(row["s2_paper_id"]))
        elif row.get("doi"):
            ids.append(f"DOI:{row['doi']}")
        elif row.get("arxiv_id"):
            ids.append(f"ARXIV:{row['arxiv_id']}")
    return [i for i in ids if i]


def command_enrich_seeds(client: S2Client) -> None:
    seeds = read_csv_safe(SEEDS_PATH, ["title", "doi", "arxiv_id", "s2_paper_id", "topic", "priority", "note"])
    ids = build_seed_ids(seeds)
    if not ids:
        logging.info("No seed IDs available to enrich.")
        return

    enriched = client.paper_batch(ids, fields=BASE_PAPER_FIELDS)
    by_title = {str(x.get("title", "")).strip().lower(): x for x in enriched if isinstance(x, dict)}
    by_id = {str(x.get("paperId", "")).strip(): x for x in enriched if isinstance(x, dict)}

    updated = []
    for _, row in seeds.iterrows():
        rowd = row.to_dict()
        pick = None
        sid = rowd.get("s2_paper_id", "")
        if sid and sid in by_id:
            pick = by_id[sid]
        elif rowd.get("title", "").strip().lower() in by_title:
            pick = by_title[rowd.get("title", "").strip().lower()]
        if pick:
            p = normalize_paper(pick)
            rowd["title"] = p.get("title") or rowd["title"]
            rowd["doi"] = p.get("doi") or rowd["doi"]
            rowd["arxiv_id"] = p.get("arxiv_id") or rowd["arxiv_id"]
            rowd["s2_paper_id"] = p.get("paperId") or rowd["s2_paper_id"]
        updated.append(rowd)

    pd.DataFrame(updated).to_csv(SEEDS_PATH, index=False, encoding="utf-8-sig", quoting=csv.QUOTE_MINIMAL)


def seed_rows_for_tracking() -> pd.DataFrame:
    cols = ["title", "doi", "arxiv_id", "s2_paper_id", "topic", "priority", "note"]
    seeds = read_csv_safe(SEEDS_PATH, cols)
    if "priority" not in seeds.columns:
        return seeds
    ab = seeds[seeds["priority"].str.upper().isin(["A", "B"])].copy()
    return ab if not ab.empty else seeds


def command_citations(client: S2Client, cache: SemanticCache, config: Dict[str, Any]) -> List[Dict[str, Any]]:
    max_n = int(config.get("citation_tracking", {}).get("max_citations_per_seed", 50))
    seeds = seed_rows_for_tracking()
    outputs: List[Dict[str, Any]] = []
    for _, row in seeds.iterrows():
        pid = str(row.get("s2_paper_id", "")).strip()
        if not pid:
            continue
        for item in client.paper_citations(pid, limit=max_n):
            cp = item.get("citingPaper") if isinstance(item, dict) else None
            if not isinstance(cp, dict):
                continue
            p = normalize_paper(cp)
            if cache.upsert_paper(p, source="semantic_citation"):
                outputs.append(paper_to_output(p, "semantic_citation", str(row.get("topic", "")), str(row.get("priority", ""))))
    return outputs


def command_references(client: S2Client, cache: SemanticCache, config: Dict[str, Any]) -> List[Dict[str, Any]]:
    max_n = int(config.get("reference_tracking", {}).get("max_references_per_seed", 50))
    seeds = seed_rows_for_tracking()
    outputs: List[Dict[str, Any]] = []
    for _, row in seeds.iterrows():
        pid = str(row.get("s2_paper_id", "")).strip()
        if not pid:
            continue
        for item in client.paper_references(pid, limit=max_n):
            rp = item.get("citedPaper") if isinstance(item, dict) else None
            if not isinstance(rp, dict):
                continue
            p = normalize_paper(rp)
            if cache.upsert_paper(p, source="semantic_reference"):
                outputs.append(paper_to_output(p, "semantic_reference", str(row.get("topic", "")), str(row.get("priority", ""))))
    return outputs


def command_authors(client: S2Client, cache: SemanticCache, config: Dict[str, Any]) -> List[Dict[str, Any]]:
    cols = ["name", "s2_author_id", "affiliation", "topic", "note"]
    authors = read_csv_safe(AUTHORS_PATH, cols)
    min_year = int(config.get("author_tracking", {}).get("min_year", 2023))
    max_papers = int(config.get("author_tracking", {}).get("max_papers_per_author", 50))
    outputs: List[Dict[str, Any]] = []

    enriched_rows = []
    for _, row in authors.iterrows():
        rowd = row.to_dict()
        aid = str(rowd.get("s2_author_id", "")).strip()
        if not aid and rowd.get("name"):
            found = client.author_search(rowd["name"], limit=1)
            if found:
                aid = str(found[0].get("authorId") or "")
                rowd["s2_author_id"] = aid
                rowd["name"] = found[0].get("name") or rowd["name"]
        if not aid:
            enriched_rows.append(rowd)
            continue

        detail = client.author_detail(aid)
        papers = detail.get("papers", []) if isinstance(detail, dict) else []
        count = 0
        for p0 in papers:
            if count >= max_papers:
                break
            p = normalize_paper(p0)
            if int(p.get("year") or 0) < min_year:
                continue
            if cache.upsert_paper(p, source="semantic_author"):
                outputs.append(paper_to_output(p, "semantic_author", str(rowd.get("topic", "")), "B"))
            count += 1
        enriched_rows.append(rowd)

    pd.DataFrame(enriched_rows).to_csv(AUTHORS_PATH, index=False, encoding="utf-8-sig", quoting=csv.QUOTE_MINIMAL)
    return outputs


def command_recommend(client: S2Client, cache: SemanticCache, config: Dict[str, Any]) -> List[Dict[str, Any]]:
    max_n = int(config.get("recommendation", {}).get("max_recommendations_per_seed", 20))
    seeds = seed_rows_for_tracking()
    outputs: List[Dict[str, Any]] = []
    for _, row in seeds.iterrows():
        pid = str(row.get("s2_paper_id", "")).strip()
        if not pid:
            continue
        for item in client.recommend_for_paper(pid, max_n):
            p = normalize_paper(item)
            if cache.upsert_paper(p, source="semantic_recommendation"):
                outputs.append(paper_to_output(p, "semantic_recommendation", str(row.get("topic", "")), str(row.get("priority", ""))))
    return outputs


def persist_results(results: List[Dict[str, Any]], weekly_csv_path: Path, run_id: str) -> None:
    weekly_columns = INBOX_COLUMNS + ["grade", "run_id"]
    if not results:
        write_rows(weekly_csv_path, [], weekly_columns)
        return
    deduped = unique_records(results)

    weekly_rows = [{**r, "run_id": run_id} for r in deduped]
    write_rows(weekly_csv_path, weekly_rows, weekly_columns)

    inbox_rows = [dict(r) for r in deduped if r.get("grade") in {"A", "B"}]
    for r in inbox_rows:
        r.pop("grade", None)
    append_rows(INBOX_PATH, inbox_rows, INBOX_COLUMNS)


def markdown_table(rows: List[Dict[str, Any]], cols: List[Tuple[str, str]]) -> str:
    if not rows:
        return ""
    header = "| " + " | ".join(c[0] for c in cols) + " |"
    sep = "|" + "|".join(["---:" if i == 0 or i == 1 else "---" for i, _ in enumerate(cols)]) + "|"
    lines = [header, sep]
    for r in rows:
        vals = [clean_text(r.get(key, "")).replace("\n", " ").replace("|", "\\|") for _, key in cols]
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def generate_weekly_md(weekly_csv_path: Path, weekly_md_path: Path, run_id: str) -> None:
    df = read_csv_safe(weekly_csv_path, INBOX_COLUMNS + ["grade", "run_id"])
    if df.empty:
        weekly_md_path.write_text(
            f"# Semantic Scholar Weekly Report\n\nRun: {run_id}\n\n## Summary\n- New search results: 0\n- New citing papers: 0\n- New reference papers: 0\n- New recommended papers: 0\n- New author papers: 0\n",
            encoding="utf-8",
        )
        return

    counts = {
        "semantic_search": len(df[df["source"] == "semantic_search"]),
        "semantic_citation": len(df[df["source"] == "semantic_citation"]),
        "semantic_reference": len(df[df["source"] == "semantic_reference"]),
        "semantic_recommendation": len(df[df["source"] == "semantic_recommendation"]),
        "semantic_author": len(df[df["source"] == "semantic_author"]),
    }

    a_rows = df[df["grade"] == "A"].sort_values(by="score", ascending=False).to_dict("records")
    b_rows = df[df["grade"] == "B"].sort_values(by="score", ascending=False).to_dict("records")
    citation_rows = df[df["source"] == "semantic_citation"].to_dict("records")
    rec_rows = df[df["source"] == "semantic_recommendation"].to_dict("records")
    author_rows = df[df["source"] == "semantic_author"].to_dict("records")

    text = [
        "# Semantic Scholar Weekly Report",
        "",
        f"Run: {run_id}",
        "",
        "## Summary",
        f"- New search results: {counts['semantic_search']}",
        f"- New citing papers: {counts['semantic_citation']}",
        f"- New reference papers: {counts['semantic_reference']}",
        f"- New recommended papers: {counts['semantic_recommendation']}",
        f"- New author papers: {counts['semantic_author']}",
        "",
        "## A-level Papers",
        markdown_table(a_rows, [("Score", "score"), ("Year", "year"), ("Title", "title"), ("Venue", "venue"), ("Reason", "reason")])
        or "| Score | Year | Title | Venue | Reason |\n|---:|---:|---|---|---|",
        "",
        "## B-level Papers",
        markdown_table(b_rows, [("Score", "score"), ("Year", "year"), ("Title", "title"), ("Venue", "venue"), ("Reason", "reason")])
        or "| Score | Year | Title | Venue | Reason |\n|---:|---:|---|---|---|",
        "",
        "## New Citations of Seed Papers",
        markdown_table(citation_rows, [("Year", "year"), ("Title", "title"), ("Venue", "venue"), ("Why relevant", "reason")])
        or "| Year | Title | Venue | Why relevant |\n|---:|---|---|---|",
        "",
        "## Recommended Papers",
        markdown_table(rec_rows, [("Score", "score"), ("Title", "title"), ("Reason", "reason")])
        or "| Score | Title | Reason |\n|---:|---|---|",
        "",
        "## Author Updates",
        markdown_table(author_rows, [("Author", "authors"), ("Year", "year"), ("Title", "title"), ("Venue", "venue")])
        or "| Author | Year | Title | Venue |\n|---|---:|---|---|",
        "",
        "## Next Actions",
        "- Download PDFs:",
        "- Send to Marker:",
        "- Add to Connected Papers:",
    ]
    weekly_md_path.write_text("\n".join(text), encoding="utf-8")


def init_layout() -> None:
    S2_DIR.mkdir(parents=True, exist_ok=True)
    DISCOVERY_DIR.mkdir(parents=True, exist_ok=True)
    ensure_csv(INBOX_PATH, INBOX_COLUMNS)
    ensure_csv(SEEDS_PATH, ["title", "doi", "arxiv_id", "s2_paper_id", "topic", "priority", "note"])
    ensure_csv(AUTHORS_PATH, ["name", "s2_author_id", "affiliation", "topic", "note"])
    if not QUERIES_PATH.exists():
        QUERIES_PATH.write_text("", encoding="utf-8")


def main() -> int:
    configure_stdio_encoding()
    setup_logging()
    init_layout()
    config = load_yaml(CONFIG_PATH)

    parser = argparse.ArgumentParser(description="Semantic Scholar discovery workflow")
    sub = parser.add_subparsers(dest="command", required=True)
    for cmd in ["search", "enrich-seeds", "citations", "references", "authors", "recommend", "weekly"]:
        sub.add_parser(cmd)

    args = parser.parse_args()

    try:
        client = S2Client(config)
    except RuntimeError as exc:
        logging.error(str(exc))
        return 2

    cache = SemanticCache(CACHE_PATH)
    all_results: List[Dict[str, Any]] = []
    run_id = run_timestamp()
    weekly_csv_path, weekly_md_path = weekly_paths(run_id)

    if args.command == "search":
        all_results.extend(command_search(client, cache, config))
    elif args.command == "enrich-seeds":
        command_enrich_seeds(client)
    elif args.command == "citations":
        all_results.extend(command_citations(client, cache, config))
    elif args.command == "references":
        all_results.extend(command_references(client, cache, config))
    elif args.command == "authors":
        all_results.extend(command_authors(client, cache, config))
    elif args.command == "recommend":
        all_results.extend(command_recommend(client, cache, config))
    elif args.command == "weekly":
        command_enrich_seeds(client)
        all_results.extend(command_search(client, cache, config))
        all_results.extend(command_citations(client, cache, config))
        all_results.extend(command_references(client, cache, config))
        all_results.extend(command_authors(client, cache, config))
        all_results.extend(command_recommend(client, cache, config))

    persist_results(all_results, weekly_csv_path, run_id)
    if args.command != "enrich-seeds":
        generate_weekly_md(weekly_csv_path, weekly_md_path, run_id)

    logging.info("Done. command=%s results=%d weekly_csv=%s", args.command, len(all_results), weekly_csv_path)
    cache.close()
    return 0


if __name__ == "__main__":
    try:
        code = main()
    except Exception:
        traceback.print_exc()
        pause_before_exit()
        sys.exit(1)

    pause_before_exit()
    sys.exit(code)
