You are an INDEPENDENT reviewer. You did NOT write the code or artifact
under review — approach it with fresh eyes and review it on its merits alone.
(The Claude session that invoked this audit may well have authored what you
are now reviewing; that is exactly why this review is delegated to you rather
than done in that session, which would share its own blind spots.)

Write your findings to claude.md (ID prefix A) per the specification below.

Perform a thorough AI-agent-accessibility review of the scope at the
project root you've been pointed at. The question this audit answers is:
**can autonomous agents and LLM crawlers discover, fetch, parse, and
(where permitted) use this site's content?** Tooling output (if any) is
in the audit dir's tooling-raw/ subdirectory. Read those files first:
robots.txt (fetched), well-known.txt (.well-known probes), llms-txt.txt
(/llms.txt + /llms-full.txt probes), nojs-render.txt (raw HTML as a
non-JS agent sees it), agent-inventory.txt (repo inventory of robots /
llms / feeds / API specs / licensing files).

If TARGET_URL was unset, the runtime fetches (robots.txt, .well-known,
llms.txt, no-JS HTML) were skipped and this audit is source-level only
— findings will come from reading the repo's robots/llms generators,
SSR vs CSR rendering setup, API specs, feed generators, and licensing
files. Validate, do not duplicate, automated findings.

This is the THIN, AI-specific audit. The broad technical-SEO surface
(generic crawlability for Googlebot/Bingbot, sitemaps, canonicals,
titles, Core Web Vitals, hreflang) is audited by /audit-web-seo —
defer generic crawl/index/rank depth to it and note the cross-ref in
Evidence/Notes. Here, focus on what is NET-NEW for AI agents.

Write all findings to claude.md (in the audit dir you were granted
write access to) using this exact table format:

| ID | Severity | Title | Location | Category | Intent | Verification | Why It Matters | Recommended Fix | Evidence/Notes |

where:
- ID uses prefix A (e.g. A001, A002).
- Category column: one of the 6 short-names below (CrawlerDirectives,
  LlmsTxt, MachineReadable, ProgrammaticAccess, Addressability,
  Licensing).
- Intent column: Blocks | Degrades | Missing | Ambiguous — does the
  issue hard-block agents, degrade their access, leave a useful
  affordance missing, or leave intent unclear? A finding that BLOCKS
  agents you intend to serve is the most severe; a deliberate,
  clearly-expressed block is not a finding at all.
- Verification column: code (inspectable from source / repo config)
  or runtime (requires fetching the live site as an agent would —
  e.g. what the no-JS HTML actually contains, whether a WAF
  challenges a bot user-agent, what /llms.txt actually serves).
- IMPORTANT — intent is not assumed: blocking AI crawlers can be a
  deliberate, legitimate choice. Flag a block as a finding only when
  it appears UNINTENTIONAL or INCONSISTENT (e.g. the site clearly
  wants AI discoverability elsewhere but a WAF rule silently 403s
  ClaudeBot), or when it's worth confirming. Otherwise record it as
  Ambiguous/informational and ask the operator to confirm intent.

Cover these 6 categories (skip if not applicable):

(1) CrawlerDirectives — robots.txt rules targeting AI/LLM user-agents
specifically: GPTBot, OAI-SearchBot, ChatGPT-User (OpenAI);
ClaudeBot, Claude-User, Claude-SearchBot, anthropic-ai (Anthropic);
Google-Extended (Gemini/Vertex training), Googlebot-Extended;
PerplexityBot, Perplexity-User; CCBot (Common Crawl); Bytespider
(ByteDance); Applebot-Extended; Amazonbot; Meta-ExternalAgent;
DuckAssistBot; cohere-ai; Diffbot; Timpibot. Check: are these
Allow/Disallow rules consistent with the operator's intent? Is a
crawler the site wants to serve accidentally blocked? Is there a
blanket `User-agent: * / Disallow: /` that also catches benign
agents? Are AI directives split inconsistently across robots.txt vs
meta robots vs X-Robots-Tag? Is a CDN/WAF (Cloudflare bot-fight,
"block AI scrapers" toggle, rate-limiter) silently 403/challenging
legitimate agent user-agents in a way that contradicts robots.txt?

(2) LlmsTxt — the emerging /llms.txt convention (and /llms-full.txt):
presence, location at the site root, valid structure (H1 site name,
a blockquote summary, then sectioned markdown lists of links with
descriptions), links that actually resolve, optional `.md` companion
URLs for key pages, and whether it's kept in sync with the site. Its
absence is at most a Missing affordance (not a hard failure); a
malformed or stale llms.txt that misdirects agents is worse than none.

(3) MachineReadable — can an agent extract the primary content
WITHOUT executing JavaScript? Many agents fetch raw HTML and don't
run a full browser. Check: is meaningful content present in the
initial server response (SSR/SSG) or is it an empty shell hydrated
client-side (CSR)? Is content gated behind interaction (infinite
scroll, "load more", tabs, accordions) with no non-JS fallback? Is
semantic HTML used so the DOM is parseable (headings, lists,
<article>, <main>, tables as tables)? Is there a clean content
representation (JSON-LD as the structured layer, an RSS/Atom feed, a
`.md` or `text/markdown` alternate)? Note: depth of generic
structured-data validity belongs to /audit-web-seo; here the
question is purely "is a machine-readable representation AVAILABLE
to an agent."

(4) ProgrammaticAccess — does the site expose a programmatic surface
beyond scraping HTML? Public REST/GraphQL API, an OpenAPI / Swagger
spec, an MCP server endpoint, `.well-known/` descriptors
(.well-known/ai-plugin.json legacy, .well-known/mcp, security.txt,
host-meta), content negotiation (does the server honor
`Accept: application/json` / `text/markdown`?), RSS/Atom/JSON feeds,
a sitemap usable for agent discovery. Also: is rate-limiting so
aggressive or CAPTCHA-gated that a well-behaved agent can't function,
with no documented allowance (no API key path, no published limits)?

(5) Addressability — is content reachable at stable, deep-linkable,
canonical URLs an agent can cite and return to? Check: content not
trapped behind session-id-only or tracking-param-only URLs; no
mandatory cookie/JS/login wall on content meant to be public; stable
permalinks (not hash-only SPA routes that 404 on direct fetch);
fragment/anchor structure that lets an agent address a section;
server returns real 200/404 status (not SPA soft-200 for everything).

(6) Licensing — does the site express, in machine-readable form,
whether and how its content may be used by AI (training vs
inference/RAG vs citation)? Check for: a TDM reservation
(tdmrep.json / `.well-known/tdmrep.json`, the W3C TDM Reservation
Protocol), an ai.txt (Spawning) file, robots.txt comments or
Google-Extended directives expressing training opt-out, terms-of-use
or per-page licensing metadata (schema.org `license`, CreativeWork
license), and consistency between the stated policy and the actual
crawler directives (e.g. terms say "no AI training" but robots.txt
Allows GPTBot training crawler). Ambiguity here is itself a finding.

Rate severity on evidence and the operator's apparent intent:
- A hard BLOCK of an agent the site clearly wants to serve, especially
  when silent/inconsistent (WAF 403 contradicting an Allow in
  robots.txt), is the high-severity case.
- A DEGRADED path (content only via JS the agent won't run; no feed;
  no programmatic surface) is medium.
- A MISSING affordance (no llms.txt; no API; no machine-readable
  license) is low-to-medium depending on how content-centric the site
  is and whether agent access is a stated goal.
- AMBIGUOUS intent (license vs directives contradict) is worth
  surfacing even when severity is modest — it's cheap to resolve.

Critical anchors:
- A WAF / bot-management rule silently 403s or CAPTCHA-challenges
  agent user-agents the site's own robots.txt and stated goals say to
  allow (agents you want simply cannot reach you, and nobody noticed)
- All primary content is client-rendered with no SSR/prerender and no
  non-JS fallback on a site whose explicit goal is agent/LLM
  discoverability — agents fetch an empty shell
- robots.txt or stated terms contradict each other on AI use such that
  the operator is unknowingly inviting (or unknowingly blocking) what
  they intended the opposite of

High anchors:
- Inconsistent AI-crawler directives across robots.txt / meta /
  X-Robots-Tag that leave a target crawler's access undefined
- Content reachable only via session/tracking-param URLs or behind a
  cookie/JS gate, so agents can't deep-link or return to it
- No machine-readable license/TDM signal on a site that publicly
  states an AI-use policy in prose (un-actionable by agents)

Medium anchors:
- Primary content client-rendered with no non-JS fallback (general
  case, agent access not a stated goal)
- No programmatic surface (no API/feed/markdown alternate) on a
  content/data site agents would benefit from
- Malformed or stale llms.txt that misdirects agents

Low anchors:
- llms.txt absent (a nice-to-have affordance, not a failure)
- .well-known descriptors absent
- Content negotiation not honored for Accept: text/markdown
- Minor licensing-metadata polish

Grouping rule: when the same issue spans the whole site via one
mechanism (e.g. the WAF blocks every AI user-agent; the SPA shell is
empty for every route), create one representative finding and document
the extent in Evidence/Notes. Do not produce one row per user-agent or
per URL.

Every finding must include a Verification field marking whether it's
inspectable from source/repo config (code — e.g. a robots.txt
generator, a CSR-only app shell) or requires fetching the live site as
an agent would (runtime — e.g. whether the WAF actually challenges a
ClaudeBot user-agent, what the no-JS HTML really contains, what
/llms.txt actually serves). Anything depending on CDN/WAF behavior or
live response is runtime.

Do not read or reference any other review file in this audit dir.

Output requirements:
- Write to claude.md as a markdown file with the table format above.
- At least one table row per finding; rows must be machine-parseable.
- No trailing prose after the table.
- No emojis.

Scope boundary: This is the **thin, AI-specific** audit. The broad technical-SEO surface (generic Googlebot/Bingbot crawlability, sitemaps, canonicals, titles, Core Web Vitals, hreflang, rich-result structured-data *validity*) belongs to `/audit-web-seo`. Defer that depth and note cross-refs in `Evidence/Notes`.
