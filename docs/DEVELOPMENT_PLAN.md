# AWS SBCL Builder Scraper — Development Plan

## Phase 0 — Site reconnaissance

**Goal:** identify the real data transport before writing the scraper.

1. Inspect Builder Center public search in a desktop browser.
2. Capture Network requests while searching builders.
3. Capture Network requests while opening a profile.
4. Identify response payloads containing alias/name.
5. Determine pagination/cursors and any rate limits.
6. Verify whether the request is unauthenticated.
7. Save representative sanitized response fixtures under `tests/fixtures/`.

**Exit criterion:** we can point to the exact request/response that supplies candidate aliases and the exact request/response that supplies the public display name.

## Phase 1 — Project foundation

- Choose runtime/language based on repository state.
- Add dependency management.
- Add configuration loader.
- Add logging.
- Add `.gitignore` rules for local databases, exports, browser profiles, cookies, and secrets.
- Add test runner.

## Phase 2 — Builder Center client

Implement a narrow client around the verified site transport:

```text
BuilderCenterClient
  ├── search(query, pagination)
  └── get_profile(alias)
```

Keep transport details inside this module so the rest of the application does not depend on AWS Builder Center's internal schema.

## Phase 3 — Parsing and normalization

Implement:

- search response parser;
- profile parser;
- alias normalization (`@foo` → `foo` internally);
- display-name normalization;
- profile URL construction/validation;
- nullable public email handling;
- schema validation.

Every parser should have fixture tests.

## Phase 4 — Local persistence

Add SQLite with a small schema:

```sql
CREATE TABLE builders (
  alias TEXT PRIMARY KEY,
  display_name TEXT NOT NULL,
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
validation
  ↓
SQLite upsert
  ↓
summary
```

The run summary should report:

- candidates discovered;
- profiles resolved;
- new builders;
- updated builders;
- skipped/invalid profiles;
- errors;
- duration.

## Phase 6 — Export

Implement CSV and JSON export from the local database.

CSV is the primary output for the SBCL workflow.

Support filters such as:

- newly discovered since date;
- query/run;
- limit;
- only records with non-empty names.

## Phase 7 — CLI / local UX

Provide a simple workflow suitable for weekly use:

```text
1. Run search/scrape
2. Review summary
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

- verify alias/name against manually opened profiles;
- test duplicate search results;
- test multiple pages/cursors;
- test unavailable profiles;
- test missing optional email;
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
