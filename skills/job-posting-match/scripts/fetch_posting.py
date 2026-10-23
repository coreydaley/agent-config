#!/usr/bin/env python3
"""Fetch one job posting from a public job-board API and print it as JSON.

Supported URLs:
  job-boards.greenhouse.io/<slug>/jobs/<id>, boards.greenhouse.io/<slug>/jobs/<id>
  any company careers URL with ?gh_jid=<id>   (needs --greenhouse-slug)
  jobs.lever.co/<slug>/<id>
  jobs.ashbyhq.com/<slug>/<id>

Prints {"company","title","url","location","workplace","pay","text"}. Exits 2
for an unsupported URL so the caller can fall back to reading the page.

Usage: fetch_posting.py URL [--greenhouse-slug SLUG]
Standard library only.
"""

import argparse
import html
import json
import re
import sys
import urllib.request
from urllib.parse import parse_qs, urlparse

UA = "job-posting-match (+https://github.com/coreydaley/agent-config)"


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


PAY_LINE = re.compile(r"(pay|salary|compensation|base)", re.I)
MONEY_RANGE = re.compile(r"\$\s?([\d,]+(?:\.\d+)?)\s?([kK])?\s*(?:-|–|—|to)\s*\$\s?([\d,]+(?:\.\d+)?)\s?([kK])?")


def pay_from_text(text: str) -> list[str]:
    """Pay ranges written into the posting text, e.g. "base pay range ... $195,000 - $255,000"."""
    found = []
    lines = text.splitlines()
    for i, line in enumerate(lines):
        context = " ".join(lines[max(0, i - 1):i + 1])
        if PAY_LINE.search(context):
            for m in MONEY_RANGE.finditer(line):
                found.append(f"{m.group(0).strip()} ({line.strip()[:120]})")
    return found


def workplace_from(location: str, text: str, given: str) -> str:
    if given:
        return given
    blob = f"{location} {text}".lower()
    if "remote" in (location or "").lower() or "#li-remote" in blob:
        return "remote"
    if "#li-hybrid" in blob:
        return "hybrid"
    if "#li-onsite" in blob:
        return "on-site"
    return ""


def parse(url: str, greenhouse_slug: str | None = None) -> tuple[str, str, str] | None:
    """Return (board, slug, job_id) for a supported URL, else None."""
    u = urlparse(url)
    parts = [p for p in u.path.split("/") if p]
    host = u.netloc.lower()
    if host.endswith("greenhouse.io") and len(parts) >= 3 and parts[1] == "jobs":
        return "greenhouse", parts[0], parts[2]
    gh_jid = parse_qs(u.query).get("gh_jid")
    if gh_jid and greenhouse_slug:
        return "greenhouse", greenhouse_slug, gh_jid[0]
    if host == "jobs.lever.co" and len(parts) >= 2:
        return "lever", parts[0], parts[1]
    if host == "jobs.ashbyhq.com" and len(parts) >= 2:
        return "ashby", parts[0], parts[1]
    return None


def fetch(board: str, slug: str, job_id: str) -> dict:
    if board == "greenhouse":
        j = get_json(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs/{job_id}?pay_transparency=true")
        pay = [f"{r['currency_type']} {r['min_cents'] // 100:,}–{r['max_cents'] // 100:,} ({to_text(r.get('title', ''))})"
               for r in j.get("pay_input_ranges") or []]
        return {"company": j.get("company_name", slug), "title": j["title"], "url": j["absolute_url"],
                "location": (j.get("location") or {}).get("name", ""), "workplace": "",
                "pay": pay, "text": to_text(j.get("content", ""))}
    if board == "lever":
        j = get_json(f"https://api.lever.co/v0/postings/{slug}/{job_id}")
        parts = [j.get("descriptionPlain", "")]
        for lst in j.get("lists", []):
            parts.append(lst.get("text", "") + "\n" + to_text(lst.get("content", "")))
        parts.append(j.get("additionalPlain", ""))
        rng = j.get("salaryRange") or {}
        pay = [f"{rng.get('currency', '')} {rng.get('min', 0):,}–{rng.get('max', 0):,} {rng.get('interval', '')}".strip()] if rng else []
        return {"company": slug, "title": j["text"], "url": j["hostedUrl"],
                "location": (j.get("categories") or {}).get("location", ""),
                "workplace": j.get("workplaceType", ""), "pay": pay, "text": "\n".join(parts)}
    if board == "ashby":
        jobs = get_json(f"https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true")["jobs"]
        j = next((x for x in jobs if x["id"] == job_id), None)
        if j is None:
            raise LookupError(f"posting {job_id} isn't on {slug}'s board (closed or unlisted?)")
        comp = (j.get("compensation") or {}).get("compensationTierSummary")
        return {"company": slug, "title": j["title"], "url": j["jobUrl"], "location": j.get("location", ""),
                "workplace": j.get("workplaceType", ""), "pay": [comp] if comp else [],
                "text": j.get("descriptionPlain") or to_text(j.get("descriptionHtml", ""))}
    raise ValueError(board)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("url")
    ap.add_argument("--greenhouse-slug", help="board slug for a company careers URL with ?gh_jid=")
    args = ap.parse_args()
    target = parse(args.url, args.greenhouse_slug)
    if not target:
        print("unsupported URL: read the page instead", file=sys.stderr)
        return 2
    posting = fetch(*target)
    if not posting["pay"]:
        posting["pay"] = pay_from_text(posting["text"])
    posting["workplace"] = workplace_from(posting["location"], posting["text"], posting["workplace"])
    print(json.dumps(posting, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
