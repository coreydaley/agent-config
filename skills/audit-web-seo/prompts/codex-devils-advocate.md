Read synthesis.md and the raw tooling output in tooling-raw/ in the
audit dir you've been granted access to. Your job is to attack the
synthesis, not improve it.

Write your challenge to devils-advocate.md (in the same audit dir)
using this table format:

| ID | Challenge Type | Target Finding | Claim | Evidence | Confidence |

where:
- ID uses prefix D (D001, D002, ...)
- Challenge Type: false_positive | severity_miscalibrated |
  missing_finding | missing_compound | impractical_remediation |
  insufficient_verification
- Target Finding: the S### ID from synthesis.md being challenged
  (or "N/A" for missing_finding / missing_compound)
- Claim: 1-2 sentence challenge
- Evidence: file:line citation, the rendered-HTML / robots / sitemap
  fetch in tooling-raw/, or a specific config reference; cite the
  affected ranking/indexation signal.
- Confidence: high | medium | low

Cover these challenge categories:

(1) False positives — findings that are actually fine in context.
Specifically for technical SEO:
- A "content is client-rendered, invisible to Google" finding on a
  framework that actually prerenders / SSRs that route (Next.js
  getServerSideProps / generateStaticParams, Nuxt SSR, Astro static)
  — the source looked CSR but the build output is HTML.
- A "noindex shipped to production" finding on a tag that is gated to
  staging / preview environments only (env check, NODE_ENV, robots
  middleware that flips on a preview hostname).
- A "missing canonical" finding where the framework injects a
  self-referencing canonical by default (Next metadata, next-seo
  DefaultSeo) that the reviewer didn't trace.
- A "duplicate title" finding where titles are templated per-route
  and only collide in a sample, not in production data.
- A "robots.txt blocks the site" finding misreading an Allow / a
  path-scoped Disallow as a sitewide block.
- A structured-data "invalid" finding measured against a stricter
  validator than Google actually enforces (recommended != required).

(2) Severity miscalibrations — findings rated too high (a Ranking
nudge dressed up as Critical; an issue on a noindex'd or low-value
route; a param URL already canonicalized) or too low (a template
issue under-counting blast radius across thousands of URLs; an
Indexation blocker filed as Medium when it de-indexes real pages).
Indexation > Ranking when ranking the severity.

(3) Missing findings — technical-SEO issues both reviewers missed:
- robots.txt blocking CSS/JS needed for render (Google renders the
  page; blocked assets degrade what it indexes)
- Pagination / infinite scroll with no crawlable paginated URLs
- Faceted-navigation crawl trap generating infinite param URLs
- Mixed HTTP/HTTPS or non-canonical protocol/host without redirects
- hreflang present but non-reciprocal (return-tag errors)
- Sitemap listing noindex'd, redirected, or 4xx URLs
- og:image / canonical using relative URLs that don't resolve for
  crawlers
- Soft 404 (200 status on an empty/"not found" page)
- Render-blocking that tanks LCP sitewide
- Structured data describing content not visible on the page
  (a rich-result eligibility violation / manual-action risk)
- JS-injected meta tags (title/canonical/robots) that the crawler
  may not execute in time

(4) Missing compound paths — separate findings that combine into a
worse outcome than any single one. Example: client-only rendering +
JS-injected canonical + no SSR = the canonical the crawler sees is
wrong AND the content is empty = the page is both mis-canonicalized
and effectively blank to the index. Be explicit about the chain and
the combined severity.

(5) Impractical / incomplete / wrong remediations — e.g.
recommending "add a sitemap" without addressing that it lists 4xx
URLs; "set a canonical" pointing at a noindex'd URL; "add structured
data" for content not on the page (invites a manual action);
prerendering advice that breaks an authenticated/personalized route;
remediations that fix ranking but introduce an indexation regression.

(6) Verification steps that don't actually prove the fix works —
"check the source" is insufficient for anything render-dependent:
rendered structured data, soft-404 status, actual indexation, and
Core Web Vitals field data require a built/live page, the URL
Inspection / Rich Results tools, or Search Console — not source
reading. A passing Lighthouse lab score doesn't prove field CWV.

Be specific. Every challenge must cite the finding ID and reference
the affected SEO signal where applicable.

Do not read or reference any other review file beyond synthesis.md
and the tooling-raw/ directory.

Output requirements:
- Write to devils-advocate.md as a markdown file with the table above.
- At least one row; rows must be machine-parseable.
- If you find no valid challenges, write one row with type
  "no_challenges" and Confidence "high" stating that you attempted
  but found nothing worth surfacing.
- No emojis.
