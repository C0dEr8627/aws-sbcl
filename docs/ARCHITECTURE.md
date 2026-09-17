# AWS SBCL Builder Scraper — Architecture

**Status:** Planning  
**Deployment:** Local machine only  
**Primary user:** One SBCL operator  
**Primary output:** Builder alias + public full/display name  
**Optional output:** Publicly exposed email only

## 1. Product goal

Replace the current one-by-one manual workflow with a small local scraper that can discover Builder Center profiles and export a clean list for SBCL outreach/sign-up tracking.

The first version should optimize for reliability, inspectability, and easy recovery when Builder Center changes its frontend.

## 2. Proposed architecture

```text
                         AWS Builder Center
                                │
                ┌───────────────┴───────────────┐
                │                               │
        Public discovery/search          Public profile
                │                    /community/@<alias>
                │                               │
                └───────────────┬───────────────┘
                                │
                         Scraper / Adapter
                                │
                     Normalization + validation
                                │
                    ┌───────────┴───────────┐
                    │                       │
                 Local data            Export layer
                 store/cache            CSV / JSON
                    │                       │
                    └───────────┬───────────┘
                                │
                         Local operator UI/CLI
```

## 3. Components

### 3.1 Discovery adapter

Responsible for finding candidate builders from Builder Center's public search/discovery mechanism.

Responsibilities:

- submit search terms / browse result pages;
- handle pagination or cursor-based results;
- extract candidate aliases/profile URLs;
- deduplicate candidates;
- expose raw response diagnostics when parsing fails.

**Important:** the concrete transport (direct HTTP endpoint vs browser automation) is intentionally not fixed until live Network inspection identifies the site's actual current endpoint.

### 3.2 Profile adapter

Given an alias or profile URL, resolve the public profile.

Responsibilities:

- fetch `/community/@<alias>`;
- extract public alias;
- extract public display/full name;
- optionally extract a clearly public email field if one exists;
- validate that the resolved alias matches the requested candidate;
- retain the profile URL.

### 3.3 Normalizer

Converts site-specific payloads/HTML into the stable application model:

```ts
type Builder = {
  alias: string;
  display_name: string;
  profile_url: string;
  email: string | null;
  source: "builder_center_public_profile";
  scraped_at: string;
};
```

### 3.4 Local store

A local SQLite database is the preferred MVP store because it provides:

- deduplication by alias;
- incremental scraping;
- historical timestamps;
- easy filtering/export;
- no external service dependency.

A JSON/CSV export remains the user-facing interchange format.

### 3.5 Exporter

Minimum formats:

- CSV — primary spreadsheet workflow;
- JSON — debugging/integration;

Recommended CSV columns:

`alias,display_name,profile_url,email,scraped_at`

### 3.6 Operator interface

Start with a CLI. A local web UI can be added only if the workflow demonstrates a need for it.

Suggested commands:

```text
scraper search <query>
scraper profile <alias>
scraper scrape --query <query> --limit <n>
scraper export --format csv --output builders.csv
```

## 4. Extraction strategy

Use a layered adapter strategy rather than coupling the entire application to the Builder Center frontend.

```text
BuilderCenterClient
        │
        ├── DiscoveryAdapter
        │       ├── DirectHttpAdapter   (preferred if public endpoint exists)
        │       └── BrowserAdapter      (fallback when required)
        │
        └── ProfileAdapter
                ├── DirectHttpAdapter
                └── BrowserAdapter
```

The direct HTTP route should be preferred when the endpoint is public and stable. Browser automation should be used only where the site's public data cannot be obtained reliably through normal HTTP requests.

## 5. Pagination and deduplication

The scraper must not assume that one search response represents all builders.

The discovery adapter should support:

- page-based pagination;
- cursor/token pagination;
- termination when no new candidates are returned;
- alias-based deduplication;
- configurable maximum records per run.

The alias is the natural stable key because it identifies the public Builder Center profile.

## 6. Error handling

Errors should be classified instead of silently skipped:

| Error | Action |
|---|---|
| HTTP 429 | Back off and retry with jitter |
| HTTP 403 | Stop and report access restriction |
| HTTP 404 profile | Mark profile unavailable |
| HTML/schema changed | Save diagnostic response and report parser mismatch |
| Network timeout | Retry bounded number of times |
| Missing display name | Keep record only in diagnostic output; do not export as valid |
| Missing email | Set `email = null` |

Do not implement aggressive concurrency. The target is a personal local utility, not a high-volume crawler.

## 7. Privacy and data-minimization boundary

The scraper should collect only information needed for the SBCL workflow and explicitly public on Builder Center.

Do **not**:

- bypass authentication;
- access private profile fields;
- derive emails from names/aliases;
- query unrelated AWS identity systems to obtain contact information;
- scrape private account data.

Email is optional and should remain null unless Builder Center itself exposes it as public information.

## 8. Local-only design

No AWS resources are required for the scraper itself.

No planned:

- Lambda;
- API Gateway;
- DynamoDB;
- S3;
- Cognito;
- hosted frontend;
- scheduled cloud jobs.

This keeps the project inexpensive and appropriate for a single-user workflow.

## 9. Security

If browser automation is eventually required, credentials/cookies must stay on the local machine and must never be committed to Git.

Use `.env` only for non-source-controlled local configuration. Add credentials, browser profiles, cookies, SQLite databases, and exports containing personal data to `.gitignore` where appropriate.

## 10. Test architecture

Tests should be separated into:

1. **Fixture tests** — parser tests against saved Builder Center responses.
2. **Normalization tests** — field mapping and validation.
3. **Deduplication tests** — repeated aliases and pagination.
4. **Live smoke test** — optional, explicitly invoked against the live public site.

Fixture tests are especially important because the site frontend/API can change without notice.
