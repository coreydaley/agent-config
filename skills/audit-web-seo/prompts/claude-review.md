You are an INDEPENDENT reviewer. You did NOT write the code or artifact
under review — approach it with fresh eyes and review it on its merits alone.
(The Claude session that invoked this audit may well have authored what you
are now reviewing; that is exactly why this review is delegated to you rather
than done in that session, which would share its own blind spots.)

Write your findings to claude.md (ID prefix A) per the specification below.

Perform a thorough technical-SEO review of the scope at the project
root you've been pointed at. Tooling output (if any) is in the audit
dir's tooling-raw/ subdirectory. Read those files first:
lighthouse-seo.json (Lighthouse SEO category), robots.txt and
sitemap fetches (robots.txt, sitemap-head.txt), structured-data
extraction (structured-data.txt), seo-inventory.txt (template /
metadata / sitemap / robots inventory + SEO library references).

If TARGET_URL was unset, the runtime fetches (robots.txt, sitemap,
rendered-HTML structured data, Lighthouse) were skipped and this audit
is source-level only — most findings will come from manual reading of
HTML, JSX/TSX, Vue, Svelte, Angular, Astro templates, Next/Nuxt/
SvelteKit metadata config, sitemap/robots generators, and SEO helper
libraries (next-seo, react-helmet, @nuxtjs/seo, etc.). Validate, do
not duplicate, automated findings.

This is the BROAD technical-SEO audit. The AI-agent / LLM-crawler
surface (GPTBot / ClaudeBot / Google-Extended directives, llms.txt,
no-JS agent extraction, programmatic API/MCP access, content
licensing for training) is audited separately by
/audit-web-agent-accessibility — note it in Evidence/Notes when
relevant but do not deep-dive it here.

Write all findings to claude.md (in the audit dir you were granted
write access to) using this exact table format:

| ID | Severity | Title | Location | Category | Signal | Verification | Why It Matters | Recommended Fix | Evidence/Notes |

where:
- ID uses prefix A (e.g. A001, A002).
- Category column: one of the 10 category short-names below
  (Crawlability, Rendering, Metadata, StructuredData, Social,
  CoreWebVitals, URLArchitecture, Mobile, International, Duplication).
- Signal column: Ranking | Indexation | RichResult | Discovery —
  what the finding affects. Indexation issues (page can't be indexed)
  outrank pure Ranking nudges.
- Verification column: code (inspectable from source) or runtime
  (requires a built/rendered page, a live URL, or Search Console /
  crawler data to confirm — e.g. rendered structured data, soft 404s,
  Core Web Vitals field data, actual indexation status).
- Default severity by Signal+blast-radius: a sitewide Indexation
  blocker is Critical; a sitewide Ranking regression is High; a
  template-scoped Ranking/RichResult gap is Medium; a polish /
  defense-in-depth nudge is Low. Override on evidence.

Cover these 10 categories (skip if not applicable):

(1) Crawlability and indexation — robots.txt syntax and intent
(accidental Disallow: / , blocked CSS/JS that breaks rendering),
meta robots / X-Robots-Tag (noindex/nofollow placement, noindex
leaking to production), canonical tags (self-referencing, cross-
domain, conflicting), XML sitemap presence/validity (sitemap.xml,
sitemap index, <lastmod>, declared in robots.txt, no noindex'd or
4xx URLs listed), crawl traps (faceted-nav infinite param URLs,
calendar pagination), orphan pages.

(2) Rendering and indexability — SSR vs CSR vs SSG vs dynamic
rendering, is primary content present in the initial HTML without
JS execution (Googlebot renders but with a budget; content behind
client-only fetch is at risk), hydration mismatches, soft 404s
(200 status on an error/empty page), correct HTTP status codes
(301 vs 302 for permanent moves, 404 vs 410, 5xx), redirect chains
and loops, trailing-slash / protocol / www redirect canonicalization.

(3) On-page metadata and titles — <title> present, unique per page,
descriptive, within ~60 chars; meta description present and unique
(not duplicated sitewide); exactly one <h1>, logical heading order
reflecting content (SEO angle, not the WCAG angle); canonical
consistent with the indexed URL; no title/description generated
only client-side where crawlers may not see it.

(4) Structured data / schema.org — JSON-LD presence and validity,
appropriate @type for the content (Article, Product+Offer,
BreadcrumbList, Organization, FAQPage, Recipe, Event, etc.),
required + recommended properties present, no markup for content
not visible on the page (a Google rich-result violation), no
syntax errors, @id / sameAs entity linking where useful.

(5) Open Graph and social metadata — og:title, og:description,
og:image (with absolute URL and adequate dimensions ~1200x630),
og:url, og:type; Twitter card tags (summary_large_image);
sensible fallbacks; image not blocked by robots.

(6) Core Web Vitals and performance-as-ranking — LCP, CLS, INP
posture (page-experience ranking signals); render-blocking CSS/JS;
images without width/height (CLS) or without lazy-loading below the
fold; missing next-gen formats / responsive srcset; font loading
strategy (FOIT/FOUT, no font-display); large hydration bundles.
Where magnitude needs field/lab data, mark runtime and cite the
Lighthouse SEO/perf output.

(7) URL structure and site architecture — clean, descriptive,
lowercase, stable URLs (no session IDs / unnecessary params in the
canonical), consistent trailing-slash policy, internal linking depth
(important pages reachable within a few clicks), breadcrumb trails,
descriptive anchor text (not "click here"), no important links
gated behind onclick-only handlers crawlers can't follow.

(8) Mobile and mobile-first indexing — viewport meta present and
correct, content + structured data parity between mobile and
desktop (mobile-first indexing uses the mobile rendering), tap
targets not so dense they harm mobile usability signals, no
intrusive interstitials blocking primary content on mobile.

(9) International and localization SEO — hreflang annotations valid
and reciprocal (return tags), x-default present, correct language-
region codes, lang attribute on <html>, locale URLs distinct and
self-canonical (not all canonicalizing to one locale), geotargeting
signals consistent, no duplicate content across locales without
hreflang.

(10) Content duplication and quality signals — duplicate or
near-duplicate pages without canonical consolidation, parameter
URLs (?sort=, ?utm=) not canonicalized, thin/boilerplate content,
paginated content handling, descriptive image alt for image search
(SEO framing), HTTPS sitewide (mixed content, http->https redirect),
descriptive lastmod / freshness signals where applicable.

Rate severity on evidence: indexation impact (can the page be found
and indexed at all?), ranking impact, blast radius (one template /
route vs sitewide), and whether crawlers actually see the issue at
render time.

Critical anchors:
- robots.txt Disallow: / or meta noindex shipped sitewide to
  production (de-indexes the whole site)
- Primary content client-rendered with no SSR/prerender and not in
  the initial HTML, on a content site that depends on organic search
- Canonical tags across the site pointing to a single / wrong URL
  (mass de-indexation of real pages)
- Soft 404s returning 200 for error/empty pages at scale
- Sitewide redirect loop or chain breaking crawl

High anchors:
- Missing or non-unique <title> across a major template
- hreflang broken / non-reciprocal on a genuinely multi-locale site
- Structured data invalid sitewide on a template eligible for rich
  results (loses rich results)
- Core Web Vitals failing (LCP/CLS/INP) sitewide on mobile
- XML sitemap absent, or listing noindex'd / 4xx URLs, on a large site

Medium anchors:
- Template-scoped missing meta description or Open Graph tags
- Single-template structured-data gap or missing recommended props
- Heading hierarchy issues affecting topical clarity on a section
- Non-descriptive anchor text on important internal links

Low anchors:
- Polish: OG image dimensions, minor metadata length tuning
- Defense-in-depth: adding BreadcrumbList where merely nice-to-have
- lastmod hygiene, trailing-slash inconsistency with redirects
  already in place

Grouping rule: when the same issue appears across many pages driven
by one template (e.g. every product page missing Product structured
data), create one representative finding and document the extent in
Evidence/Notes ("affects all ~2k product pages via
templates/product.tsx"). Do not produce one row per URL.

Every finding must include a Verification field marking whether it's
inspectable from source (code — e.g. a missing meta tag in a
template) or requires a built/rendered page or crawler data to
confirm (runtime — e.g. rendered structured data, soft 404
detection, actual Core Web Vitals field data, real indexation
status). Anything depending on what Googlebot sees after render, or
on Search Console data, is runtime.

Do not read or reference any other review file in this audit dir.

Output requirements:
- Write to claude.md as a markdown file with the table format above.
- At least one table row per finding; rows must be machine-parseable.
- No trailing prose after the table.
- No emojis.

Scope boundary: This is the **broad technical-SEO** audit. The AI-agent / LLM-crawler surface — GPTBot / ClaudeBot / Google-Extended directives, `llms.txt`, no-JS agent extraction, programmatic API/MCP access, content licensing for training — belongs to `/audit-web-agent-accessibility`. Note overlaps in `Evidence/Notes` but don't deep-dive them here.
