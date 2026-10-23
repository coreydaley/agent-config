#!/usr/bin/env python3
"""Fetch current job postings from public job-board APIs.

Reads a config (see ../example-config.json) listing companies and the job
board each one uses, keeps postings whose title matches the role keywords,
cuts each description down to its requirements section, and writes one JSON
object per posting to <out>/postings.jsonl.

Only public, unauthenticated board APIs are used (no scraping):
  greenhouse  https://boards-api.greenhouse.io/v1/boards/<slug>/jobs?content=true
  lever       https://api.lever.co/v0/postings/<slug>?mode=json
  ashby       https://api.ashbyhq.com/posting-api/job-board/<slug>

Usage: fetch_postings.py --config CONFIG --out DIR
Standard library only.
"""

import argparse
import html
import json
import re
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

UA = "job-market-scan (+https://github.com/coreydaley/agent-config)"
REQ_HEADING = re.compile(
    r"(requirements|qualifications|what you.ll (bring|need)|you (have|bring|are)|"
    r"about you|skills|experience|who you are|must.haves|nice to have)",
    re.I,
)
MAX_CHARS = 6000


def get_json(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def to_text(markup: str) -> str:
    markup = html.unescape(markup or "")
    markup = re.sub(r"<(br|/p|/li|/h\d|/div)[^>]*>", "\n", markup, flags=re.I)
    markup = re.sub(r"<li[^>]*>", "\n- ", markup, flags=re.I)
    text = html.unescape(re.sub(r"<[^>]+>", " ", markup)).replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r"\n\s*\n+", "\n", text).strip()


def requirements_part(text: str) -> str:
    """The requirements section if one can be found, else the whole text (capped)."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if len(line) < 80 and REQ_HEADING.search(line):
            return "\n".join(lines[i:])[:MAX_CHARS]
    return text[:MAX_CHARS]


def fetch(company: dict) -> list[dict]:
    board, slug, name = company["board"], company["slug"], company.get("name", company["slug"])
    out = []
    if board == "greenhouse":
        for j in get_json(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true")["jobs"]:
            out.append({"title": j["title"], "url": j["absolute_url"],
                        "location": (j.get("location") or {}).get("name", ""),
                        "text": to_text(j.get("content", ""))})
    elif board == "lever":
        for j in get_json(f"https://api.lever.co/v0/postings/{slug}?mode=json"):
            parts = [j.get("descriptionPlain", "")]
            for lst in j.get("lists", []):
                parts.append(lst.get("text", "") + "\n" + to_text(lst.get("content", "")))
            out.append({"title": j["text"], "url": j["hostedUrl"],
                        "location": (j.get("categories") or {}).get("location", ""),
                        "text": "\n".join(parts)})
    elif board == "ashby":
        for j in get_json(f"https://api.ashbyhq.com/posting-api/job-board/{slug}")["jobs"]:
            if j.get("isListed") is False:
                continue
            out.append({"title": j["title"], "url": j["jobUrl"], "location": j.get("location", ""),
                        "text": j.get("descriptionPlain") or to_text(j.get("descriptionHtml", ""))})
    else:
        raise ValueError(f"{name}: unknown board {board!r} (use greenhouse, lever or ashby)")
    for p in out:
        p["company"] = name
    return out


def matches(title: str, location: str, cfg: dict) -> bool:
    t = title.lower()
    if not any(k.lower() in t for k in cfg.get("title_keywords", [])):
        return False
    if any(k.lower() in t for k in cfg.get("exclude_title_keywords", [])):
        return False
    locs = cfg.get("location_keywords", [])
    return not locs or any(k.lower() in (location or "").lower() for k in locs)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    cfg = json.loads(args.config.read_text())
    per_company = cfg.get("max_per_company", 4)
    args.out.mkdir(parents=True, exist_ok=True)
    def fetch_one(company):
        try:
            return company, fetch(company), None
        except Exception as exc:  # one bad board shouldn't stop the run
            return company, [], exc

    kept, failed = [], []
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(fetch_one, cfg["companies"]))
    for company, fetched, exc in results:
        if exc:
            failed.append(f"{company.get('name', company['slug'])}: {exc}")
            continue
        postings, seen = [], set()
        for p in fetched:  # one role posted in several locations counts once
            if matches(p["title"], p["location"], cfg) and p["title"].lower() not in seen:
                seen.add(p["title"].lower())
                postings.append(p)
        for p in postings[:per_company]:
            p["requirements"] = requirements_part(p.pop("text"))
            kept.append(p)
        print(f"{company.get('name', company['slug'])}: {len(postings)} matching, kept {min(len(postings), per_company)}",
              file=sys.stderr)

    with (args.out / "postings.jsonl").open("w") as f:
        for p in kept:
            f.write(json.dumps(p) + "\n")
    print(f"{len(kept)} postings written to {args.out / 'postings.jsonl'}", file=sys.stderr)
    for line in failed:
        print(f"FAILED {line}", file=sys.stderr)
    return 0 if kept else 1


if __name__ == "__main__":
    sys.exit(main())
