# AWS SBCL Builder Scraper — Development Plan

## MVP acceptance rule

A builder is a target only when all three public-profile conditions are true:

```python
location.strip().casefold().endswith("india")
and followers == 0
and following == 0
```

The scraper must use the public Builder Center profile location for the India check. It must not infer nationality from a name or alias. Email is optional and may be collected only when explicitly public on the profile.

## Phase 0 — Site reconnaissance

**Goal:** identify the real data transport before writing the discovery scraper.

1. Inspect Builder Center public search in a desktop browser.
2. Capture Network requests while searching builders.
3. Capture Network requests while opening a profile.
4. Identify response payloads containing candidate aliases/profile URLs.
5. Determine pagination/cursors and any rate limits.
6. Verify whether the request is unauthenticated.
7. Save representative sanitized response fixtures under `tests/fixtures/`.

**Exit criterion:** we can point to the exact public request/response that supplies candidate profiles. Do not invent or hard-code an unverified internal API endpoint.

## Phase 1 — Project foundation

- Python 3.11+ project.
- Dependency management.
- `.gitignore` rules for local databases, exports, browser profiles, cookies, and secrets.
- Test runner.
- Initial target-filter tests.

## Phase 2 — Builder Center client

Implement a narrow client around the verified site transport:

```text
BuilderCenterClient
  ├── search(query, pagination)
  └── get_profile(alias)
```

Keep transport details inside this module so the rest of the application does not depend on Builder Center's internal schema.

A public profile adapter is already in place for `/community/@<alias>`. Discovery/search remains dependent on Phase 0 reconnaissance.

## Phase 3 — Parsing and normalization

Implement:

- search response parser;
- public profile parser;
- alias normalization (`@foo` → `foo` internally);
- display-name normalization;
- public location extraction;
- follower/following extraction;
- profile URL construction/validation;
- nullable public email handling;
- target-filter validation.

Every parser should have fixture tests.

## Phase 4 — Local persistence

Add SQLite with a small schema:

```sql
CREATE TABLE builders (
  alias TEXT PRIMARY KEY,
  display_name TEXT NOT NULL,
  location TEXT NOT NULL,
  followers INTEGER NOT NULL,
  following INTEGER NOT NULL,
  profile_url TEXT NOT NULL,
  email TEXT,
  first_seen_at TEXT NOT NULL,
  last_seen_at TEXT NOT NULL
);
```

Use upsert semantics so repeated searches do not create duplicates.

## Phase 5 — Scrape workflow

Implement the end-to-end flow:

```text
query
  ↓
discovery
  ↓
unique aliases
  ↓
profile resolution
  ↓
India + 0 followers + 0 following filter
  ↓
SQLite upsert
  ↓
summary
```

The run summary should report:

- candidates discovered;
- profiles resolved;
- target builders;
- filtered-out profiles;
- new builders;
- updated builders;
- errors;
- duration.

## Phase 6 — Export

Implement CSV and JSON export from the local database.

CSV is the primary output for the SBCL workflow.

Support filters such as:

- only target builders;
- newly discovered since date;
- query/run;
- limit;
- only records with non-empty names.

## Phase 7 — CLI / local UX

Provide a simple workflow suitable for weekly use:

```text
1. Run search/scrape
2. Review target count
3. Export CSV
4. Use CSV for SBCL tracking
```

Keep the interface intentionally small. Do not build a hosted dashboard unless the local CLI proves insufficient.

## Phase 8 — Reliability hardening

- bounded retries;
- exponential backoff;
- 429 handling;
- request timeout;
- schema-change diagnostics;
- fixture regression suite;
- clear error messages;
- conservative request rate.

## Phase 9 — Validation

Before considering the MVP complete:

- verify alias/name/location/counts against manually opened public profiles;
- test duplicate search results;
- test multiple pages/cursors;
- test unavailable profiles;
- test missing optional email;
- test target filtering;
- test export correctness;
- run a small live scrape before larger weekly runs.

## Phase 10 — Future enhancements

Only after the MVP is stable:

- interactive local UI;
- saved searches;
- incremental weekly run history;
- contact/status columns maintained by the operator;
- import of existing SBCL tracking CSV;
- browser-assisted profile review.

These are deliberately outside the first implementation scope.
